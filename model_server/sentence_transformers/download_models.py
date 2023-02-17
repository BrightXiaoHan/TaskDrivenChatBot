from sentence_transformers import SentenceTransformer

model = SentenceTransformer("distiluse-base-multilingual-cased-v1")
del model
