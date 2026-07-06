import sys
import os
import unittest
import time
from fastapi.testclient import TestClient

# Ensure backend root is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from main import app
from database.session import init_db, SessionLocal
from database.models import Paper, ParentChunk, ResearchGap, ProjectIdea, TopicCluster
from tools.pdf_processor import extract_pages_from_pdf, chunk_text_with_metadata
from vector_store.embeddings import bge_embedding_function, bm25_searcher, reranker
from vector_store.chroma_store import vector_store

class ResearchIQTestSuite(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        print("\n=== Initializing Test Database and Schema ===")
        init_db()
        cls.db = SessionLocal()
        cls.client = TestClient(app)
        
        # Locate test PDF in uploads directory
        cls.pdf_dir = "./uploads"
        cls.pdf_files = [os.path.join(cls.pdf_dir, f) for f in os.listdir(cls.pdf_dir) if f.endswith(".pdf")]
        cls.test_pdf = cls.pdf_files[0] if cls.pdf_files else None
        
    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        print("\n=== Test Suite Finished ===")
        
    def test_01_health_check(self):
        print("\n[Test 1] Verifying FastAPI Health Check Endpoint...")
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        print("-> SUCCESS: Health endpoint responded correctly.")

    def test_02_pdf_extraction(self):
        print("\n[Test 2] Verifying PDF Text Extraction Pipeline...")
        if not self.test_pdf:
            self.skipTest("No PDF files available in backend/uploads/ to test parser.")
            
        pages = extract_pages_from_pdf(self.test_pdf)
        self.assertGreater(len(pages), 0, "PDF extraction failed to yield pages.")
        self.assertIn("page_number", pages[0])
        self.assertIn("text", pages[0])
        print(f"-> SUCCESS: Extracted {len(pages)} pages from {os.path.basename(self.test_pdf)}")

    def test_03_parent_child_chunking(self):
        print("\n[Test 3] Verifying Parent-Child Chunking Strategy...")
        # Create a mock pages list
        mock_pages = [
            {"page_number": 1, "text": "Abstract\nThis is a mock abstract for testing. Section 1. Introduction\nThis is the introduction text. It describes the problem. We want to test parent-child chunking."},
            {"page_number": 2, "text": "Methodology\nOur proposed methodology is based on federated learning.\nReferences\n1. First Paper citation.\n2. Second citation."}
        ]
        
        parent_chunks, child_chunks = chunk_text_with_metadata(
            mock_pages, 
            "mock_paper.pdf", 
            parent_size=50, 
            parent_overlap=10, 
            child_size=30, 
            child_overlap=5
        )
        
        self.assertGreater(len(parent_chunks), 0)
        self.assertGreater(len(child_chunks), 0)
        
        # Verify metadata propagation
        self.assertEqual(parent_chunks[0]["source_file"], "mock_paper.pdf")
        self.assertIn("parent_id", child_chunks[0])
        
        # Verify section header heuristic works
        self.assertEqual(parent_chunks[-1]["section"], "References")
        print(f"-> SUCCESS: Created {len(parent_chunks)} parent chunks and {len(child_chunks)} child chunks with metadata tracking.")

    def test_04_embedding_generation(self):
        print("\n[Test 4] Verifying BGE Embedding Dimensions...")
        sample_text = "Represent this sentence for testing embeddings dimensionality."
        embeddings = bge_embedding_function([sample_text])
        self.assertEqual(len(embeddings), 1)
        # BGE Small should be 384 dimensions
        self.assertEqual(len(embeddings[0]), 384)
        print(f"-> SUCCESS: Generated embedding of length {len(embeddings[0])}")

    def tearDown(self):
        self.db.rollback()

    def test_05_vector_insertion_and_hybrid_search(self):
        print("\n[Test 5] Verifying Hybrid Search and RRF Retrieval Accuracy...")
        if not self.test_pdf:
            self.skipTest("No PDF files available in uploads/ to index.")
            
        filename = os.path.basename(self.test_pdf)
        pages = extract_pages_from_pdf(self.test_pdf)
        
        # Recreate paper and parents cleanly to avoid UNIQUE constraint violations
        existing = self.db.query(Paper).filter(Paper.filename == filename).first()
        if existing:
            self.db.query(ParentChunk).filter(ParentChunk.source_file == filename).delete()
            self.db.delete(existing)
            self.db.commit()
            try:
                vector_store.collection.delete(where={"source": filename})
            except Exception:
                pass
        
        # Recreate a fresh paper row
        db_paper = Paper(filename=filename, title=filename)
        self.db.add(db_paper)
        self.db.commit()
        self.db.refresh(db_paper)
        
        parent_chunks, child_chunks = chunk_text_with_metadata(
            pages, filename, parent_size=1500, parent_overlap=250, child_size=400, child_overlap=50
        )
        
        # Save parents to SQLite
        for pc in parent_chunks:
            db_pc = ParentChunk(
                id=pc["chunk_id"],
                paper_id=db_paper.id,
                source_file=pc["source_file"],
                text=pc["text"],
                page_number=pc["page_number"],
                section=pc["section"]
            )
            self.db.add(db_pc)
        self.db.commit()
        
        # Index children in ChromaDB & BM25
        documents = [c["text"] for c in child_chunks]
        metadatas = [{
            "source": c["source_file"],
            "page_number": c["page_number"],
            "section": c["section"],
            "paper_id": db_paper.id,
            "parent_id": c["parent_id"]
        } for c in child_chunks]
        ids = [c["chunk_id"] for c in child_chunks]
        
        vector_store.add_documents(documents, metadatas, ids)
        
        # Run hybrid search query
        query = "learners mobile devices English"
        results = vector_store.hybrid_search(query, n_results=3)
        
        self.assertGreater(len(results), 0, "Hybrid search returned zero results.")
        self.assertIn("parent_id", results[0], "Result chunk is missing parent metadata.")
        self.assertIn("source_file", results[0])
        print(f"-> SUCCESS: Retrieval executed. Matches found: {len(results)}. Highest score: {results[0].get('rerank_score', 0.0):.3f}")

    def test_06_historical_results_mapping(self):
        print("\n[Test 6] Verifying Historical Results Endpoint Schema Consistency...")
        # Put dummy rows into Gaps, Ideas, and Clusters
        db_gap = ResearchGap(
            title="Federated Learning Gap",
            gap_type="Implicit Gap",
            description="Federated learning has poor latency on mobile phones",
            evidence="In Section 4, the authors do not evaluate mobile device power draw.",
            potential_impact="High",
            research_opportunity="Evaluate differential privacy overhead.",
            difficulty_score=8.5
        )
        self.db.add(db_gap)
        
        db_idea = ProjectIdea(
            title="FedMobile Framework",
            innovation_category="Moderate Innovation",
            description="A lightweight federated training engine for iOS devices.",
            novelty_score=8.0,
            feasibility_score=7.5,
            required_dataset="Flickr Vitals Dataset",
            methodology="Quantized LoRA training nodes.",
            expected_outcome="Sub-100ms training overhead.",
            implementation_roadmap=["Setup nodes", "Prune layers", "Deploy"],
            difficulty="Hard",
            tech_stack=["PyTorch", "FastAPI"],
            implementation_plan="Mock plan text"
        )
        self.db.add(db_idea)
        
        db_cluster = TopicCluster(
            cluster_name="Decentralized Learning",
            themes=["Federated", "Security"],
            emerging_areas=["Adversarial Poisoning"],
            paper_ids=["EJ1172284.pdf"],
            size=150
        )
        self.db.add(db_cluster)
        self.db.commit()
        
        # Query endpoint
        response = self.client.get("/api/historical-results")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check gaps
        self.assertGreater(len(data.get("research_gaps", [])), 0)
        gap = data["research_gaps"][0]
        self.assertEqual(gap["gap_type"], "Implicit Gap")
        self.assertEqual(gap["evidence"], "In Section 4, the authors do not evaluate mobile device power draw.")
        self.assertEqual(gap["potential_impact"], "High")
        
        # Check ideas
        self.assertGreater(len(data.get("project_ideas", [])), 0)
        idea = data["project_ideas"][0]
        self.assertEqual(idea["innovation_category"], "Moderate Innovation")
        self.assertEqual(idea["novelty_score"], 8.0)
        self.assertEqual(idea["feasibility_score"], 7.5)
        self.assertEqual(idea["required_dataset"], "Flickr Vitals Dataset")
        self.assertEqual(idea["implementation_roadmap"], ["Setup nodes", "Prune layers", "Deploy"])
        
        print("-> SUCCESS: Historical results reconstructed and structured correctly.")

    def test_07_search_endpoint_with_filters(self):
        print("\n[Test 7] Verifying Search Endpoint POST Request and Filtering...")
        if not self.test_pdf:
            self.skipTest("No test PDF indexed.")
            
        filename = os.path.basename(self.test_pdf)
        
        # Test 7.1: Regular query
        res = self.client.post("/api/search", json={
            "query": "mobile learning tools",
            "history": []
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("answer", data)
        self.assertIn("confidence_score", data)
        self.assertIn("search_latency_ms", data)
        
        # Test 7.2: Query with paper filter matching
        res_filter = self.client.post("/api/search", json={
            "query": "mobile learning tools",
            "history": [],
            "paper_filter": filename
        })
        self.assertEqual(res_filter.status_code, 200)
        
        # Test 7.3: Query with paper filter mismatch (should yield no results)
        res_mismatch = self.client.post("/api/search", json={
            "query": "mobile learning tools",
            "history": [],
            "paper_filter": "nonexistent_file.pdf"
        })
        self.assertEqual(res_mismatch.status_code, 200)
        self.assertEqual(len(res_mismatch.json()["passages"]), 0)
        
        print("-> SUCCESS: Search endpoint handles POST body, histories, and metadata filtering.")

if __name__ == "__main__":
    unittest.main()
