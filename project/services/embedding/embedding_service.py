from langchain_huggingface import HuggingFaceEmbeddings

def get_embedding_model(model_name="BAAI/bge-m3"):
    return HuggingFaceEmbeddings(model_name=model_name)
