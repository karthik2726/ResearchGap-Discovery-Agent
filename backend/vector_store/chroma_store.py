import chromadb
from chromadb.config import Settings
import os
from vector_store.embeddings import bge_embedding_function, bm25_searcher, reranker

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./vector_store/chromadb_data")

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        
        # Robustly handle embedding function conflict
        try:
            self.collection = self.client.get_collection(
                name="research_papers",
                embedding_function=bge_embedding_function
            )
            print("ChromaDB: Loaded existing collection 'research_papers' with BGE embeddings.")
        except Exception as e:
            print(f"ChromaDB: Recreating collection 'research_papers' due to conflict/absence: {e}")
            try:
                self.client.delete_collection("research_papers")
            except Exception:
                pass
            self.collection = self.client.create_collection(
                name="research_papers",
                metadata={"hnsw:space": "cosine"},
                embedding_function=bge_embedding_function
            )
            print("ChromaDB: Created new collection 'research_papers' with BGE embeddings.")
        
    def add_documents(self, documents: list[str], metadatas: list[dict], ids: list[str]):
        """Adds documents to the collection and updates the BM25 index."""
        # Add to Chroma
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        # Feed to BM25 searcher index
        chunks_for_bm25 = []
        for doc, meta, cid in zip(documents, metadatas, ids):
            chunks_for_bm25.append({
                "chunk_id": cid,
                "text": doc,
                "source_file": meta.get("source", "Unknown"),
                "page_number": meta.get("page_number", 1),
                "section": meta.get("section", "Abstract")
            })
        bm25_searcher.add_documents(chunks_for_bm25)
        
    def search(self, query_text: str, n_results: int = 5, where: dict = None):
        """Searches the vector store for relevant chunks using BGE embeddings."""
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where
        )
        return results

    def hybrid_search(self, query_text: str, n_results: int = 5, where: dict = None, threshold: float = 0.1) -> list[dict]:
        """Hybrid search combining Vector Search (BGE) and Keyword Search (BM25), followed by Cross-Encoder reranking, Parent-Child retrieval, and Context Compression."""
        # 1. BGE Query Instruction Prepending
        # Prepend query instruction for BGE embedding models
        vector_query = f"Represent this sentence for searching relevant passages: {query_text}"
        
        # 2. Vector Search (fetching candidate child chunks)
        vector_res = self.collection.query(
            query_texts=[vector_query],
            n_results=n_results * 4,  # fetch more for merging & rerank
            where=where
        )
        
        vector_chunks = []
        if vector_res and "documents" in vector_res and vector_res["documents"] and len(vector_res["documents"]) > 0:
            docs = vector_res["documents"][0]
            metas = vector_res["metadatas"][0]
            ids = vector_res["ids"][0]
            distances = vector_res["distances"][0] if "distances" in vector_res else [0.5] * len(docs)
            
            for doc, meta, cid, dist in zip(docs, metas, ids, distances):
                sim = 1.0 - float(dist)
                if sim >= threshold:
                    vector_chunks.append({
                        "chunk_id": cid,
                        "text": doc,
                        "source_file": meta.get("source", "Unknown"),
                        "page_number": meta.get("page_number", 1),
                        "section": meta.get("section", "Abstract"),
                        "parent_id": meta.get("parent_id"),
                        "vector_score": sim,
                        "bm25_score": 0.0
                    })
                    
        # 3. BM25 Search (keyword matching on child chunks)
        bm25_chunks = bm25_searcher.search(query_text, n_results=n_results * 4)
        
        # Apply manual metadata filtering for BM25 results
        if where:
            source_filter = None
            section_filter = None
            if "$and" in where:
                for cond in where["$and"]:
                    if "source" in cond:
                        source_filter = cond["source"]
                    if "section" in cond:
                        section_filter = cond["section"]
            else:
                source_filter = where.get("source")
                section_filter = where.get("section")
                
            if source_filter:
                bm25_chunks = [c for c in bm25_chunks if c["source_file"] == source_filter]
            if section_filter:
                bm25_chunks = [c for c in bm25_chunks if c["section"] == section_filter]
                
        # 4. Combine rankings via Reciprocal Rank Fusion (RRF)
        rrf_scores = {}
        
        # Rank by vector score
        vector_sorted = sorted(vector_chunks, key=lambda x: x["vector_score"], reverse=True)
        for rank, chunk in enumerate(vector_sorted):
            cid = chunk["chunk_id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (60.0 + (rank + 1)))
            
        # Rank by BM25 score
        bm25_sorted = sorted(bm25_chunks, key=lambda x: x["bm25_score"], reverse=True)
        for rank, chunk in enumerate(bm25_sorted):
            cid = chunk["chunk_id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (60.0 + (rank + 1)))
            
        # Merge dictionaries
        merged_chunks = {}
        for c in vector_chunks:
            merged_chunks[c["chunk_id"]] = c
        for c in bm25_chunks:
            cid = c["chunk_id"]
            if cid not in merged_chunks:
                merged_chunks[cid] = {
                    "chunk_id": cid,
                    "text": c["text"],
                    "source_file": c.get("source_file", "Unknown"),
                    "page_number": c.get("page_number", 1),
                    "section": c.get("section", "Abstract"),
                    "parent_id": c.get("parent_id"),
                    "vector_score": 0.0,
                    "bm25_score": c["bm25_score"]
                }
            else:
                merged_chunks[cid]["bm25_score"] = c["bm25_score"]
                
        # Build list of merged chunks with RRF scores
        all_merged = []
        for cid, score in rrf_scores.items():
            if cid in merged_chunks:
                chunk = merged_chunks[cid]
                chunk["rrf_score"] = score
                all_merged.append(chunk)
                
        all_merged = sorted(all_merged, key=lambda x: x["rrf_score"], reverse=True)
        candidate_chunks = all_merged[:n_results * 3]
        
        if not candidate_chunks:
            return []
            
        # 5. Parent-Child Retrieval: Fetch Parent Chunks from SQLite Database
        from database.session import SessionLocal
        db = SessionLocal()
        parent_map = {}
        try:
            parent_ids = list({c["parent_id"] for c in candidate_chunks if c.get("parent_id")})
            if parent_ids:
                from database.models import ParentChunk
                db_parents = db.query(ParentChunk).filter(ParentChunk.id.in_(parent_ids)).all()
                parent_map = {p.id: p.text for p in db_parents}
        except Exception as e:
            print(f"Error loading parent chunks: {e}")
        finally:
            db.close()
            
        # Attach parent chunk texts
        for c in candidate_chunks:
            pid = c.get("parent_id")
            if pid and pid in parent_map:
                c["parent_text"] = parent_map[pid]
            else:
                c["parent_text"] = c["text"]
                
        # 6. Cross-Encoder Reranking (using Parent text for semantic verification)
        rerank_candidates = []
        for c in candidate_chunks:
            rerank_candidates.append({
                "chunk_id": c["chunk_id"],
                "text": c["parent_text"],
                "child_text": c["text"],
                "source_file": c["source_file"],
                "page_number": c["page_number"],
                "section": c["section"],
                "parent_id": c["parent_id"]
            })
            
        reranked = reranker.rerank(query_text, rerank_candidates, top_k=n_results)
        
        # 7. Context Compression: Retain only the most relevant sentences in Parent Chunks
        for c in reranked:
            c["text"] = compress_context(query_text, c["text"])
            
        return reranked

def compress_context(query: str, parent_text: str, max_sentences: int = 4) -> str:
    """Helper to score sentences in the parent chunk using the CrossEncoder, keeping the top-N sentences."""
    import re
    sentences = re.split(r'(?<=[.!?])\s+', parent_text.strip())
    if len(sentences) <= max_sentences:
        return parent_text
        
    pairs = [[query, s] for s in sentences]
    try:
        from vector_store.embeddings import _reranker_model
        if _reranker_model is None:
            from sentence_transformers import CrossEncoder
            model_name = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
            _reranker_model = CrossEncoder(model_name)
        scores = _reranker_model.predict(pairs)
    except Exception as e:
        print(f"Context compression failure: {e}")
        return " ".join(sentences[:max_sentences])
        
    scored_sentences = list(zip(sentences, scores, range(len(sentences))))
    scored_sentences = sorted(scored_sentences, key=lambda x: x[1], reverse=True)
    
    # Select top N, preserve original order
    top_sentences = sorted(scored_sentences[:max_sentences], key=lambda x: x[2])
    compressed = " ".join([s[0] for s in top_sentences])
    return compressed

# Singleton instance
vector_store = VectorStore()

