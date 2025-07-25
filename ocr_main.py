from google.cloud import vision
from google.oauth2 import service_account
import os
import json
import re
from PIL import Image
import pdf_to_images
import clean_for_llm
import gemini_just_reorder

# 공통 설정
key_path = os.path.expanduser("/home/key/rag_project_google_vision_service_account_key.json")
credentials = service_account.Credentials.from_service_account_file(key_path)
client = vision.ImageAnnotatorClient(credentials=credentials)
pdf_path = "/rag_project/ocr_test/google_vision/test_pdf.pdf"

# 이미지 확대 함수
def upscale_image(input_path, scale_factor):
    """
    이미지 파일을 지정된 배율만큼 확대하고 임시 파일로 저장한 뒤, 경로를 반환합니다.
    """
    img = Image.open(input_path)
    new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
    resized_img = img.resize(new_size, Image.LANCZOS)

    # 임시 저장 경로 설정
    upscaled_path = input_path.replace(".png", f"_upscaled_{int(scale_factor * 100)}.png")
    resized_img.save(upscaled_path)
    print(f"[INFO] 이미지가 {scale_factor}배 확대되어 '{upscaled_path}'로 저장되었습니다.")

    return upscaled_path

def run_document_text_detection(image_path):
    with open(image_path, "rb") as image_file:
        content = image_file.read()
    image = vision.Image(content=content)

    image_context = vision.ImageContext(language_hints=[])

    response = client.document_text_detection(image=image, image_context=image_context)
    full_text_annotation = response.full_text_annotation

    full_text_blocks = []
    printed_blocks = []
    handwritten_blocks = []

    threshold = 0.75  # 인쇄체 confidence 기준 (조정 가능)

    for page in full_text_annotation.pages:
        for block in page.blocks:
            block_text = ""
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    word_text = "".join([symbol.text for symbol in word.symbols])
                    block_text += word_text + " "
            block_text = block_text.strip()

            bbox = [
                {"x": v.x if v.x is not None else 0, "y": v.y if v.y is not None else 0}
                for v in block.bounding_box.vertices
            ]

            block_info = {
                "text": block_text,
                "confidence": round(block.confidence, 3),
                "bounding_poly": bbox,
            }

            # 전체 블록 저장
            full_text_blocks.append(block_info)

            # confidence 기준 분류
            if block.confidence >= threshold:
                printed_blocks.append(block_info)
            else:
                handwritten_blocks.append(block_info)

    # 결과 저장
    ocr_result_doc = {
        "full_text": full_text_annotation.text,         # 원본 전체 텍스트
        "full_text_blocks": full_text_blocks,           # 모든 블록 (confidence 무관)
        "printed_blocks": printed_blocks,               # confidence ≥ threshold
        "handwritten_blocks": handwritten_blocks,       # confidence < threshold
    }

    # 저장 파일명 생성
    filename = os.path.splitext(os.path.basename(image_path))[0]  # ex: 250721-1130-ocr_test-01
    output_path = os.path.join(os.path.dirname(image_path), f"{filename}_ocr_result.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ocr_result_doc, f, indent=2, ensure_ascii=False)
    print(f"[DOCUMENT_TEXT_DETECTION] OCR 결과가 '{output_path}'로 저장되었습니다.")


def main():
    # 슬라이드 이미지 생성 및 저장
    image_paths = pdf_to_images.pdf_to_images(pdf_path)
    image_dir = os.path.dirname(image_paths[0]) if image_paths else None

    scale_factor = 1.5
    
    for idx, image_path in enumerate(image_paths, start=1):
        upscaled_path = upscale_image(image_path, scale_factor=scale_factor)
        run_document_text_detection(upscaled_path)

        filename = os.path.splitext(os.path.basename(upscaled_path))[0]
        ocr_json_path = os.path.join(os.path.dirname(upscaled_path), f"{filename}_ocr_result.json")
        cleaned_txt_path = os.path.join(os.path.dirname(upscaled_path), f"{filename}_cleaned.txt")
        gemini_json_path = os.path.join(os.path.dirname(upscaled_path), f"{filename}_gemini_reorder.json")

        clean_for_llm.process_cleaning(ocr_json_path, cleaned_txt_path)

        gemini_just_reorder.process_gemini_reorder(cleaned_txt_path, gemini_json_path, idx)  # idx가 슬라이드 번호

if __name__ == "__main__":
    main()