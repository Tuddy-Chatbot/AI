import os
from services.ocr.pdf_service import pdf_to_images
from services.ocr.ocr_service import upscale_image, run_document_text_detection
from services.ocr.clean_service import process_cleaning
from services.ocr.gemini_service import process_gemini_reorder

def process_pdf_pipeline(pdf_path: str, session_dir: str):
    image_paths = pdf_to_images(pdf_path, session_dir)
    results = []

    for idx, image_path in enumerate(image_paths, start=1):
        upscaled_path = upscale_image(image_path, 1.5)
        ocr_json = run_document_text_detection(upscaled_path)
        cleaned_txt = process_cleaning(ocr_json)
        gemini_json = process_gemini_reorder(cleaned_txt, idx)

        results.append({
            "slide": idx,
            "image": upscaled_path,
            "ocr_json": ocr_json,
            "cleaned_txt": cleaned_txt,
            "gemini_json": gemini_json
        })

    return results
