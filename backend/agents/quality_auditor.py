from core.llm import get_llm
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from agents.state import AgentState

class QualityAudit(BaseModel):
    methodology_problems: List[str] = Field(description="List of methodology problems like small sample size")
    statistical_problems: List[str] = Field(description="List of statistical problems like unsupported conclusions")
    reproducibility_problems: List[str] = Field(description="List of reproducibility problems like missing code")
    reliability_score: float = Field(description="Score from 0.0 to 100.0 indicating overall reliability")

def quality_auditor_node(state: AgentState) -> Dict[str, Any]:
    llm = get_llm()
    parser = JsonOutputParser(pydantic_object=QualityAudit)
    
    prompt = PromptTemplate(
        template="You are a Research Quality Auditor.\n"
                 "Evaluate the methodology, statistics, and reproducibility of the following research paper.\n"
                 "{format_instructions}\n\n"
                 "Paper Data:\n{paper_data}\n",
        input_variables=["paper_data"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    
    chain = prompt | llm | parser
    audits = {}
    
    for filename, analysis in state.get("paper_analyses", {}).items():
        try:
            # Provide abstract and methodology for auditing instead of full text to save tokens
            paper_data = f"Title: {analysis.get('title')}\nAbstract: {analysis.get('abstract')}\nMethodology: {analysis.get('methodology')}\nResults: {analysis.get('results')}"
            res = chain.invoke({"paper_data": paper_data[:15000]})
            audits[filename] = res
        except Exception as e:
            print(f"Error auditing {filename}: {e}")
            audits[filename] = {
                "methodology_problems": ["Error during audit"],
                "statistical_problems": [],
                "reproducibility_problems": [],
                "reliability_score": 50.0
            }
            
    return {"quality_audits": audits}
