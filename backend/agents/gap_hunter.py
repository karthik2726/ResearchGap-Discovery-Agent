from core.llm import get_llm
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from agents.state import AgentState

class Gap(BaseModel):
    title: str = Field(description="Short, specific title for the research gap")
    gap_type: str = Field(description="One of: Explicit Gap, Implicit Gap, Methodological Weakness, Dataset Limitation, Scalability Issue, Evaluation Weakness, Practical Deployment Gap")
    description: str = Field(description="Detailed explanation of what is missing or unexplored in the literature")
    evidence: str = Field(description="Specific evidence, paragraph context, or citation references from the analyzed paper(s)")
    potential_impact: str = Field(description="The potential impact or value to the field if this gap is addressed")
    research_opportunity: str = Field(description="A concrete research opportunity or direction to solve this gap")
    difficulty_score: float = Field(description="Difficulty rating from 1.0 (easy) to 10.0 (extremely complex) to solve this gap")

class GapReport(BaseModel):
    gaps: List[Gap] = Field(description="List of top 8-10 research gaps, ranked by significance (highest impact first)")

def gap_hunter_node(state: AgentState) -> Dict[str, Any]:
    llm = get_llm()
    parser = JsonOutputParser(pydantic_object=GapReport)
    
    context = ""
    for filename, analysis in state.get("paper_analyses", {}).items():
        context += (
            f"Paper: {analysis.get('title', 'Unknown')}\n"
            f"Abstract: {analysis.get('abstract', '')}\n"
            f"Methodology: {analysis.get('methodology', '')}\n"
            f"Results: {analysis.get('results', '')}\n"
            f"Limitations: {analysis.get('limitations', '')}\n"
            f"Datasets: {', '.join(analysis.get('datasets', [])) if isinstance(analysis.get('datasets'), list) else analysis.get('datasets', '')}\n\n"
        )
        
    prompt = PromptTemplate(
        template=(
            "You are a Research Gap Hunter specialized in academic literature analysis.\n"
            "Analyze the methodology, datasets, limitations, and evaluation methods of the research papers below.\n"
            "Identify up to 10 concrete, specific research gaps and categorize them. Do not suggest generic ideas.\n"
            "Rank the gaps in order of significance (highest impact first).\n"
            "{format_instructions}\n\n"
            "Research Paper Context:\n{context}\n"
        ),
        input_variables=["context"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    
    chain = prompt | llm | parser
    
    try:
        res = chain.invoke({"context": context[:30000]})
        gaps = res.get("gaps", [])
        
        normalized = []
        for g in gaps:
            if isinstance(g, dict):
                normalized.append({
                    "title": g.get("title", "Research Gap"),
                    "gap_type": g.get("gap_type", "Implicit Gap"),
                    "description": g.get("description", ""),
                    "evidence": g.get("evidence", ""),
                    "potential_impact": g.get("potential_impact", ""),
                    "research_opportunity": g.get("research_opportunity", ""),
                    "difficulty_score": g.get("difficulty_score", g.get("difficulty", 7.0)),
                })
        return {"research_gaps": normalized}
    except Exception as e:
        print(f"Error hunting gaps: {e}")
        return {"research_gaps": []}
