from fastapi import APIRouter, HTTPException, Query, Form
import os
import time
import shutil
import boto3
import asyncio

from services.ocr.pipeline_service import process_pdf_pipeline
from services.convert.ppt_to_pdf_service import ensure_pdf, PPT2PDFError
from utils.file_utils import create_session_dir 

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

AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
if not AWS_S3_BUCKET:
    raise ValueError("환경변수 AWS_S3_BUCKET가 설정되지 않았습니다.")

# --- Boto3 클라이언트 초기화 (애플리케이션 로드 시 1회) ---
# EC2 인스턴스 역할, ~/.aws/credentials, 환경변수 순으로 자격 증명 자동 탐지
s3_client = boto3.client('s3')

@router.post("/vectordb/ocr-and-add-from-s3")
async def process_and_add_from_s3(
    user_id: str = Form(...),
    file_key: str = Form(...) # S3 파일 키
):
    """
    S3에서 파일을 (boto3로) 직접 가져와 OCR 파이프라인을 실행하고,
    결과를 즉시 VectorDB에 추가한 뒤,
    성공 시 임시 생성된 디렉토리를 삭제합니다.
    """
    timing = {}
    start_total = time.perf_counter()
    
    # 1. 영구 세션 디렉토리 생성 (기존 OCR 라우터 방식)
    # [Goal 1] create_session_dir를 사용하여 작업 공간 확보
    session_dir = create_session_dir("output", user_id)
    
    try:
        # 2. S3/get 대신 boto3 다운로드 로직으로 변경
        start = time.perf_counter()
        # S3 Key에서 실제 파일 이름 추출 (file_key가 "path/to/file.pdf"일 경우)
        original_file_name = os.path.basename(file_key) 
        local_temp_path = os.path.join(session_dir, original_file_name)
        
        try:
            # s3_client.download_file은 동기(blocking) 함수이므로
            # asyncio.to_thread를 사용해 별도 스레드에서 실행 (FastAPI 이벤트 루프 차단 방지)
            await asyncio.to_thread(
                s3_client.download_file,
                AWS_S3_BUCKET,  # S3 버킷 이름
                file_key,       # S3 객체 키
                local_temp_path # 다운로드 받을 로컬 경로
            )
            timing['s3_download'] = round(time.perf_counter() - start, 3)
        except Exception as e:
            # 예: botocore.exceptions.ClientError, NoCredentialsError 등
            print(f"[ERR] S3 파일 다운로드 실패: {e}")
            raise HTTPException(status_code=500, detail=f"S3 파일 다운로드 실패 (boto3): {e}")

        # 3. [Goal 1] PPT -> PDF 변환
        start = time.perf_counter()
        try:
            pdf_path = ensure_pdf(local_temp_path, session_dir)
        except PPT2PDFError as e:
            raise HTTPException(status_code=400, detail=f"PPT 변환 실패: {e}")
        timing['ppt2pdf'] = round(time.perf_counter() - start, 3)

        # 4. [Goal 2] OCR 파이프라인 실행 (JSON 파일이 session_dir에 저장됨)
        start = time.perf_counter()
        ocr_results, ocr_timing = process_pdf_pipeline(pdf_path, session_dir)
        timing.update(ocr_timing) 
        
        # 5. [Goal 3] VectorDB에 추가하기 위한 문서 로드
        start = time.perf_counter()
        user_base_dir = os.path.join(BASE_DIR, user_id)
        date_folder = os.path.basename(session_dir) # (e.g., "251116-172245")
        
        docs = load_slide_documents_from_folder(user_base_dir, date_folder)
        if not docs:
            raise HTTPException(status_code=404, detail="OCR 처리 후 로드할 문서를 찾을 수 없습니다.")
        timing['doc_load'] = round(time.perf_counter() - start, 3)
        
        # 6. [Goal 3] VectorDB에 추가
        start = time.perf_counter()
        vector_store = get_vector_store(INDEX_NAME, namespace=user_id)
        ids = add_documents_to_vector_db(vector_store, docs, namespace=user_id)
        timing['vectordb_add'] = round(time.perf_counter() - start, 3)

        # 7. [Goal 4] 모든 작업 성공 시 디렉토리 삭제
        try:
            shutil.rmtree(session_dir)
            print(f"[CLEANUP] 작업 성공. 세션 디렉토리 삭제: {session_dir}")
        except Exception as e:
            print(f"[ERR] 세션 디렉토리 삭제 실패: {session_dir} - {e}")
            # (참고) 삭제 실패가 전체 트랜잭션을 실패시킬 필요는 없음

        timing['total_time'] = round(time.perf_counter() - start_total, 3)
        
        return {
            "status": "success",
            "message": "OCR 및 VectorDB 추가 완료",
            "added_count": len(ids),
            "namespace": user_id,
            "session_dir": session_dir, # 삭제되었지만 로그용으로 반환
            "timing": timing
        }

    except Exception as e:
        # 2~6 단계에서 오류 발생 시
        # [Goal 4]의 '성공 시 삭제' 조건에 따라 디렉토리는 삭제되지 않음.
        print(f"[ERR] 프로세스 실패. 디렉토리 유지: {session_dir}")
        if isinstance(e, HTTPException):
            raise e # HTTPException은 그대로 다시 발생시킴
        else:
            raise HTTPException(status_code=500, detail=f"전체 프로세스 실패: {e}")