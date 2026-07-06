from core.llm import get_llm
from langchain_core.prompts import PromptTemplate
from agents.state import AgentState
from typing import Dict, Any
import json

def strategist_node(state: AgentState) -> Dict[str, Any]:
    llm = get_llm()
    
    # Aggregate data
    landscape = state.get("research_landscape", "")
    gaps = json.dumps(state.get("research_gaps", [])[:5], indent=2)
    ideas = json.dumps(state.get("project_ideas", [])[:5], indent=2)
    
    # Calculate best/worst papers based on quality audit
    quality_audits = state.get("quality_audits", {})
    best_paper = ""
    weakest_paper = ""
    if quality_audits:
        sorted_papers = sorted(quality_audits.items(), key=lambda x: x[1].get("reliability_score", 0), reverse=True)
        best_paper = f"{sorted_papers[0][0]} (Score: {sorted_papers[0][1].get('reliability_score', 0)})"
        weakest_paper = f"{sorted_papers[-1][0]} (Score: {sorted_papers[-1][1].get('reliability_score', 0)})"
        
    prompt = PromptTemplate(
        template="You are the Chief Research Strategist.\n"
                 "Generate a comprehensive Master Intelligence Report using the aggregated data.\n"
                 "Include: Executive Summary, Research Landscape, Top Gaps, Best Ideas, Most Reliable Paper, Weakest Paper, and Recommendations.\n"
                 "Use Markdown format.\n\n"
                 "Data:\n"
                 "Landscape: {landscape}\n"
                 "Top Gaps: {gaps}\n"
                 "Top Ideas: {ideas}\n"
                 "Most Reliable Paper: {best_paper}\n"
                 "Weakest Paper: {weakest_paper}\n",
        input_variables=["landscape", "gaps", "ideas", "best_paper", "weakest_paper"]
    )
    
    chain = prompt | llm
    
    try:
        report = chain.invoke({
            "landscape": landscape,
            "gaps": gaps,
            "ideas": ideas,
            "best_paper": best_paper,
            "weakest_paper": weakest_paper
        }).content
        return {"master_report": report}
    except Exception as e:
        print(f"Error generating master report: {e}")
        return {"master_report": "# Master Intelligence Report\n\nError generating report."}
