import os
import json
import numpy as np
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from core.llm import get_llm
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from agents.state import AgentState

class ClusterSummary(BaseModel):
    cluster_name: str = Field(description="Themes/Topic name for this cluster of papers")
    themes: List[str] = Field(description="List of 3-5 major themes/concepts discussed in these papers")
    emerging_areas: List[str] = Field(description="Emerging research areas or trends in this cluster")

class DomainLandscape(BaseModel):
    research_landscape: str = Field(description="A 2-3 paragraph summary of the overall research landscape covered by all papers")
    evolution_trends: List[str] = Field(description="List of key trends and evolution directions of research in this domain")

def get_paper_embeddings(state: AgentState) -> Dict[str, List[float]]:
    """Generates average embeddings for each paper using its title and abstract."""
    from vector_store.embeddings import bge_embedding_function
    paper_embeddings = {}
    for filename, analysis in state.get("paper_analyses", {}).items():
        text_to_embed = f"{analysis.get('title', filename)} {analysis.get('abstract', '')}"
        try:
            # Generate embedding using the BGE embedding function
            emb = bge_embedding_function([text_to_embed])[0]
            paper_embeddings[filename] = emb
        except Exception as e:
            print(f"Error embedding paper {filename}: {e}")
            # Fallback to zero vector
            paper_embeddings[filename] = [0.0] * 384
    return paper_embeddings

def mapper_node(state: AgentState) -> Dict[str, Any]:
    if not state.get("paper_analyses"):
        return {"topic_clusters": [], "research_landscape": "No data available."}
        
    llm = get_llm()
    
    # 1. Run K-Means Clustering on paper embeddings
    try:
        from sklearn.cluster import KMeans
        paper_embs = get_paper_embeddings(state)
        filenames = list(paper_embs.keys())
        
        if not filenames:
            return {"topic_clusters": [], "research_landscape": "No papers analyzed yet."}
            
        X = np.array([paper_embs[f] for f in filenames])
        n_papers = len(filenames)
        n_clusters = min(3, n_papers) if n_papers > 1 else 1
        
        clusters_map = {}
        if n_papers > 1:
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
            labels = kmeans.fit_predict(X)
            for label, fname in zip(labels, filenames):
                label_val = int(label)
                if label_val not in clusters_map:
                    clusters_map[label_val] = []
                clusters_map[label_val].append(fname)
        else:
            clusters_map[0] = [filenames[0]]
    except Exception as e:
        print(f"Clustering error: {e}")
        # Fallback to putting all papers in a single cluster
        filenames = list(state["paper_analyses"].keys())
        clusters_map = {0: filenames}
        n_clusters = 1

    # 2. Summarize each cluster using the LLM
    topic_clusters = []
    cluster_parser = JsonOutputParser(pydantic_object=ClusterSummary)
    
    for c_id, paper_files in clusters_map.items():
        papers_info = ""
        for f in paper_files:
            analysis = state["paper_analyses"][f]
            papers_info += f"Filename: {f}\nTitle: {analysis.get('title')}\nAbstract: {analysis.get('abstract')}\n\n"
            
        cluster_prompt = PromptTemplate(
            template="You are a Research Domain Expert.\n"
                     "Analyze the following group of papers in this cluster and identify their common topic cluster name, "
                     "major themes, and emerging areas.\n"
                     "{format_instructions}\n\n"
                     "Papers in Cluster:\n{papers}\n",
            input_variables=["papers"],
            partial_variables={"format_instructions": cluster_parser.get_format_instructions()},
        )
        
        cluster_chain = cluster_prompt | llm | cluster_parser
        try:
            res = cluster_chain.invoke({"papers": papers_info})
            topic_clusters.append({
                "name": res.get("cluster_name", f"Cluster {c_id + 1}"),
                "themes": res.get("themes", []),
                "emerging_areas": res.get("emerging_areas", []),
                "paper_filenames": paper_files,
                "size": len(paper_files) * 100 + 100
            })
        except Exception as e:
            print(f"Error analyzing cluster {c_id}: {e}")
            topic_clusters.append({
                "name": f"Topic Cluster {c_id + 1}",
                "themes": ["Research Trends"],
                "emerging_areas": ["Advanced Methodology"],
                "paper_filenames": paper_files,
                "size": len(paper_files) * 100 + 100
            })

    # 3. Generate Overall Research Landscape Summary
    landscape_parser = JsonOutputParser(pydantic_object=DomainLandscape)
    all_papers_summary = ""
    for f, analysis in state["paper_analyses"].items():
        all_papers_summary += f"Title: {analysis.get('title')}\nAbstract: {analysis.get('abstract')}\n\n"
        
    landscape_prompt = PromptTemplate(
        template="You are a Chief Research Strategist.\n"
                 "Analyze all of the following research papers and generate a comprehensive research landscape summary "
                 "and identify evolution trends across them.\n"
                 "{format_instructions}\n\n"
                 "All Research Papers:\n{all_papers}\n",
        input_variables=["all_papers"],
        partial_variables={"format_instructions": landscape_parser.get_format_instructions()},
    )
    
    landscape_chain = landscape_prompt | llm | landscape_parser
    try:
        landscape_res = landscape_chain.invoke({"all_papers": all_papers_summary[:25000]})
        landscape_text = landscape_res.get("research_landscape", "Error generating landscape.")
        # We can append trends to landscape text or return them inside state
        trends_text = "\n\n### Key Research Evolution & Trends:\n" + "\n".join([f"- {t}" for t in landscape_res.get("evolution_trends", [])])
        research_landscape = landscape_text + trends_text
    except Exception as e:
        print(f"Error generating landscape summary: {e}")
        research_landscape = "Error generating research landscape."
        
    return {
        "topic_clusters": topic_clusters,
        "research_landscape": research_landscape
    }
