from core.llm import get_llm
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from agents.state import AgentState

class WritingEvaluation(BaseModel):
    writing_problems: List[str] = Field(description="Examples of writing problems (e.g. contradictions, citation gaps)")
    improvement_suggestions: List[str] = Field(description="Suggestions for improving academic writing")
    readability_score: float = Field(description="Score from 0.0 to 100.0 for readability")
    clarity_score: float = Field(description="Score from 0.0 to 100.0 for clarity")
    academic_quality_score: float = Field(description="Score from 0.0 to 100.0 for academic quality")
    humanization_score: float = Field(description="Score from 0.0 to 100.0 for how natural and academically polished the writing appears")

def writing_evaluator_node(state: AgentState) -> Dict[str, Any]:
    llm = get_llm()
    parser = JsonOutputParser(pydantic_object=WritingEvaluation)
    
    prompt = PromptTemplate(
        template="You are an Academic Writing Evaluator.\n"
                 "Analyze the writing quality of the following research paper abstract and intro/methodology excerpts.\n"
                 "Do NOT claim AI detection. Instead provide a Humanization Score evaluating how natural, varied, and academically polished it is.\n"
                 "{format_instructions}\n\n"
                 "Paper Excerpt:\n{paper_text}\n",
        input_variables=["paper_text"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    
    chain = prompt | llm | parser
    evals = {}
    
    for filename, text in state.get("paper_texts", {}).items():
        try:
            # We sample the first 10,000 characters for writing evaluation
            sample_text = text[:10000]
            res = chain.invoke({"paper_text": sample_text})
            evals[filename] = res
        except Exception as e:
            print(f"Error evaluating writing for {filename}: {e}")
            evals[filename] = {
                "writing_problems": ["Error during evaluation"],
                "improvement_suggestions": [],
                "readability_score": 50.0,
                "clarity_score": 50.0,
                "academic_quality_score": 50.0,
                "humanization_score": 50.0
            }
            
    return {"writing_evaluations": evals}
