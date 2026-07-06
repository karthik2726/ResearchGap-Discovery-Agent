from core.llm import get_llm
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from agents.state import AgentState

class PaperExtraction(BaseModel):
    title: str = Field(description="Title of the paper")
    abstract: str = Field(description="Abstract of the paper")
    methodology: str = Field(description="Methodology used in the paper")
    datasets: List[str] = Field(description="Datasets used in the paper")
    results: str = Field(description="Key results of the paper")
    limitations: str = Field(description="Limitations stated in the paper")
    references: List[str] = Field(description="Key references")

def analyst_node(state: AgentState) -> Dict[str, Any]:
    llm = get_llm()
    parser = JsonOutputParser(pydantic_object=PaperExtraction)
    
    prompt = PromptTemplate(
        template="You are a Research Paper Analyst.\n"
                 "Extract the requested information from the following research paper text.\n"
                 "If a section is not explicitly present, infer it or leave it empty, but follow the exact JSON format.\n"
                 "{format_instructions}\n\n"
                 "Paper Text:\n{text}\n",
        input_variables=["text"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    
    chain = prompt | llm | parser
    
    analyses = {}
    for filename, text in state["paper_texts"].items():
        # Truncate text to avoid context limits if necessary
        truncated_text = text[:100000] # roughly 20000-25000 tokens
        try:
            res = chain.invoke({"text": truncated_text})
            analyses[filename] = res
        except Exception as e:
            print(f"Failed to analyze {filename}: {e}")
            analyses[filename] = {
                "title": filename,
                "abstract": "Extraction failed",
                "methodology": "",
                "datasets": [],
                "results": "",
                "limitations": "",
                "references": []
            }
            
    return {"paper_analyses": analyses}
