# test_import.py
try:
    from sentence_transformers import SentenceTransformer
    print('✅ sentence-transformers import successful!')
    # Try to load a model
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print('✅ Model loaded!')
    print(f'   Embedding dimension: {model.get_sentence_embedding_dimension()}')
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()