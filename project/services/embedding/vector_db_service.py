import os
from dotenv import load_dotenv
from typing import List, Tuple, Optional
from pinecone import Pinecone
from langchain_core.documents import Document
from langchain_pinecone import PineconeVectorStore

load_dotenv()

def init_vector_store(embedding_model, index_name: str, namespace: Optional[str] = None):
    """
    Pinecone 벡터스토어 초기화
    """
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("환경변수 PINECONE_API_KEY가 필요합니다.")

    pc = Pinecone(api_key=api_key)
    index = pc.Index(index_name)

    # PineconeVectorStore는 namespace를 인자로 받을 수 있음
    vector_store = PineconeVectorStore(
        embedding=embedding_model,
        index=index,
        namespace=namespace
    )
    return vector_store


def add_documents_to_vector_db(vector_store: PineconeVectorStore, docs: List[Document]):
    """
    문서 리스트를 벡터 DB에 추가
    """
    if not docs:
        print("추가할 문서가 없습니다.")
        return []

    ids = vector_store.add_documents(docs)
    print(f"{len(ids)}개의 문서가 벡터 DB에 추가되었습니다.")
    return ids

def search_documents(
    embedding_model,
    index_name: str,
    namespace: str,
    query: str,
    k: int = 3
) -> List[Tuple[Document, float]]:
    """
    특정 namespace 내에서 유사 문서 검색
    """
    vector_store = init_vector_store(embedding_model, index_name, namespace)
    results = vector_store.similarity_search_with_score(query, k=k, namespace=namespace)
    return results