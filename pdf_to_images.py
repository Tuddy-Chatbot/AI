from pdf2image import convert_from_path
from datetime import datetime
import os
from PIL import Image

def pdf_to_images(pdf_path: str, root_output_dir: str = "slide_images", dpi: int = 300):
    """
    PDF 파일을 슬라이드 단위로 이미지로 변환하고, 날짜+시간 기반 폴더 및 이름으로 저장.
    반환: 이미지 파일 경로 리스트
    """
    # 타임스탬프 추출
    timestamp = datetime.now().strftime("%y%m%d-%H%M")
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_dir = os.path.join(root_output_dir, f"{timestamp}")

    os.makedirs(output_dir, exist_ok=True)

    # PDF → 이미지 변환
    images = convert_from_path(pdf_path, dpi=dpi)

    saved_paths = []
    for idx, img in enumerate(images, start=1):
        slide_filename = f"{timestamp}-{pdf_name}-{idx:02d}.png"
        slide_path = os.path.join(output_dir, slide_filename)
        img.save(slide_path, "PNG")
        saved_paths.append(slide_path)
        print(f"[SAVED] {slide_path}")

    return saved_paths
