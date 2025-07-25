import json
import re
import os


def clean_for_llm(text: str) -> str:
    """
    LLM에 넘기기 전 특수문자 정제 함수
    - 알파벳, 한글, 숫자, 기본 구두점(.,?!) 및 의미 있는 기호만 유지
    - 장식용, 노이즈성 특수문자 전부 제거
    """
    # 장식용 문자 제거 (필요시 추가)
    text = re.sub(r"[■●◆★☆▶◀⚫]", "", text)

    # 허용 문자 이외 모두 제거
    # 허용 문자: 한글, 영문, 숫자, 기본 구두점(.,?!), 괄호, 번호 기호, 리스트 기호 등
    text = re.sub(
        r"[^가-힣a-zA-Z0-9\s.,?!:;()\[\]\-]", "", text
    )

    # 중복된 줄바꿈, 공백 정리
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"[ ]{2,}", " ", text)

    return text.strip()


def load_full_text_from_ocr(json_path: str) -> str:
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"'{json_path}' 파일이 존재하지 않습니다.")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    full_text = data.get("full_text", "").strip()
    if not full_text:
        raise ValueError("OCR 결과에서 'full_text' 항목이 비어 있습니다.")

    return full_text

def process_cleaning(ocr_json_path: str, output_txt_path: str):
    """
    OCR 결과 JSON 파일 경로를 받아 LLM 전처리 텍스트 파일로 저장
    """
    try:
        raw_text = load_full_text_from_ocr(ocr_json_path)
        cleaned_text = clean_for_llm(raw_text)

        with open(output_txt_path, "w", encoding="utf-8") as f:
            f.write(cleaned_text)

        print(f"[✔] 전처리 완료: '{output_txt_path}'에 저장되었습니다.")
    except Exception as e:
        print(f"[오류] {e}")
