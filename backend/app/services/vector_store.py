import lancedb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import pandas as pd
import os

class VectorStoreManager:
    def __init__(self, db_path="./data/lancedb", table_name="documents"):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.db = lancedb.connect(db_path)
        self.table_name = table_name
        # Create table if it doesn't exist
        try:
            self.table = self.db.open_table(table_name)
        except:
            self.table = None

    def add_documents(self, documents: List[str], metadatas: List[Dict]):
        # Generate embeddings
        embeddings = self.embedding_model.encode(documents).tolist()
        
        # Prepare data for LanceDB
        data = []
        for i, (doc, meta, emb) in enumerate(zip(documents, metadatas, embeddings)):
            data.append({
                "id": i,
                "text": doc,
                "embedding": emb,
                **meta  # Add all metadata fields
            })
        
        df = pd.DataFrame(data)
        
        if self.table is None:
            self.table = self.db.create_table(self.table_name, data=df)
        else:
            self.table.add(df)
        
        return len(data)
    
    def search(self, query: str, n_results: int = 5):
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()[0]
        
        # Perform the search
        results = self.table.search(query_embedding).limit(n_results).to_pandas()
        return results.to_dict('records')