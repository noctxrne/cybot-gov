import os
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from sklearn.svm import LinearSVC
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

# Import the new LanceDB VectorStoreManager
from app.services.vector_store import VectorStoreManager  # Updated import

class HybridRAGService:
    def __init__(self, config):
        self.config = config
        self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
        
        # Initialize LanceDB vector store
        self.vector_store = VectorStoreManager(
            db_path=os.path.join(config.VECTOR_STORE_PATH, "lancedb"),
            table_name="cyber_laws"
        )
        
        # Intent classifier setup
        self.intent_classifier = None
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.setup_intent_classifier()
    
    def setup_intent_classifier(self):
        """Setup intent classification with common cyber law queries"""
        # Training data for intent classification
        intents = {
            'definition': [
                "What is hacking?",
                "Define phishing",
                "What does cyber crime mean?",
                "Explain digital signature",
                "What is the IT Act?"
            ],
            'penalty': [
                "What is the punishment for hacking?",
                "Penalty for data theft",
                "Fine for cyber fraud",
                "Jail term for online harassment",
                "Legal consequences of phishing"
            ],
            'procedure': [
                "How to file cyber crime complaint?",
                "Procedure for digital signature",
                "Steps to report online fraud",
                "Process for data protection compliance",
                "How to register cyber complaint?"
            ],
            'section': [
                "Section 66 of IT Act",
                "What is Section 43A?",
                "Explain IT Act Section 72",
                "Cyber law section for hacking",
                "Legal section for data breach"
            ]
        }
        
        # Prepare training data
        X_train = []
        y_train = []
        
        for intent, examples in intents.items():
            X_train.extend(examples)
            y_train.extend([intent] * len(examples))
        
        # Vectorize and train
        if X_train:
            X_vec = self.vectorizer.fit_transform(X_train)
            self.intent_classifier = LinearSVC()
            self.intent_classifier.fit(X_vec, y_train)
    
    def classify_intent(self, query: str) -> str:
        """Classify user query intent"""
        if not self.intent_classifier:
            return "general"
        
        query_vec = self.vectorizer.transform([query])
        intent = self.intent_classifier.predict(query_vec)[0]
        return intent
    
    def search_documents(self, query: str, intent: str, top_k: int = 5) -> List[Dict]:
        """Search relevant documents using hybrid approach"""
        try:
            # Search using LanceDB vector store
            search_results = self.vector_store.search(query, n_results=top_k * 2)
            
            # Filter and format results
            filtered_results = []
            for result in search_results:
                # LanceDB returns results as dict with '_distance' field
                score = 1 - (result.get('_distance', 1.0) / 2) if '_distance' in result else 0.8
                
                # Intent-based filtering
                if intent == 'section' and 'section' not in query.lower():
                    # For section queries, prioritize section metadata
                    if 'section_title' in result:
                        filtered_results.append({
                            'content': result.get('text', ''),
                            'metadata': {k: v for k, v in result.items() if k not in ['text', 'embedding', '_distance']},
                            'score': score
                        })
                else:
                    filtered_results.append({
                        'content': result.get('text', ''),
                        'metadata': {k: v for k, v in result.items() if k not in ['text', 'embedding', '_distance']},
                        'score': score
                    })
            
            # Sort by score and return top_k
            filtered_results.sort(key=lambda x: x['score'], reverse=True)
            return filtered_results[:top_k]
            
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def generate_response(self, query: str, context: List[Dict]) -> Dict[str, Any]:
        """Generate response using RAG pattern"""
        # Extract relevant information
        relevant_texts = [item['content'] for item in context]
        combined_context = "\n\n".join(relevant_texts)
        
        # Create response template based on intent
        intent = self.classify_intent(query)
        
        response_template = f"""Based on the Cyber Laws, here's the information:

Context from relevant laws:
{combined_context[:2000]}  # Limit context length

Answer: """
        
        # Add disclaimer
        disclaimer = "\n\n**Disclaimer**: This information is based on available cyber laws. For legal advice, please consult a qualified legal professional."
        
        # Extract metadata sources
        sources = []
        for item in context:
            metadata = item['metadata']
            source_info = {
                'title': metadata.get('filename', 'Unknown'),
                'section': metadata.get('section_title', ''),
                'confidence': round(item['score'] * 100, 2)
            }
            sources.append(source_info)
        
        return {
            'answer': response_template + disclaimer,
            'intent': intent,
            'sources': sources,
            'confidence': round(np.mean([item['score'] for item in context]) * 100, 2) if context else 0,
            'context_used': len(relevant_texts)
        }
    
    def query(self, user_query: str) -> Dict[str, Any]:
        """Main query method"""
        # Classify intent
        intent = self.classify_intent(user_query)
        
        # Search relevant documents
        context = self.search_documents(user_query, intent)
        
        # Generate response
        if context:
            response = self.generate_response(user_query, context)
        else:
            response = {
                'answer': "I couldn't find specific information on that topic in the cyber laws database. Please try rephrasing your question or contact legal authorities for specific queries.",
                'intent': intent,
                'sources': [],
                'confidence': 0,
                'context_used': 0
            }
        
        return response