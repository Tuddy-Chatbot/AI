import os
import shutil
import subprocess

SUPPORTED_PPT_EXTS = {".ppt", ".pptx"}

class PPT2PDFError(Exception):
    pass

def _has_soffice() -> bool:
    return shutil.which("soffice") is not None

def ensure_pdf(input_path: str, session_dir: str) -> str:
    ext = os.path.splitext(input_path)[1].lower()
    if ext == ".pdf":
        return input_path
    if ext not in SUPPORTED_PPT_EXTS:
        raise PPT2PDFError(f"Unsupported file type for PPT->PDF: {ext}")
    if not _has_soffice():
        raise PPT2PDFError("LibreOffice(soffice) not found. Install libreoffice.")

    os.makedirs(session_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(input_path))[0]
    out_pdf = os.path.join(session_dir, f"{base}.pdf")
    
    # LO 사용자 프로필 경로를 명시적으로 지정 (HOME 기반)
    home = os.environ.get("HOME", "/tmp")
    lo_profile = os.path.join(home, ".config", "libreoffice", "4")
    os.makedirs(lo_profile, exist_ok=True)

    cmd = [
        "soffice",
        "--headless",
        "--nologo",
        "--nofirststartwizard",
        "--nodefault",                 
        "--nolockcheck",               
        "--norestore",                
        "-env:JavaDisabled=true",      
        f"-env:UserInstallation=file://{lo_profile}",  
        "--convert-to", "pdf:impress_pdf_Export",
        "--outdir", session_dir,
        input_path,
    ]
    
    # 환경 변수로 캐시/런타임 디렉토리도 안전한 곳으로
    env = os.environ.copy()
    env.setdefault("XDG_CACHE_HOME", os.path.join(home, ".cache"))
    env.setdefault("XDG_RUNTIME_DIR", os.path.join(home, ".run"))
    os.makedirs(env["XDG_CACHE_HOME"], exist_ok=True)
    os.makedirs(env["XDG_RUNTIME_DIR"], exist_ok=True)
    
    res = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    if res.returncode != 0:
        raise PPT2PDFError(
            f"PPT->PDF conversion failed (code {res.returncode}). "
            f"STDOUT: {res.stdout}\nSTDERR: {res.stderr}"
        )

    # 기대 파일명 규칙이 성립하는지 최종 확인
    if not os.path.exists(out_pdf):
        raise PPT2PDFError(
            "Conversion succeeded but expected PDF not found: "
            f"{out_pdf}\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}"
        )
    return out_pdf