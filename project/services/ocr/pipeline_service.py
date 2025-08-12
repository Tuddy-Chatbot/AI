import os
from services.ocr.pdf_service import pdf_to_images
from services.ocr.ocr_service import upscale_image, run_document_text_detection
from services.ocr.clean_service import process_cleaning
from services.ocr.gemini_service import process_gemini_reorder

def remove_file_safely(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"[DEL] {file_path}")
    except Exception as e:
        print(f"[ERR] 파일 삭제 실패: {file_path} - {e}")
        
def process_pdf_pipeline(pdf_path: str, session_dir: str):
    image_paths = pdf_to_images(pdf_path, session_dir)
    results = []
    
    upscaled_paths = []
    ocr_json_paths = []
    cleaned_txt_paths = []

    for idx, image_path in enumerate(image_paths, start=1):
        upscaled_path = upscale_image(image_path, 1.5)
        upscaled_paths.append(upscaled_path)

        ocr_json_path = run_document_text_detection(upscaled_path)
        ocr_json_paths.append(ocr_json_path)

        cleaned_txt_path = process_cleaning(ocr_json_path)
        cleaned_txt_paths.append(cleaned_txt_path)

        gemini_json_path = process_gemini_reorder(cleaned_txt_path, idx)

        results.append({
            "slide": idx,
            "image": upscaled_path,
            "ocr_json": ocr_json_path,
            "cleaned_txt": cleaned_txt_path,
            "gemini_json": gemini_json_path
        })

    # 최종 파일 제외하고 임시파일 삭제
    for path in image_paths + upscaled_paths + ocr_json_paths + cleaned_txt_paths:
        remove_file_safely(path)

    return results