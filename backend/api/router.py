import os
import shutil
import uuid
import time
import re
import json
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from database.session import get_db, SessionLocal
from database.models import Paper, TopicCluster, ResearchGap, ProjectIdea, GlobalReport, ParentChunk
from tools.pdf_processor import extract_pages_from_pdf, chunk_text_with_metadata
from vector_store.chroma_store import vector_store
from vector_store.embeddings import bm25_searcher, tokenize
from agents.graph import research_graph
from agents.state import AgentState
from core.llm import get_llm

router = APIRouter()

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory store for task status
tasks_status = {}
tasks_results = {}

class QueryRequest(BaseModel):
    query: str
    history: Optional[List[Dict[str, str]]] = []
    paper_filter: Optional[str] = None
    section_filter: Optional[str] = None

def process_papers_background(task_id: str, file_paths: List[str]):
    db = SessionLocal()
    try:
        tasks_status[task_id] = "Processing and Parsing PDFs"
        print(f"[Ingestion Logging] Starting task {task_id}")
        
        paper_texts = {}
        for path in file_paths:
            filename = os.path.basename(path)
            print(f"[Ingestion Logging] Checking for existing paper: {filename}")
            
            # Document De-duplication
            existing_paper = db.query(Paper).filter(Paper.filename == filename).first()
            db.query(ParentChunk).filter(ParentChunk.source_file == filename).delete()
            if existing_paper:
                print(f"[Ingestion Logging] Paper '{filename}' already indexed. Deleting old records...")
                db.delete(existing_paper)
                db.commit()
                try:
                    vector_store.collection.delete(where={"source": filename})
                    bm25_searcher.chunks = [c for c in bm25_searcher.chunks if c.get("source_file") != filename]
                    if bm25_searcher.chunks:
                        from rank_bm25 import BM25Okapi
                        corpus_tokens = [tokenize(c["text"]) for c in bm25_searcher.chunks]
                        bm25_searcher.bm25 = BM25Okapi(corpus_tokens)
                    else:
                        bm25_searcher.bm25 = None
                    bm25_searcher.save()
                    print(f"[Ingestion Logging] Successfully deleted old vector references for {filename}")
                except Exception as ve:
                    print(f"[Ingestion Logging] Error deleting vector store elements: {ve}")

            print(f"[Ingestion Logging] Parsing PDF pages: {filename}")
            pages = extract_pages_from_pdf(path)
            full_text = " ".join([p["text"] for p in pages])
            paper_texts[filename] = full_text
            
            # Save Initial Paper to DB to get paper ID
            db_paper = Paper(filename=filename, title=filename, upload_time=None)
            db.add(db_paper)
            db.commit()
            db.refresh(db_paper)
            
            # Metadata-preserving parent-child chunking
            print(f"[Ingestion Logging] Chunking text into Parent & Child chunks: {filename}")
            tasks_status[task_id] = f"Chunking and Indexing {filename}"
            parent_chunks, child_chunks = chunk_text_with_metadata(
                pages, 
                filename, 
                parent_size=1500, 
                parent_overlap=250, 
                child_size=400, 
                child_overlap=50
            )
            
            # Save Parent Chunks to SQLite
            print(f"[Ingestion Logging] Saving {len(parent_chunks)} parent chunks to SQLite...")
            for pc in parent_chunks:
                db_pc = ParentChunk(
                    id=pc["chunk_id"],
                    paper_id=db_paper.id,
                    source_file=pc["source_file"],
                    text=pc["text"],
                    page_number=pc["page_number"],
                    section=pc["section"]
                )
                db.add(db_pc)
            db.commit()
            
            # Save Child Chunks to ChromaDB & BM25 Index
            print(f"[Ingestion Logging] Indexing {len(child_chunks)} child chunks in vector & keyword stores...")
            documents = [c["text"] for c in child_chunks]
            metadatas = [{
                "source": c["source_file"],
                "page_number": c["page_number"],
                "section": c["section"],
                "paper_id": db_paper.id,
                "parent_id": c["parent_id"]
            } for c in child_chunks]
            ids = [c["chunk_id"] for c in child_chunks]
            
            vector_store.add_documents(documents=documents, metadatas=metadatas, ids=ids)
            print(f"[Ingestion Logging] Finished indexing {filename}")
            
        tasks_status[task_id] = "Running Agentic Analysis"
        
        # Initialize LangGraph State
        initial_state = AgentState(
            paper_files=file_paths,
            paper_texts=paper_texts,
            paper_analyses={},
            topic_clusters=[],
            research_landscape="",
            research_gaps=[],
            project_ideas=[],
            quality_audits={},
            writing_evaluations={},
            master_report="",
            current_step="start"
        )
        
        # Run Multi-Agent Graph
        print("[Ingestion Logging] Launching LangGraph Agentic Workflow")
        final_state = research_graph.invoke(initial_state)
        
        # Write Agent results to Database
        tasks_status[task_id] = "Persisting Analysis Results"
        print("[Ingestion Logging] Persisting results to SQLite database")
        
        # Update Papers with full extracted details
        for filename, analysis in final_state.get("paper_analyses", {}).items():
            db_paper = db.query(Paper).filter(Paper.filename == filename).first()
            if db_paper:
                db_paper.title = analysis.get("title")
                db_paper.abstract = analysis.get("abstract")
                db_paper.methodology = analysis.get("methodology")
                db_paper.datasets = analysis.get("datasets")
                db_paper.results = analysis.get("results")
                db_paper.limitations = analysis.get("limitations")
                db_paper.references = analysis.get("references")
                
                # Fetch reliability score
                audit = final_state.get("quality_audits", {}).get(filename, {})
                db_paper.reliability_score = audit.get("reliability_score", 50.0)
                db_paper.quality_audit = audit
                
                # Fetch humanization score
                writing = final_state.get("writing_evaluations", {}).get(filename, {})
                db_paper.humanization_score = writing.get("humanization_score", 50.0)
                db_paper.writing_evaluation = writing
                
        # Save Research Gaps with complete schemas
        for gap in final_state.get("research_gaps", []):
            exists = db.query(ResearchGap).filter(ResearchGap.title == gap["title"]).first()
            if not exists:
                db_gap = ResearchGap(
                    title=gap["title"],
                    gap_type=gap.get("gap_type", "Implicit Gap"),
                    description=gap["description"],
                    evidence=gap.get("evidence", ""),
                    potential_impact=gap.get("potential_impact", "Medium"),
                    research_opportunity=gap.get("research_opportunity", ""),
                    difficulty_score=gap.get("difficulty_score", 7.0)
                )
                db.add(db_gap)
                
        # Save Project Ideas with complete schemas
        for idea in final_state.get("project_ideas", []):
            exists = db.query(ProjectIdea).filter(ProjectIdea.title == idea["title"]).first()
            if not exists:
                db_idea = ProjectIdea(
                    title=idea["title"],
                    innovation_category=idea.get("innovation_category", "Moderate Innovation"),
                    description=idea["description"],
                    novelty_score=idea.get("novelty_score", 7.0),
                    feasibility_score=idea.get("feasibility_score", 7.0),
                    required_dataset=idea.get("required_dataset", ""),
                    methodology=idea.get("methodology", ""),
                    expected_outcome=idea.get("expected_outcome", ""),
                    implementation_roadmap=idea.get("implementation_roadmap", []),
                    difficulty=idea.get("difficulty", "Medium"),
                    tech_stack=idea.get("tech_stack", []),
                    implementation_plan=idea.get("methodology", "")
                )
                db.add(db_idea)
                
        # Save Topic Clusters
        for cluster in final_state.get("topic_clusters", []):
            exists = db.query(TopicCluster).filter(TopicCluster.cluster_name == cluster["name"]).first()
            if not exists:
                db_cluster = TopicCluster(
                    cluster_name=cluster["name"],
                    themes=cluster.get("themes", []),
                    emerging_areas=cluster.get("emerging_areas", []),
                    paper_ids=cluster.get("paper_filenames", []),
                    size=cluster.get("size", 100)
                )
                db.add(db_cluster)
                
        # Save Global Report
        db_report = GlobalReport(
            research_landscape=final_state.get("research_landscape", ""),
            master_report=final_state.get("master_report", "")
        )
        db.add(db_report)
                
        db.commit()
        
        tasks_results[task_id] = final_state
        tasks_status[task_id] = "Completed"
        print(f"[Ingestion Logging] Task {task_id} completed successfully")
        
    except Exception as e:
        db.rollback()
        tasks_status[task_id] = f"Error: {str(e)}"
        print(f"[Ingestion Logging] Workflow error: {e}")
    finally:
        db.close()


