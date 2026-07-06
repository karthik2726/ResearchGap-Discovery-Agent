from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./researchiq.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    # Detect schema changes and recreate database if out of sync
    from sqlalchemy import inspect
    inspector = inspect(engine)
    if inspector.has_table("research_gaps"):
        columns = [c["name"] for c in inspector.get_columns("research_gaps")]
        if "evidence" not in columns:
            print("ChromaDB/SQLite: Schema mismatch detected (e.g. missing 'evidence' column). Recreating database...")
            Base.metadata.drop_all(bind=engine)
            
            # Reset Vector Store and BM25 index data files as well
            try:
                import shutil
                if os.path.exists("./vector_store/chromadb_data"):
                    shutil.rmtree("./vector_store/chromadb_data")
                    print("ChromaDB: Cleared old vector data.")
                if os.path.exists("./vector_store/bm25_index.pkl"):
                    os.remove("./vector_store/bm25_index.pkl")
                    print("BM25: Cleared old index data.")
            except Exception as e:
                print(f"Error resetting vector data on schema change: {e}")
                
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
