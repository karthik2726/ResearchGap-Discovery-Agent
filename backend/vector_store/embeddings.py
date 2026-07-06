import os
import re
import pickle
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

# Lazy loaded embedding model and reranker to speed up start times
_embedding_model = None
_reranker_model = None

class BGEEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model_name=None):
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
        
    def __call__(self, input: Documents) -> Embeddings:
        global _embedding_model
        if _embedding_model is None:
            from sentence_transformers import SentenceTransformer
            print(f"Loading embedding model: {self.model_name}...")
            _embedding_model = SentenceTransformer(self.model_name)
        
        # BGE models perform best with instructions for query vs passage
        # For indexing, we can embed directly. For search, we prepend a query instruction if using BGE
        # Let's check if we're embedding search queries vs passages (simple passage encoding here)
        embeddings = _embedding_model.encode(input, normalize_embeddings=True, convert_to_numpy=True).tolist()
        return embeddings

def tokenize(text: str) -> list[str]:
    """Simple alphanumeric tokenizer for BM25."""
    return re.findall(r'\w+', text.lower())

class BM25Searcher:
    def __init__(self, index_path=None):
        self.index_path = index_path or os.getenv("BM25_INDEX_PATH", "./vector_store/bm25_index.pkl")
        self.chunks = []
        self.bm25 = None
        self.load()
        
    def save(self):
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        with open(self.index_path, 'wb') as f:
            pickle.dump((self.chunks, self.bm25), f)
            
    def load(self):
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, 'rb') as f:
                    self.chunks, self.bm25 = pickle.load(f)
            except Exception as e:
                print(f"Error loading BM25 index: {e}")
                self.chunks = []
                self.bm25 = None

    def add_documents(self, new_chunks: list[dict]):
        """Adds new chunks to the BM25 corpus and updates the index."""
        # De-duplicate chunks to prevent duplicate indexing
        existing_ids = {c["chunk_id"] for c in self.chunks}
        added = False
        for chunk in new_chunks:
            if chunk["chunk_id"] not in existing_ids:
                self.chunks.append(chunk)
                added = True
                
        if added:
            from rank_bm25 import BM25Okapi
            corpus_tokens = [tokenize(c["text"]) for c in self.chunks]
            self.bm25 = BM25Okapi(corpus_tokens)
            self.save()
            print(f"BM25 index updated: {len(self.chunks)} total chunks.")

    def search(self, query: str, n_results: int = 10) -> list[dict]:
        """Runs a keyword search and returns top-k matching chunks with scores."""
        if not self.bm25 or not self.chunks:
            return []
        
        query_tokens = tokenize(query)
        scores = self.bm25.get_scores(query_tokens)
        
        # Zip, sort and filter
        scored_chunks = []
        for idx, score in enumerate(scores):
            if score > 0:
                chunk_copy = dict(self.chunks[idx])
                chunk_copy["bm25_score"] = float(score)
                scored_chunks.append(chunk_copy)
                
        # Sort descending by score
        scored_chunks = sorted(scored_chunks, key=lambda x: x["bm25_score"], reverse=True)
        return scored_chunks[:n_results]

class CrossEncoderReranker:
    def __init__(self, model_name=None):
        self.model_name = model_name or os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
        
    def rerank(self, query: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
        if not chunks:
            return []
            
        global _reranker_model
        if _reranker_model is None:
            from sentence_transformers import CrossEncoder
            print(f"Loading reranker model: {self.model_name}...")
            _reranker_model = CrossEncoder(self.model_name)
            
        pairs = [[query, c["text"]] for c in chunks]
        scores = _reranker_model.predict(pairs)
        
        for idx, score in enumerate(scores):
            chunks[idx]["rerank_score"] = float(score)
            
        # Sort descending by rerank score
        sorted_chunks = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)
        return sorted_chunks[:top_k]

# Singleton instances
bge_embedding_function = BGEEmbeddingFunction()
bm25_searcher = BM25Searcher()
reranker = CrossEncoderReranker()
