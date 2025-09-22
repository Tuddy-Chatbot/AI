import os, requests, json, re
import base64
from typing import Optional, List, Dict
from utils.env_utils import GEMINI_KEY

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

def build_prompt(text: str) -> str:
    return f"""
아래는 OCR로 추출한 강의 텍스트입니다. 문장 순서가 섞여 있고, 일부는 보충 설명이나 필기입니다.

{text}

당신의 작업은 다음과 같습니다:

1. 문장을 논리적인 흐름에 맞게 자연스럽게 재정렬하세요.
2. 각 문단은 하나의 개념 또는 주제를 담도록 구성하고, 줄바꿈이나 번호, 리스트 기호(- 등)를 사용해 구분하세요.
3. 불필요한 기호(예: '*')는 제거하고, 문맥에 맞게 문장을 정돈하세요.
4. 한글과 영어가 혼용되어 있다면, 가독성을 위해 **가능한 한 한글로 통일**하고 영어 용어는 괄호로 보완하세요. 
5. 문장이 중복되거나 불완전할 경우, 자연스러운 흐름으로 정리해도 됩니다.
6. 재정렬된 텍스트의 내용을 대표할 수 있는 **슬라이드 제목**을 하나 생성하세요.

출력 형식:
제목: [여기에 생성한 제목 입력]
본문: [재정렬된 본문]
"""

def call_gemini(prompt: str, images: Optional[List[Dict]] = None) -> str:
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_KEY}
    
    parts = [{"text": prompt}]
    if images:
        for image_data in images:
            image_bytes = image_data.get("data")
            mime_type = image_data.get("mime_type")
            
            if image_bytes and mime_type:
                encoded_image = base64.b64encode(image_bytes).decode('utf-8')
                parts.append({
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": encoded_image
                    }
                })
        
    data = {"contents":[{"parts": parts}]}
    
    resp = requests.post(API_URL, headers=headers, params=params, json=data)
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]

def process_gemini_reorder(cleaned_txt_path: str, slide_number: int) -> str:
    with open(cleaned_txt_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    prompt = build_prompt(text)
    result = call_gemini(prompt)
    result = result.replace("\n", " ")

    title_match = re.search(r"제목:\s*(.+?)\s*본문:", result)
    body_match = re.search(r"본문:\s*(.+)", result)
    if not title_match or not body_match:
        raise ValueError("Gemini 응답에서 제목/본문 파싱 실패")

    output_json = [{
        "slide_number": slide_number,
        "title": title_match.group(1).strip(),
        "text": body_match.group(1).strip()
    }]

    output_path = cleaned_txt_path.replace("_cleaned.txt", "_gemini_reorder.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_json, f, ensure_ascii=False, indent=2)

    print(f"[GEMINI] {output_path}")
    return output_path
