import os
from dotenv import load_dotenv
from typing import List, Tuple, Optional
from pinecone import Pinecone
from langchain_core.documents import Document
from langchain_pinecone import PineconeVectorStore
from services.embedding.embedding_service import get_embedding_model 

load_dotenv()

# Pinecone 클라이언트도 애플리케이션 시작 시 한 번만 초기화
api_key = os.getenv("PINECONE_API_KEY")
if not api_key:
    raise ValueError("환경변수 PINECONE_API_KEY가 필요합니다.")
pc = Pinecone(api_key=api_key)

def get_vector_store(index_name: str, namespace: Optional[str] = None):
    """
    미리 생성된 Pinecone 클라이언트를 사용하여 VectorStore 객체를 반환
    """
    embedding_model = get_embedding_model()
    index = pc.Index(index_name)
    vector_store = PineconeVectorStore(
        embedding=embedding_model,
        index=index,
        namespace=namespace
    )
    return vector_store

def add_documents_to_vector_db(vector_store: PineconeVectorStore, docs: List[Document], namespace: str):
    """
    문서 리스트를 벡터 DB에 추가
    """
    if not docs:
        print("추가할 문서가 없습니다.")
        return []

    ids = vector_store.add_documents(docs, namespace=namespace)
    print(f"{len(ids)}개의 문서가 벡터 DB에 추가되었습니다.")
    return ids

def search_documents(
    index_name: str,
    namespace: str,
    query: str,
    k: int = 3
) -> List[Tuple[Document, float]]:
    """
    특정 namespace 내에서 유사 문서 검색
    """
    vector_store = get_vector_store(index_name, namespace)
    results = vector_store.similarity_search_with_score(query, k=k, namespace=namespace)
    return results