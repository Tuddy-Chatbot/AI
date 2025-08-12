from fastapi import APIRouter, UploadFile, File, Form
import os
from services.ocr.pipeline_service import process_pdf_pipeline
from utils.file_utils import create_session_dir

router = APIRouter()

@router.post("/ocr")
async def process_pdf(
    user_id: str = Form(...),
    file: UploadFile = File(...)
):
    # 사용자별 세션 디렉토리 생성
    session_dir = create_session_dir("output", user_id)

    # 파일 저장 경로: output/{user_id}/{timestamp}_{filename}
    pdf_path = os.path.join(session_dir, f"{os.path.basename(session_dir)}_{file.filename}")
    with open(pdf_path, "wb") as f:
        f.write(await file.read())

    # 전체 파이프라인 실행
    results = process_pdf_pipeline(pdf_path, session_dir)

    return {
        "status": "success",
        "user_id": user_id,
        "session_dir": session_dir,
        "files": results
    }
