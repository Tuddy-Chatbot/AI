from google.cloud import vision
from google.oauth2 import service_account
import os, json
from PIL import Image
from utils.env_utils import GOOGLE_KEY

# Vision API 클라이언트 설정
credentials = service_account.Credentials.from_service_account_file(GOOGLE_KEY)
client = vision.ImageAnnotatorClient(credentials=credentials)

def upscale_image(input_path, scale_factor=1.5):
    img = Image.open(input_path)
    new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
    resized_img = img.resize(new_size, Image.LANCZOS)

    upscaled_path = input_path.replace(".png", f"_upscaled_{int(scale_factor*100)}.png")
    resized_img.save(upscaled_path)
    print(f"[INFO] 이미지 확대 저장: {upscaled_path}")
    return upscaled_path

def run_document_text_detection(image_path: str) -> str:
    with open(image_path, "rb") as f:
        content = f.read()
    image = vision.Image(content=content)
    response = client.document_text_detection(image=image)

    full_text_annotation = response.full_text_annotation
    full_text_blocks = []
    printed_blocks = []
    handwritten_blocks = []

    threshold = 0.75
    for page in full_text_annotation.pages:
        for block in page.blocks:
            block_text = "".join(
                symbol.text
                for paragraph in block.paragraphs
                for word in paragraph.words
                for symbol in word.symbols
            ).strip()

            bbox = [{"x": v.x or 0, "y": v.y or 0} for v in block.bounding_box.vertices]
            block_info = {
                "text": block_text,
                "confidence": round(block.confidence, 3),
                "bounding_poly": bbox,
            }

            full_text_blocks.append(block_info)
            (printed_blocks if block.confidence >= threshold else handwritten_blocks).append(block_info)

    # JSON 저장
    filename = os.path.splitext(os.path.basename(image_path))[0]
    output_path = os.path.join(os.path.dirname(image_path), f"{filename}_ocr_result.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "full_text": full_text_annotation.text,
            "full_text_blocks": full_text_blocks,
            "printed_blocks": printed_blocks,
            "handwritten_blocks": handwritten_blocks,
        }, f, indent=2, ensure_ascii=False)

    print(f"[OCR] JSON 저장: {output_path}")
    return output_path
