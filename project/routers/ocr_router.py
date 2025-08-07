from fastapi import APIRouter, UploadFile, File
import os
from services.ocr.pipeline_service import process_pdf_pipeline
from utils.file_utils import create_session_dir

router = APIRouter()

@router.post("/ocr")
async def process_pdf(file: UploadFile = File(...)):
    session_dir = create_session_dir("output")

    # PDF 임시 저장
    pdf_path = os.path.join(session_dir, file.filename)
    with open(pdf_path, "wb") as f:
        f.write(await file.read())

    # 전체 파이프라인 실행
    results = process_pdf_pipeline(pdf_path, session_dir)

    return {
        "status": "success",
        "session_dir": session_dir,
        "files": results
    }
