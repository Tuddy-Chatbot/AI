import json, os, re

def clean_for_llm(text: str) -> str:
    text = re.sub(r"[■●◆★☆▶◀⚫]", "", text)
    text = re.sub(r"[^가-힣a-zA-Z0-9\s.,?!:;()\[\]\-]", "", text)
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"[ ]{2,}", " ", text)
    return text.strip()

def process_cleaning(ocr_json_path: str) -> str:
    if not os.path.exists(ocr_json_path):
        raise FileNotFoundError(f"{ocr_json_path} 없음")

    with open(ocr_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_text = data.get("full_text", "").strip()
    cleaned_text = clean_for_llm(raw_text)

    output_txt_path = ocr_json_path.replace("_ocr_result.json", "_cleaned.txt")
    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write(cleaned_text)

    print(f"[CLEAN] {output_txt_path}")
    return output_txt_path
