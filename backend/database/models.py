from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    upload_time = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Extracted data
    title = Column(String, nullable=True)
    abstract = Column(Text, nullable=True)
    methodology = Column(Text, nullable=True)
    datasets = Column(JSON, nullable=True)
    results = Column(Text, nullable=True)
    limitations = Column(Text, nullable=True)
    references = Column(JSON, nullable=True)
    
    # Audit Scores
    reliability_score = Column(Float, nullable=True)
    humanization_score = Column(Float, nullable=True)
    quality_audit = Column(JSON, nullable=True)
    writing_evaluation = Column(JSON, nullable=True)
    
class ResearchGap(Base):
    __tablename__ = "research_gaps"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    gap_type = Column(String, nullable=True)
    description = Column(Text)
    evidence = Column(Text, nullable=True)
    potential_impact = Column(String)
    research_opportunity = Column(Text, nullable=True)
    difficulty_score = Column(Float)

class ProjectIdea(Base):
    __tablename__ = "project_ideas"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    innovation_category = Column(String, nullable=True)
    description = Column(Text)
    novelty_score = Column(Float, nullable=True)
    feasibility_score = Column(Float, nullable=True)
    required_dataset = Column(Text, nullable=True)
    methodology = Column(Text, nullable=True)
    expected_outcome = Column(Text, nullable=True)
    implementation_roadmap = Column(JSON, nullable=True)
    difficulty = Column(String)
    tech_stack = Column(JSON)
    implementation_plan = Column(Text)
    
class TopicCluster(Base):
    __tablename__ = "topic_clusters"
    
    id = Column(Integer, primary_key=True, index=True)
    cluster_name = Column(String)
    themes = Column(JSON)
    emerging_areas = Column(JSON, nullable=True)
    paper_ids = Column(JSON) # List of paper IDs in this cluster
    size = Column(Integer, nullable=True)

class ParentChunk(Base):
    __tablename__ = "parent_chunks"

    id = Column(String, primary_key=True, index=True)
    paper_id = Column(Integer, index=True)
    source_file = Column(String)
    text = Column(Text)
    page_number = Column(Integer)
    section = Column(String)

class GlobalReport(Base):
    __tablename__ = "global_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    research_landscape = Column(Text, nullable=True)
    master_report = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

