import os
import json
from typing import List
from langchain_core.documents import Document

def load_slide_documents_from_folder(base_dir: str, date_folder: str) -> List[Document]:
    target_dir = os.path.join(base_dir, date_folder)
    if not os.path.isdir(target_dir):
        raise FileNotFoundError(f"지정된 폴더가 존재하지 않습니다: {target_dir}")

    documents = []
    json_files = [f for f in os.listdir(target_dir) if f.endswith("_gemini_reorder.json")]

    for fname in json_files:
        full_path = os.path.join(target_dir, fname)
        with open(full_path, "r", encoding="utf-8") as f:
            slide_data = json.load(f)
            for slide in slide_data:
                slide_number = slide.get("slide_number", None)
                title = slide.get("title", "")
                text = slide.get("text", "")
                text_single_line = " ".join(line.strip() for line in text.splitlines())
                content = f"[슬라이드 {slide_number}] {title}\n{text_single_line}"

                documents.append(Document(
                    page_content=content,
                    metadata={
                        "slide_number": slide_number,
                        "file": fname
                    }
                ))

    print(f"총 {len(documents)}개의 슬라이드 문서 로드 완료")
    return documents