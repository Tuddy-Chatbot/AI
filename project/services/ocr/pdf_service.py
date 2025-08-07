from pdf2image import convert_from_path
from datetime import datetime
import os

def pdf_to_images(pdf_path: str, output_dir: str, dpi: int = 300):
    """
    PDF 파일을 이미지로 변환하고 output_dir에 저장
    """
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    images = convert_from_path(pdf_path, dpi=dpi)

    saved_paths = []
    for idx, img in enumerate(images, start=1):
        slide_filename = f"{pdf_name}-{idx:02d}.png"
        slide_path = os.path.join(output_dir, slide_filename)
        img.save(slide_path, "PNG")
        saved_paths.append(slide_path)
        print(f"[SAVED] {slide_path}")

    return saved_paths