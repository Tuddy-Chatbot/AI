from fastapi import APIRouter, UploadFile, File, Form
import os
from services.ocr.pipeline_service import process_pdf_pipeline
from utils.file_utils import create_session_dir
import time

router = APIRouter()

@router.post("/ocr")
async def process_pdf(
    user_id: str = Form(...),
    file: UploadFile = File(...)
):
    # 사용자별 세션 디렉토리 생성
    session_dir = create_session_dir("output", user_id)

    # pdf 파일 저장 경로: output/{user_id}/{timestamp}/{timestamp}_{filename}
    # basename는 경로의 가장 마지막 경로를 반환함
    pdf_path = os.path.join(session_dir, f"{os.path.basename(session_dir)}_{file.filename}")
    
    start_total = time.perf_counter()
    
    # open으로 파일 생성
    with open(pdf_path, "wb") as f:
        # 파일에 pdf 내용 작성
        f.write(await file.read())

    # 전체 파이프라인 실행
    results, timing_pipeline = process_pdf_pipeline(pdf_path, session_dir)
    
    end_total = time.perf_counter()
    timing_pipeline["total_time"] = round(end_total - start_total, 3)  # PDF 저장 + 파이프라인 전체 시간 포함

    return {
        "status": "success",
        "user_id": user_id,
        "session_dir": session_dir,
        "files": results,
        "timing": timing_pipeline
    }
