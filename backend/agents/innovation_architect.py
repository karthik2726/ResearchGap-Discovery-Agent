from core.llm import get_llm
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from agents.state import AgentState
import json

class Idea(BaseModel):
    title: str = Field(description="Title of the proposed project or research idea")
    innovation_category: str = Field(description="One of: Incremental, Moderate Innovation, High-Risk High-Reward")
    description: str = Field(description="Detailed overview of the project idea")
    novelty_score: float = Field(description="Novelty score from 1.0 (very common) to 10.0 (groundbreaking)")
    feasibility_score: float = Field(description="Feasibility score from 1.0 (almost impossible) to 10.0 (very straightforward)")
    required_dataset: str = Field(description="Name and description of required datasets or simulated environments")
    methodology: str = Field(description="Scientific methodology, modeling techniques, or experimental setup proposed")
    expected_outcome: str = Field(description="Expected scientific or practical outcomes and performance metrics")
    implementation_roadmap: List[str] = Field(description="A 4-5 step chronological roadmap for building/testing the idea")
    difficulty: str = Field(description="One of: Easy, Medium, Hard, Expert")
    tech_stack: List[str] = Field(description="Specific list of tools, libraries, or frameworks (e.g., PyTorch, HuggingFace)")

class IdeaList(BaseModel):
    ideas: List[Idea] = Field(description="List of top 6-8 innovative ideas covering different categories based on identified gaps")

def innovation_architect_node(state: AgentState) -> Dict[str, Any]:
    llm = get_llm()
    parser = JsonOutputParser(pydantic_object=IdeaList)
    
    gaps_summary = json.dumps(state.get("research_gaps", []), indent=2)
    
    # Also get paper context for domain-specific ideas
    paper_context = ""
    for filename, analysis in state.get("paper_analyses", {}).items():
        paper_context += f"Paper Title: {analysis.get('title', '')}\nAbstract: {analysis.get('abstract', '')[:500]}\n\n"
    
    prompt = PromptTemplate(
        template=(
            "You are an Innovation Architect generating research and project ideas.\n"
            "Review the identified research gaps and the papers' context below.\n"
            "Generate up to 8 highly innovative, domain-specific research ideas.\n"
            "Ensure you produce a mix of: Incremental, Moderate Innovation, and High-Risk High-Reward ideas.\n"
            "{format_instructions}\n\n"
            "Paper Domain Context:\n{paper_context}\n\n"
            "Research Gaps:\n{gaps}\n"
        ),
        input_variables=["gaps", "paper_context"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    
    chain = prompt | llm | parser
    
    try:
        res = chain.invoke({"gaps": gaps_summary[:20000], "paper_context": paper_context[:5000]})
        ideas = res.get("ideas", [])
        normalized = []
        for idea in ideas:
            if isinstance(idea, dict):
                normalized.append({
                    "title": idea.get("title", "Research Idea"),
                    "innovation_category": idea.get("innovation_category", "Moderate Innovation"),
                    "description": idea.get("description", ""),
                    "novelty_score": idea.get("novelty_score", 7.0),
                    "feasibility_score": idea.get("feasibility_score", 7.0),
                    "required_dataset": idea.get("required_dataset", "None specified"),
                    "methodology": idea.get("methodology", ""),
                    "expected_outcome": idea.get("expected_outcome", ""),
                    "implementation_roadmap": idea.get("implementation_roadmap", []),
                    "difficulty": idea.get("difficulty", "Medium"),
                    "tech_stack": idea.get("tech_stack", []),
                })
        return {"project_ideas": normalized}
    except Exception as e:
        print(f"Error architecting ideas: {e}")
        return {"project_ideas": []}
