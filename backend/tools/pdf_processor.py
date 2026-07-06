import fitz  # PyMuPDF
import pdfplumber
import os
import re

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts all text from a PDF file using PyMuPDF."""
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        print(f"Error extracting text with PyMuPDF: {e}")
        # Fallback to pdfplumber
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e2:
            print(f"Error extracting text with pdfplumber: {e2}")
            
    return text

def extract_pages_from_pdf(pdf_path: str) -> list[dict]:
    """Extracts pages from a PDF, returning a list of dicts with page number and raw text."""
    pages = []
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text = page.get_text()
                pages.append({
                    "page_number": page.number + 1,
                    "text": text
                })
    except Exception as e:
        print(f"Error page-extracting with PyMuPDF: {e}")
        # Fallback to pdfplumber
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    pages.append({
                        "page_number": page.page_number,
                        "text": text
                    })
        except Exception as e2:
            print(f"Error page-extracting with pdfplumber: {e2}")
            
    return pages

def detect_section(line: str, current_section: str) -> str:
    """Heuristic to detect section headers in research papers."""
    cleaned = line.strip()
    if not cleaned:
        return current_section
        
    # Remove numbering (e.g., "1. Introduction" -> "Introduction")
    norm = re.sub(r'^(?:[0-9\.\-\s]+|[I|V|X]+\.?\s+)', '', cleaned).lower().strip()
    
    sections = [
        'abstract', 'introduction', 'related work', 'background', 
        'methodology', 'methods', 'system architecture', 'experiments', 
        'experimental setup', 'results', 'discussion', 'conclusion', 
        'limitations', 'references', 'future work', 'acknowledgements'
    ]
    
    if norm in sections:
        return cleaned
        
    # Check for short uppercase headers
    if 3 < len(cleaned) < 50 and cleaned.isupper() and not cleaned.endswith('.'):
        return cleaned
        
    return current_section

def chunk_text_with_metadata(
    pages: list[dict], 
    source_file: str, 
    chunk_size: int = 1000, 
    overlap: int = 200,
    parent_size: int = 1500,
    parent_overlap: int = 250,
    child_size: int = 400,
    child_overlap: int = 50
) -> tuple[list[dict], list[dict]]:
    """
    Groups page sentences into parent chunks and child chunks.
    Preserves exact page numbers, section headers, and file origins.
    """
    # 1. First extract all sentences across the document with their page & section metadata
    sentences = []
    current_section = "Abstract"
    
    for page_dict in pages:
        page_num = page_dict["page_number"]
        text = page_dict["text"]
        lines = text.split('\n')
        
        for line in lines:
            cleaned_line = line.strip()
            if not cleaned_line:
                continue
                
            # Check for section header
            new_section = detect_section(cleaned_line, current_section)
            if new_section != current_section:
                current_section = new_section
                # Skip indexing section headers as separate sentences
                continue
                
            # Split line into sentences
            # simple regex splitting
            line_sentences = re.split(r'(?<=[.!?])\s+', cleaned_line)
            for s in line_sentences:
                s_clean = s.strip()
                if len(s_clean) > 5: # ignore very short noise
                    sentences.append({
                        "text": s_clean,
                        "page_number": page_num,
                        "section": current_section
                    })
                    
    # 2. Build Parent Chunks by grouping sentences
    parent_chunks = []
    parent_idx = 0
    
    i = 0
    while i < len(sentences):
        chunk_sentences = []
        chunk_len = 0
        
        j = i
        while j < len(sentences) and chunk_len < parent_size:
            chunk_sentences.append(sentences[j])
            chunk_len += len(sentences[j]["text"]) + 1
            j += 1
            
        if not chunk_sentences:
            break
            
        # Determine dominant metadata for parent chunk
        page_number = chunk_sentences[0]["page_number"]
        section = chunk_sentences[0]["section"]
        parent_text = " ".join([s["text"] for s in chunk_sentences])
        parent_id = f"{source_file}_parent_{parent_idx}"
        
        parent_chunks.append({
            "source_file": source_file,
            "page_number": page_number,
            "section": section,
            "chunk_id": parent_id,
            "text": parent_text
        })
        
        # Create child chunks inside this parent chunk
        child_chunks_list = []
        child_idx = 0
        
        start = 0
        while start < len(parent_text):
            end = start + child_size
            child_txt = parent_text[start:end]
            
            # Avoid cutting words in half
            if end < len(parent_text):
                last_space = child_txt.rfind(' ')
                if last_space > (child_size // 2):
                    end = start + last_space
                    child_txt = parent_text[start:end]
                    
            child_chunks_list.append({
                "source_file": source_file,
                "page_number": page_number,
                "section": section,
                "chunk_id": f"{parent_id}_child_{child_idx}",
                "parent_id": parent_id,
                "text": child_txt.strip()
            })
            child_idx += 1
            start += (child_size - child_overlap)
            if child_size - child_overlap <= 0:
                break
                
        parent_chunks[-1]["children"] = child_chunks_list
        parent_idx += 1
        
        # Advance i with sliding window overlap
        next_i = j
        overlap_len = 0
        while j > i and overlap_len < parent_overlap:
            j -= 1
            overlap_len += len(sentences[j]["text"]) + 1
            
        if j > i:
            i = j
        else:
            i = next_i
            
    # Flatten all children
    all_child_chunks = []
    for pc in parent_chunks:
        all_child_chunks.extend(pc.pop("children", []))
        
    return parent_chunks, all_child_chunks

