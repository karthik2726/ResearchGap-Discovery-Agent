from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    # Input
    paper_files: List[str]  # Paths to uploaded PDFs
    
    # Processed Data
    paper_texts: Dict[str, str]  # filename -> full text
    
    # Agent 1: Analyst Output
    paper_analyses: Dict[str, Dict[str, Any]]
    
    # Agent 2: Mapper Output
    topic_clusters: List[Dict[str, Any]]
    research_landscape: str
    
    # Agent 3: Gap Hunter Output
    research_gaps: List[Dict[str, Any]]
    
    # Agent 4: Innovation Architect Output
    project_ideas: List[Dict[str, Any]]
    
    # Agent 5: Quality Auditor Output
    quality_audits: Dict[str, Dict[str, Any]]
    
    # Agent 6: Writing Evaluator Output
    writing_evaluations: Dict[str, Dict[str, Any]]
    
    # Agent 7: Chief Strategist Output
    master_report: str
    
    # Internal routing flag
    current_step: str
