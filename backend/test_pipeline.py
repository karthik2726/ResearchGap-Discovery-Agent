import sys
import os
import time

# Ensure backend root is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from database.session import init_db, SessionLocal
from database.models import Paper
from tools.pdf_processor import extract_pages_from_pdf, chunk_text_with_metadata
from vector_store.embeddings import bge_embedding_function, bm25_searcher, reranker
from vector_store.chroma_store import vector_store
from core.llm import get_llm

def run_tests():
    print("==============================================")
    # 1. Initialize Database
    init_db()
    db = SessionLocal()
    print("SUCCESS: Database initialized.")
    
    # 2. Check if there are any PDFs in uploads
    pdf_dir = "./uploads"
    pdf_files = [os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
    
    if not pdf_files:
        print("WARNING: No PDF files found in backend/uploads/ to test parser. Skipping parser test.")
        return
        
    test_pdf = pdf_files[0]
    filename = os.path.basename(test_pdf)
    print(f"Testing pipeline with file: {test_pdf}")
    
    # 3. Test PDF Page-by-Page Extraction
    start = time.time()
    pages = extract_pages_from_pdf(test_pdf)
    print(f"SUCCESS: Extracted {len(pages)} pages in {time.time() - start:.2f} seconds.")
    assert len(pages) > 0, "No pages extracted!"
    
    # 4. Test Metadata Chunking
    parent_chunks, child_chunks = chunk_text_with_metadata(pages, filename, chunk_size=1000, overlap=200)
    print(f"SUCCESS: Created {len(parent_chunks)} parent chunks and {len(child_chunks)} child chunks with metadata.")
    assert len(parent_chunks) > 0, "No parent chunks generated!"
    print(f"Sample Chunk Metadata: {parent_chunks[0]}")
    
    # 5. Test Embeddings
    print("Testing BGE Embedding Function...")
    emb_start = time.time()
    embs = bge_embedding_function([parent_chunks[0]["text"]])
    print(f"SUCCESS: Generated BGE embeddings in {time.time() - emb_start:.2f} seconds. Size: {len(embs[0])}")
    
    # 6. Test Vector & BM25 Indexing
    print("Testing Vector Store and BM25 index insertion...")
    documents = [c["text"] for c in child_chunks]
    metadatas = [{"source": c["source_file"], "page_number": c["page_number"], "section": c["section"], "parent_id": c["parent_id"]} for c in child_chunks]
    ids = [c["chunk_id"] for c in child_chunks]
    
    vector_store.add_documents(documents, metadatas, ids)
    print("SUCCESS: Added documents to ChromaDB and BM25 index.")
    
    # 7. Test Hybrid Search & Reranking
    print("Testing Hybrid Search + Reranker...")
    query = "methodology limitations datasets"
    results = vector_store.hybrid_search(query, n_results=3)
    print(f"SUCCESS: Hybrid search returned {len(results)} reranked results.")
    for idx, r in enumerate(results):
        print(f"  [{idx+1}] File: {r['source_file']}, Page: {r['page_number']}, Section: {r['section']}, Rerank Score: {r.get('rerank_score'):.3f}")
        
    # 8. Test LLM interaction
    print("Testing LLM generation...")
    llm = get_llm()
    prompt = f"Summarize the following text in 1 sentence:\n{parent_chunks[0]['text']}"
    res = llm.invoke(prompt)
    print(f"SUCCESS: LLM output: {res.content}")
    print("==============================================")
    print("ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
