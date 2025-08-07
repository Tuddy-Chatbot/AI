from fastapi import APIRouter, HTTPException, Query
from typing import List
import os

from services.embedding.document_loader import load_slide_documents_from_folder
from services.embedding.embedding_service import get_embedding_model
from services.embedding.vector_db_service import (
    init_vector_store,
    add_documents_to_vector_db,
    search_documents
)

router = APIRouter()

# 환경 설정
BASE_DIR = "/app/output"
INDEX_NAME = "rag-slides-index"

# 공용 임베딩 모델 초기화
embedding_model = get_embedding_model()

@router.post("/vectordb/add")
async def add_documents(
    user_id: str = Query(..., description="사용자 ID (namespace로 사용)"),
    date_folder: str = Query(..., description="슬라이드 JSON이 있는 날짜 폴더명")
):
    """
    사용자별 namespace(user_id)에 문서 추가
    """
    try:
        docs = load_slide_documents_from_folder(BASE_DIR, date_folder)
        if not docs:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
        
        vector_store = init_vector_store(embedding_model, INDEX_NAME, namespace=user_id)
        ids = add_documents_to_vector_db(vector_store, docs)

        return {
            "status": "success",
            "added_count": len(ids),
            "namespace": user_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vectordb/search")
async def search_in_vectordb(
    user_id: str = Query(..., description="검색할 사용자 ID (namespace)"),
    query: str = Query(..., description="검색할 질문"),
    k: int = 3
):
    """
    사용자별 namespace(user_id) 내에서만 검색
    """
    try:
        results = search_documents(
            embedding_model=embedding_model,
            index_name=INDEX_NAME,
            namespace=user_id,
            query=query,
            k=k
        )

        formatted_results = [
            {
                "score": float(score),
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            for doc, score in results
        ]

        return {
            "status": "success",
            "query": query,
            "namespace": user_id,
            "found_count": len(formatted_results),
            "results": formatted_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))