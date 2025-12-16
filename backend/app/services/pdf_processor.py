import os
import re
from typing import List, Dict, Any
import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import hashlib
from datetime import datetime

# Import the new LanceDB VectorStoreManager
from app.services.vector_store import VectorStoreManager  # Updated import

class PDFProcessor:
    def __init__(self, config):
        self.config = config
        self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Initialize LanceDB vector store
        os.makedirs(config.VECTOR_STORE_PATH, exist_ok=True)
        self.vector_store = VectorStoreManager(
            db_path=os.path.join(config.VECTOR_STORE_PATH, "lancedb"),
            table_name="cyber_laws"
        )
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF with structure preservation"""
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Extract text with layout preservation
                    page_text = page.extract_text(x_tolerance=1, y_tolerance=1)
                    if page_text:
                        # Add page marker
                        text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
        except Exception as e:
            raise Exception(f"PDF extraction failed: {str(e)}")
        return text
    
    def extract_cyber_law_sections(self, text: str) -> List[Dict[str, Any]]:
        """Extract cyber law specific sections using patterns"""
        sections = []
        
        # Patterns for Indian Cyber Laws
        patterns = [
            r'(IT\s+Act,\s*2000|Information\s+Technology\s+Act,\s*2000)',
            r'SECTION\s+\d+[A-Z]*\s*[:\.]?\s*(.+)',
            r'(Cyber\s+Crime|Cyber\s+Security|Data\s+Protection|Digital\s+Signature)',
            r'^\s*(\d+[\.\)])\s+(.+)$',  # Numbered sections
        ]
        
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for section headers
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    if current_section:
                        sections.append(current_section)
                    
                    current_section = {
                        'title': line,
                        'content': '',
                        'type': 'section',
                        'keywords': self.extract_keywords(line)
                    }
                    break
            else:
                # Add to current section
                if current_section:
                    current_section['content'] += line + ' '
        
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords"""
        cyber_keywords = [
            'hacking', 'phishing', 'malware', 'data breach', 'encryption',
            'digital signature', 'electronic record', 'cyber terrorism',
            'identity theft', 'privacy', 'certifying authority', 'intermediary',
            'computer resource', 'network service', 'electronic governance'
        ]
        
        found_keywords = []
        text_lower = text.lower()
        for keyword in cyber_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def create_chunks(self, text: str, metadata: Dict) -> List[Dict]:
        """Split text into chunks for embedding"""
        chunks = self.text_splitter.split_text(text)
        
        chunk_data = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                'chunk_index': i,
                'chunk_id': f"{metadata.get('document_id', '')}_chunk_{i}",
                'word_count': len(chunk.split()),
                'char_count': len(chunk)
            })
            
            chunk_data.append({
                'content': chunk,
                'metadata': chunk_metadata
            })
        
        return chunk_data
    
    def add_to_vector_store(self, chunks: List[Dict]) -> int:
        """Add chunks to LanceDB vector database"""
        try:
            # Prepare data for LanceDB
            documents = []
            metadatas = []
            
            for chunk in chunks:
                documents.append(chunk['content'])
                metadatas.append(chunk['metadata'])
            
            # Add to vector store (LanceDB handles embeddings internally)
            chunks_added = self.vector_store.add_documents(documents, metadatas)
            
            return chunks_added
            
        except Exception as e:
            raise Exception(f"Vector store update failed: {str(e)}")
    
    def process_document(self, file_path: str, metadata: Dict) -> Dict[str, Any]:
        """Main processing pipeline"""
        try:
            # Extract text
            print(f"Extracting text from {file_path}")
            text = self.extract_text_from_pdf(file_path)
            
            # Extract sections
            print("Extracting cyber law sections...")
            sections = self.extract_cyber_law_sections(text)
            
            # Create chunks
            print("Creating chunks...")
            all_chunks = []
            for section in sections:
                section_metadata = metadata.copy()
                section_metadata.update({
                    'section_title': section['title'],
                    'keywords': section['keywords']
                })
                
                chunks = self.create_chunks(section['content'], section_metadata)
                all_chunks.extend(chunks)
            
            # Add to vector store
            print("Adding to vector database...")
            chunks_added = self.add_to_vector_store(all_chunks)
            
            return {
                'success': True,
                'total_sections': len(sections),
                'total_chunks': chunks_added,
                'sections': sections[:5]  # Return first 5 sections as sample
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }