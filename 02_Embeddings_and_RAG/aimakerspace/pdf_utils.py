import os
from typing import List, Dict, Any, Optional
import logging

# PDF processing imports
try:
    import PyPDF2
    import pdfplumber
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logging.warning("PDF processing libraries not available. Install PyPDF2, pdfplumber, and pymupdf for PDF support.")


class PDFLoader:
    """Loader for PDF documents with multiple extraction strategies."""
    
    def __init__(self, path: str, extraction_method: str = "pdfplumber"):
        """
        Initialize PDF loader.
        
        Args:
            path: Path to PDF file
            extraction_method: Method to use for text extraction ("pdfplumber", "pymupdf", "pypdf2")
        """
        if not PDF_AVAILABLE:
            raise ImportError("PDF processing libraries not available. Install PyPDF2, pdfplumber, and pymupdf.")
        
        self.path = path
        self.extraction_method = extraction_method
        self.documents = []
        self.metadata = []
        
    def extract_text_pdfplumber(self) -> List[Dict[str, Any]]:
        """Extract text using pdfplumber (good for complex layouts)."""
        results = []
        try:
            with pdfplumber.open(self.path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text and text.strip():
                        results.append({
                            'text': text.strip(),
                            'page': page_num + 1,
                            'method': 'pdfplumber',
                            'source': self.path
                        })
        except Exception as e:
            logging.error(f"Error extracting text with pdfplumber: {e}")
        return results
    
    def extract_text_pymupdf(self) -> List[Dict[str, Any]]:
        """Extract text using PyMuPDF (fast and reliable)."""
        results = []
        try:
            doc = fitz.open(self.path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                if text and text.strip():
                    results.append({
                        'text': text.strip(),
                        'page': page_num + 1,
                        'method': 'pymupdf',
                        'source': self.path
                    })
            doc.close()
        except Exception as e:
            logging.error(f"Error extracting text with PyMuPDF: {e}")
        return results
    
    def extract_text_pypdf2(self) -> List[Dict[str, Any]]:
        """Extract text using PyPDF2 (basic extraction)."""
        results = []
        try:
            with open(self.path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    if text and text.strip():
                        results.append({
                            'text': text.strip(),
                            'page': page_num + 1,
                            'method': 'pypdf2',
                            'source': self.path
                        })
        except Exception as e:
            logging.error(f"Error extracting text with PyPDF2: {e}")
        return results
    
    def extract_text_hybrid(self) -> List[Dict[str, Any]]:
        """Try multiple methods and combine results."""
        methods = ['pymupdf', 'pdfplumber', 'pypdf2']
        all_results = []
        
        for method in methods:
            try:
                if method == 'pymupdf':
                    results = self.extract_text_pymupdf()
                elif method == 'pdfplumber':
                    results = self.extract_text_pdfplumber()
                elif method == 'pypdf2':
                    results = self.extract_text_pypdf2()
                
                if results:
                    all_results.extend(results)
                    break  # Use first successful method
            except Exception as e:
                logging.warning(f"Method {method} failed: {e}")
                continue
        
        return all_results
    
    def load_documents(self) -> List[str]:
        """Load and extract text from PDF."""
        if self.extraction_method == "hybrid":
            results = self.extract_text_hybrid()
        elif self.extraction_method == "pdfplumber":
            results = self.extract_text_pdfplumber()
        elif self.extraction_method == "pymupdf":
            results = self.extract_text_pymupdf()
        elif self.extraction_method == "pypdf2":
            results = self.extract_text_pypdf2()
        else:
            raise ValueError(f"Unknown extraction method: {self.extraction_method}")
        
        # Store metadata for later use
        self.metadata = results
        
        # Extract just the text for compatibility
        self.documents = [result['text'] for result in results]
        return self.documents
    
    def get_metadata(self) -> List[Dict[str, Any]]:
        """Get metadata for extracted documents."""
        return self.metadata


class DocumentLoader:
    """Unified document loader that handles multiple file types."""
    
    def __init__(self, path: str, encoding: str = "utf-8"):
        self.path = path
        self.encoding = encoding
        self.documents = []
        self.metadata = []
    
    def load_documents(self) -> List[str]:
        """Load documents from the specified path."""
        if os.path.isdir(self.path):
            self._load_directory()
        elif os.path.isfile(self.path):
            self._load_single_file()
        else:
            raise ValueError("Provided path is neither a valid directory nor a file.")
        
        return self.documents
    
    def _load_single_file(self):
        """Load a single file based on its extension."""
        if self.path.endswith(".txt"):
            with open(self.path, "r", encoding=self.encoding) as f:
                self.documents.append(f.read())
        elif self.path.endswith(".pdf"):
            if PDF_AVAILABLE:
                pdf_loader = PDFLoader(self.path)
                self.documents = pdf_loader.load_documents()
                self.metadata = pdf_loader.get_metadata()
            else:
                raise ImportError("PDF processing not available. Install required libraries.")
        else:
            raise ValueError(f"Unsupported file format: {self.path}")
    
    def _load_directory(self):
        """Load all supported files from a directory."""
        for root, _, files in os.walk(self.path):
            for file in files:
                file_path = os.path.join(root, file)
                if file.endswith(".txt"):
                    with open(file_path, "r", encoding=self.encoding) as f:
                        self.documents.append(f.read())
                elif file.endswith(".pdf") and PDF_AVAILABLE:
                    pdf_loader = PDFLoader(file_path)
                    self.documents.extend(pdf_loader.load_documents())
                    self.metadata.extend(pdf_loader.get_metadata())
    
    def get_metadata(self) -> List[Dict[str, Any]]:
        """Get metadata for loaded documents."""
        return self.metadata 