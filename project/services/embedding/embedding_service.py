from langchain_huggingface import HuggingFaceEmbeddings

# 애플리케이션 시작 시 한 번만 로드 (전역변수)
embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")

def get_embedding_model():
    return embedding_model
