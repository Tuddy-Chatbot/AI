import os
from services.ocr.pdf_service import pdf_to_images
from services.ocr.ocr_service import upscale_image, run_document_text_detection
from services.ocr.clean_service import process_cleaning
from services.ocr.gemini_service import process_gemini_reorder
import time

def remove_file_safely(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"[DEL] {file_path}")
    except Exception as e:
        print(f"[ERR] 파일 삭제 실패: {file_path} - {e}")
        
def process_pdf_pipeline(pdf_path: str, session_dir: str):
    timing_per_step = {
        "upscale": [],
        "ocr": [],
        "clean": [],
        "gemini": []
    }
    
    image_paths = pdf_to_images(pdf_path, session_dir)
    results = []
    
    upscaled_paths, ocr_json_paths, cleaned_txt_paths = [], [], []

    for idx, image_path in enumerate(image_paths, start=1):
        # upscale
        start = time.perf_counter()
        try:
            upscaled_path = upscale_image(image_path, 1.5)
            upscaled_paths.append(upscaled_path)
            timing_per_step["upscale"].append(time.perf_counter() - start)
        except Exception as e:
            print(f"[ERR] {idx}번째 슬라이드 업스케일 처리 중 문제 발생: {e}")
            upscaled_path = None

        # OCR
        start = time.perf_counter()
        try:
            if upscaled_path:
                ocr_json_path = run_document_text_detection(upscaled_path)
                ocr_json_paths.append(ocr_json_path)
                timing_per_step["ocr"].append(time.perf_counter() - start)
            else:
                ocr_json_path = None
        except Exception as e:
            print(f"[ERR] {idx}번째 슬라이드 OCR 처리 중 문제 발생: {e}")
            ocr_json_path = None

        # llm 전달 전처리
        start = time.perf_counter()
        try:
            if ocr_json_path:
                cleaned_txt_path = process_cleaning(ocr_json_path)
                cleaned_txt_paths.append(cleaned_txt_path)
                timing_per_step["clean"].append(time.perf_counter() - start)
            else:
                cleaned_txt_path = None
        except Exception as e:
            print(f"[ERR] {idx}번째 슬라이드 Cleaning 처리 중 문제 발생: {e}")
            cleaned_txt_path = None

        # gemini
        start = time.perf_counter()
        try:
            if cleaned_txt_path:
                gemini_json_path = process_gemini_reorder(cleaned_txt_path, idx)
                timing_per_step["gemini"].append(time.perf_counter() - start)
            else:
                gemini_json_path = None
        except Exception as e:
            print(f"[ERR] {idx}번째 슬라이드 Gemini 처리 중 문제 발생: {e}")
            gemini_json_path = None

        results.append({
            "slide": idx,
            "image": upscaled_path,
            "ocr_json": ocr_json_path,
            "cleaned_txt": cleaned_txt_path,
            "gemini_json": gemini_json_path
        })

    # 최종 파일 제외하고 임시파일 삭제
    for path in image_paths + [p for p in upscaled_paths if p] + [p for p in ocr_json_paths if p] + [p for p in cleaned_txt_paths if p]:
        remove_file_safely(path)

        
    # 삭제된 임시파일들은 results에서 삭제
    for result in results:
        result.pop("image", None)      # upscaled_path가 저장되어 있음
        result.pop("ocr_json", None)
        result.pop("cleaned_txt", None)
        
    # 단계별 시간 평균 계산 (실패한 단계 제외)
    timing_summary = {}
    for step, times in timing_per_step.items():
        valid_times = [t for t in times if t is not None]
        timing_summary[f"{step}_avg"] = round(sum(valid_times)/len(valid_times), 3) if valid_times else 0.0

    return results, timing_summary