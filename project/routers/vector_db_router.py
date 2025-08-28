from fastapi import APIRouter, HTTPException, Query
from typing import List
import os
import time

from services.embedding.document_loader import load_slide_documents_from_folder
from services.embedding.vector_db_service import (
    get_vector_store,
    add_documents_to_vector_db,
    search_documents
)

router = APIRouter()

# 환경 설정
BASE_DIR = "/app/output"
INDEX_NAME = "rag-slides-index"

@router.post("/vectordb/add")
async def add_documents_endpoint(
    user_id: str = Query(..., description="사용자 ID (namespace로 사용)"),
    date_folder: str = Query(..., description="슬라이드 JSON이 있는 날짜 폴더명")
):
    """
    사용자별 namespace(user_id)에 문서 추가
    """
    timing = {}
    start_total = time.perf_counter()
    try:
        user_base_dir = os.path.join(BASE_DIR, user_id)
        docs = load_slide_documents_from_folder(user_base_dir, date_folder)
        if not docs:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
        
        vector_store = get_vector_store(INDEX_NAME, namespace=user_id)
        ids = add_documents_to_vector_db(vector_store, docs, namespace=user_id)

        return {
            "status": "success",
            "added_count": len(ids),
            "namespace": user_id,
            "timing": timing
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        timing['total_time'] = round(time.perf_counter() - start_total, 3)


@router.post("/vectordb/search")
async def search_in_vectordb(
    user_id: str = Query(..., description="검색할 사용자 ID (namespace)"),
    query: str = Query(..., description="검색할 질문"),
    k: int = 3
):
    """
    사용자별 namespace(user_id) 내에서만 검색
    """
    timing = {}
    start_total = time.perf_counter()
    try:
        results = search_documents(
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
            "results": formatted_results,
            "timing": timing
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        timing['total_time'] = round(time.perf_counter() - start_total, 3)