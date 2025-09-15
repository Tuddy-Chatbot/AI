from fastapi import APIRouter, UploadFile, File, Form
import os
from services.ocr.pipeline_service import process_pdf_pipeline
from utils.file_utils import create_session_dir
from services.convert.ppt_to_pdf_service import ensure_pdf, PPT2PDFError
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
    
    # 1) 업로드 파일을 그대로 저장 
    with open(pdf_path, "wb") as f:
        f.write(await file.read())

    # 2) PPT/PPTX이면 PDF로 변환 
    #    - PDF면 그대로 경로 반환
    #    - 변환 실패 시 명확한 에러 반환
    start_conv = time.perf_counter()
    try:
        pdf_path = ensure_pdf(pdf_path, session_dir)
    except PPT2PDFError as e:
        # 변환 실패 시 기존 파이프라인 진입 전 에러 응답
        return {
            "status": "error",
            "user_id": user_id,
            "session_dir": session_dir,
            "message": str(e)
        }
    end_conv = time.perf_counter()

    # 3) 전체 파이프라인 실행 
    results, timing_pipeline = process_pdf_pipeline(pdf_path, session_dir)
    
    end_total = time.perf_counter()
    # 총 소요시간(업로드+변환+파이프라인) 기록 
    timing_pipeline["ppt2pdf_time"] = round(end_conv - start_conv, 3)
    timing_pipeline["total_time"] = round(end_total - start_total, 3)

    return {
        "status": "success",
        "user_id": user_id,
        "session_dir": session_dir,
        "files": results,
        "timing": timing_pipeline
    }