@router.post("/upload")
async def upload_papers(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    file_paths = []
    for file in files:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_paths.append(file_path)
        
    task_id = str(uuid.uuid4())
    tasks_status[task_id] = "Pending"
    
    # Run in background with dedicated SessionLocal creation inside task
    background_tasks.add_task(process_papers_background, task_id, file_paths)
    
    return {"message": "Files uploaded and processing started", "task_id": task_id}

@router.get("/status/{task_id}")
async def get_status(task_id: str):
    return {"status": tasks_status.get(task_id, "Unknown")}

@router.get("/results/{task_id}")
async def get_results(task_id: str):
    if task_id in tasks_results:
        return tasks_results[task_id]
    return {"error": "Results not ready or task not found."}

@router.get("/papers")
async def get_papers(db: Session = Depends(get_db)):
    papers = db.query(Paper).all()
    return papers

@router.get("/gaps")
async def get_gaps(db: Session = Depends(get_db)):
    gaps = db.query(ResearchGap).all()
    # Sort or rank gaps descending by difficulty score / significance
    return gaps

@router.get("/ideas")
async def get_ideas(db: Session = Depends(get_db)):
    ideas = db.query(ProjectIdea).all()
    return ideas

@router.get("/clusters")
async def get_clusters(db: Session = Depends(get_db)):
    clusters = db.query(TopicCluster).all()
    return clusters

@router.get("/historical-results")
async def get_historical_results(db: Session = Depends(get_db)):
    """Fetch and rebuild a complete AnalysisResults dict from persisted SQLite database tables."""
    papers = db.query(Paper).all()
    if not papers:
        return {}
        
    gaps = db.query(ResearchGap).all()
    ideas = db.query(ProjectIdea).all()
    clusters = db.query(TopicCluster).all()
    
    # Get latest global report
    global_report = db.query(GlobalReport).order_by(GlobalReport.id.desc()).first()
    research_landscape = global_report.research_landscape if global_report else ""
    master_report = global_report.master_report if global_report else ""
    
    # Reconstruct paper_analyses, quality_audits, writing_evaluations
    paper_analyses = {}
    quality_audits = {}
    writing_evaluations = {}
    
    for p in papers:
        paper_analyses[p.filename] = {
            "title": p.title,
            "abstract": p.abstract,
            "methodology": p.methodology,
            "datasets": p.datasets,
            "results": p.results,
            "limitations": p.limitations,
            "references": p.references
        }
        if p.quality_audit:
            quality_audits[p.filename] = p.quality_audit
        else:
            quality_audits[p.filename] = {
                "reliability_score": p.reliability_score,
                "methodology_problems": [],
                "statistical_problems": [],
                "reproducibility_problems": []
            }
            
        if p.writing_evaluation:
            writing_evaluations[p.filename] = p.writing_evaluation
        else:
            writing_evaluations[p.filename] = {
                "readability_score": 70.0,
                "clarity_score": 70.0,
                "academic_quality_score": 70.0,
                "humanization_score": p.humanization_score,
                "problems": [],
                "suggestions": []
            }
            
    # Reconstruct gaps list with all properties
    research_gaps = []
    for g in gaps:
        research_gaps.append({
            "title": g.title,
            "gap_type": g.gap_type or "Implicit Gap",
            "description": g.description,
            "evidence": g.evidence or "",
            "potential_impact": g.potential_impact,
            "research_opportunity": g.research_opportunity or "",
            "difficulty_score": g.difficulty_score
        })
        
    # Reconstruct ideas list with all properties
    project_ideas = []
    for idea in ideas:
        project_ideas.append({
            "title": idea.title,
            "innovation_category": idea.innovation_category or "Moderate Innovation",
            "description": idea.description,
            "novelty_score": idea.novelty_score or 7.0,
            "feasibility_score": idea.feasibility_score or 7.0,
            "required_dataset": idea.required_dataset or "",
            "methodology": idea.methodology or "",
            "expected_outcome": idea.expected_outcome or "",
            "implementation_roadmap": idea.implementation_roadmap or [],
            "difficulty": idea.difficulty or "Medium",
            "tech_stack": idea.tech_stack or []
        })
        
    # Reconstruct clusters list with all properties
    topic_clusters = []
    for c in clusters:
        topic_clusters.append({
            "name": c.cluster_name,
            "themes": c.themes or [],
            "emerging_areas": c.emerging_areas or [],
            "paper_filenames": c.paper_ids or [],
            "size": c.size or 100
        })
        
    return {
        "paper_analyses": paper_analyses,
        "topic_clusters": topic_clusters,
        "research_landscape": research_landscape,
        "research_gaps": research_gaps,
        "project_ideas": project_ideas,
        "quality_audits": quality_audits,
        "writing_evaluations": writing_evaluations,
        "master_report": master_report
    }

@router.post("/search")
async def search_rag(req: QueryRequest):
    """True RAG Endpoint: refines search query with history, runs hybrid search, reranks context, synthesizes answer."""
    start_time = time.time()
    llm = get_llm()
    
    query = req.query
    history = req.history
    
    # 1. Query refinement using LLM if history is present
    if history:
        history_str = ""
        for msg in history:
            history_str += f"{msg.get('role', 'user').capitalize()}: {msg.get('content', '')}\n"
        refine_prompt = (
            f"Given the following conversation history and a follow-up question, "
            f"rephrase the follow-up question to be a standalone search query in a scientific paper database.\n"
            f"Do not write any commentary or conversational replies, just output the search query.\n\n"
            f"History:\n{history_str}\n"
            f"Follow-up: {query}\n\n"
            f"Standalone Query:"
        )
        try:
            query = llm.invoke(refine_prompt).content.strip()
            query = re.sub(r'^["\']|["\']$', '', query)
        except Exception as e:
            print(f"Error refining query: {e}")
            
    # 2. Build metadata query filter where constraint
    where = None
    if req.paper_filter and req.section_filter:
        where = {
            "$and": [
                {"source": req.paper_filter},
                {"section": req.section_filter}
            ]
        }
    elif req.paper_filter:
        where = {"source": req.paper_filter}
    elif req.section_filter:
        where = {"section": req.section_filter}

    # 3. Hybrid Search, Parent Chunk Fetching, Reranking & Context Compression
    try:
        reranked_chunks = vector_store.hybrid_search(query, n_results=5, where=where, threshold=0.1)
    except Exception as e:
        print(f"Error executing hybrid search: {e}")
        reranked_chunks = []
        
    # 4. Calculate Confidence Score
    confidence_score = 0.0
    if reranked_chunks:
        import math
        # Sigmoid: maps ms-marco cross-encoder scores (usually -10 to +3) to 0-100%
        # Clean sigmoid mapping: sigmoid(x) where mid point is around -3.0
        # If max score is 1.0, confidence is high. If max score is -6.0, confidence is lower.
        max_score = max([c.get("rerank_score", -5.0) for c in reranked_chunks])
        prob = 1.0 / (1.0 + math.exp(- (max_score + 3.0)))
        confidence_score = round(prob * 100, 1)
        
    # 5. Synthesize Answer via LLM
    context = ""
    for i, c in enumerate(reranked_chunks):
        context += (
            f"[Passage {i+1}] (Source: {c['source_file']}, Page: {c['page_number']}, "
            f"Section: {c['section']})\n"
            f"Content: {c['text']}\n\n"
        )
        
    system_prompt = (
        "You are ResearchIQ, a premium AI Research Intelligence System.\n"
        "Synthesize a clear, detailed, and comprehensive answer to the user's query using the provided context passages.\n"
        "Cite the sources of claims inline using references like `[Source: filename, Page: X]`. Do not use indices like [1].\n"
        "Do not make up facts. If the information is not present in the context, explicitly say that the uploaded documents "
        "do not contain sufficient information to answer.\n\n"
        f"Context:\n{context}\n"
        f"Query: {query}\n\n"
        "Answer (Markdown):"
    )
    
    answer = "No matching research papers or context retrieved to answer the question."
    if reranked_chunks:
        try:
            answer = llm.invoke(system_prompt).content.strip()
        except Exception as e:
            answer = f"Error during LLM answer synthesis: {e}"
            
    # 6. Suggested Follow-up Questions
    follow_ups = []
    if reranked_chunks:
        follow_up_prompt = (
            f"Based on the query: '{query}' and answer: '{answer[:1000]}', "
            f"suggest exactly 3 follow-up questions for a researcher to dive deeper.\n"
            f"Output as a valid JSON list of strings. Do not include markdown wraps.\n"
            f"Format example: [\"question 1\", \"question 2\", \"question 3\"]"
        )
        try:
            res_txt = llm.invoke(follow_up_prompt).content.strip()
            res_txt = re.sub(r'^```json\s*|```$', '', res_txt, flags=re.MULTILINE).strip()
            follow_ups = json.loads(res_txt)
        except Exception:
            follow_ups = [
                "What methodology details are mentioned in the source?",
                "What experimental results or datasets are evaluated?",
                "What limitations does the paper outline?"
            ]
            
    latency = round((time.time() - start_time) * 1000, 1)
    
    return {
        "answer": answer,
        "passages": reranked_chunks,
        "confidence_score": confidence_score,
        "follow_up_questions": follow_ups,
        "search_latency_ms": latency
    }

