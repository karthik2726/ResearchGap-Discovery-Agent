from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.analyst import analyst_node
from agents.mapper import mapper_node
from agents.gap_hunter import gap_hunter_node
from agents.innovation_architect import innovation_architect_node
from agents.quality_auditor import quality_auditor_node
from agents.writing_evaluator import writing_evaluator_node
from agents.strategist import strategist_node

def create_research_graph():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("mapper", mapper_node)
    workflow.add_node("gap_hunter", gap_hunter_node)
    workflow.add_node("innovation_architect", innovation_architect_node)
    workflow.add_node("quality_auditor", quality_auditor_node)
    workflow.add_node("writing_evaluator", writing_evaluator_node)
    workflow.add_node("strategist", strategist_node)
    
    # Define edges
    # Analyst feeds into everything
    workflow.add_edge("analyst", "mapper")
    workflow.add_edge("analyst", "quality_auditor")
    workflow.add_edge("analyst", "writing_evaluator")
    workflow.add_edge("analyst", "gap_hunter")
    
    # Gap hunter feeds into innovation architect
    workflow.add_edge("gap_hunter", "innovation_architect")
    
    # All of them feed into the strategist
    # Wait, in LangGraph we need a sequential flow or a parallel fan-out/fan-in.
    # Since nodes run sequentially in basic StateGraph if we link them, let's just make it a pipeline for simplicity
    # or use fan-out/fan-in by passing through.
    # Let's simplify to a sequential pipeline where state accumulates.
    
    # Re-define sequential workflow to accumulate state
    workflow_seq = StateGraph(AgentState)
    workflow_seq.add_node("analyst", analyst_node)
    workflow_seq.add_node("mapper", mapper_node)
    workflow_seq.add_node("gap_hunter", gap_hunter_node)
    workflow_seq.add_node("innovation_architect", innovation_architect_node)
    workflow_seq.add_node("quality_auditor", quality_auditor_node)
    workflow_seq.add_node("writing_evaluator", writing_evaluator_node)
    workflow_seq.add_node("strategist", strategist_node)
    
    workflow_seq.set_entry_point("analyst")
    workflow_seq.add_edge("analyst", "mapper")
    workflow_seq.add_edge("mapper", "gap_hunter")
    workflow_seq.add_edge("gap_hunter", "innovation_architect")
    workflow_seq.add_edge("innovation_architect", "quality_auditor")
    workflow_seq.add_edge("quality_auditor", "writing_evaluator")
    workflow_seq.add_edge("writing_evaluator", "strategist")
    workflow_seq.add_edge("strategist", END)
    
    return workflow_seq.compile()

research_graph = create_research_graph()
