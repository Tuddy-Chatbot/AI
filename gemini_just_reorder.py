import os
import requests
import json
import re
from dotenv import load_dotenv

load_dotenv()

# Gemini API 설정
API_KEY = os.getenv('API_KEY')
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# 입력 및 출력 파일 경로
INPUT_FILE = "cleaned_full_text_for_llm.txt"
OUTPUT_FILE = "reordered_text.json"

def call_gemini_api(prompt: str) -> str:
    headers = {"Content-Type": "application/json"}
    params = {"key": API_KEY}
    data = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    response = requests.post(API_URL, headers=headers, params=params, json=data)
    if response.status_code != 200:
        raise Exception(f"[Gemini API 오류] {response.status_code}: {response.text}")

    candidates = response.json().get("candidates", [])
    if not candidates:
        raise Exception("Gemini 응답에서 텍스트를 찾을 수 없습니다.")
    
    return candidates[0]["content"]["parts"][0]["text"]


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

def parse_single_chunk(text: str, slide_number: int) -> list:
    # 제목과 본문을 정확히 분리
    title_match = re.search(r"제목:\s*(.+?)\s*본문:", text, re.DOTALL)
    body_match = re.search(r"본문:\s*(.+)", text, re.DOTALL)

    if not title_match or not body_match:
        raise Exception("Gemini 응답에서 '제목' 또는 '본문'을 정확히 찾을 수 없습니다.")

    title = title_match.group(1).strip()
    body = body_match.group(1).strip()

    chunk_obj = {
        "slide_number": slide_number,
        "title": title,
        "text": body
    }
    return [chunk_obj]

def process_gemini_reorder(input_txt_path: str, output_json_path: str, slide_number: int):
    print(f"[INFO] Gemini 재정렬 시작: {input_txt_path} (슬라이드 번호: {slide_number})")
    try:
        with open(input_txt_path, "r", encoding="utf-8") as f:
            input_text = f.read().strip()

        prompt = build_prompt(input_text)
        result = call_gemini_api(prompt)
        result = result.replace("\n", " ")

        chunked_output = parse_single_chunk(result, slide_number)

        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(chunked_output, f, ensure_ascii=False, indent=2)

        print(f"[✔] 결과 저장 완료: '{output_json_path}'")
    except Exception as e:
        print(f"[ERROR] Gemini 재정렬 실패: {e}")
