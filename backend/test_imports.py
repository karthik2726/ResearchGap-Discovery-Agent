import sys
try:
    import numpy
    print(f"NumPy version: {numpy.__version__}")
    import pydantic
    import chromadb
    import fastapi
    import uvicorn
    import langchain
    import pdfplumber
    import cryptography
    import cffi
    import fitz # PyMuPDF
    print("SUCCESS: All critical dependencies imported correctly!")
except Exception as e:
    print(f"ERROR during import: {e}")
    sys.exit(1)
