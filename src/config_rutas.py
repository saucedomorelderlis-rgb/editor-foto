import os
import json
import platform
from pathlib import Path
import torch

BASE_DIR = Path(__file__).resolve().parent.parent if Path(__file__).parent.name == "src" else Path(__file__).resolve().parent

MODELS_DIR = BASE_DIR / "modelos"
KOKORO_DIR = MODELS_DIR / "kokoro"
PROYECTOS_DIR = BASE_DIR / "proyectos"
VOCES_PROPIAS_DIR = PROYECTOS_DIR / "voces_propias"
BIN_CPP_DIR = BASE_DIR / "bin_cpp"

OUTPUT_DIR = BASE_DIR / "resultados"
IMG_OUT_DIR = OUTPUT_DIR / "imagenes"
AUDIO_OUT_DIR = OUTPUT_DIR / "audios"
VIDEO_OUT_DIR = OUTPUT_DIR / "videos"
DOCS_OUT_DIR = OUTPUT_DIR / "documentos"

for carpeta in [MODELS_DIR, KOKORO_DIR, PROYECTOS_DIR, VOCES_PROPIAS_DIR, BIN_CPP_DIR, IMG_OUT_DIR, AUDIO_OUT_DIR, VIDEO_OUT_DIR, DOCS_OUT_DIR]:
    carpeta.mkdir(parents=True, exist_ok=True)

PERFILES_VOCES_PATH = PROYECTOS_DIR / "perfiles_voces.json"
HISTORIAL_PROYECTO_PATH = PROYECTOS_DIR / "ultima_historia.json"
CONFIG_APP_PATH = PROYECTOS_DIR / "config_estudio.json"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32

SDXL_BASE_PATH = BASE_DIR / "sd_xl_base_1.0.safetensors"
SDXL_LORA_PATH = BASE_DIR / "sd_xl_offset_example-lora_1.0.safetensors"
CHATTTS_DIR = MODELS_DIR / "ChatTTS-main"

DRIVE_MOUNT_DIR = Path("/content/drive/MyDrive")
DRIVE_PROYECTOS_DIR = DRIVE_MOUNT_DIR / "EstudioCineIA_Proyectos" if DRIVE_MOUNT_DIR.exists() else (PROYECTOS_DIR / "respaldo_local")

def cargar_config():
    defecto = {
        "gemini_api_key": "",
        "openai_api_key": "",
        "telegram_token": "",
        "telegram_chat_id": "",
        "proyecto_activo": "Proyecto_Principal"
    }
    if CONFIG_APP_PATH.exists():
        try:
            datos = json.loads(CONFIG_APP_PATH.read_text(encoding="utf-8"))
            defecto.update(datos)
        except Exception:
            pass
    return defecto

def guardar_config(gemini_key=None, openai_key=None, telegram_token=None, telegram_chat_id=None, proyecto_activo=None):
    cfg = cargar_config()
    if gemini_key is not None and gemini_key.strip():
        cfg["gemini_api_key"] = gemini_key.strip()
    if openai_key is not None:
        cfg["openai_api_key"] = openai_key.strip()
    if telegram_token is not None:
        cfg["telegram_token"] = telegram_token.strip()
    if telegram_chat_id is not None:
        cfg["telegram_chat_id"] = str(telegram_chat_id).strip()
    if proyecto_activo is not None and proyecto_activo.strip():
        cfg["proyecto_activo"] = proyecto_activo.strip()
    CONFIG_APP_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    return cfg

if __name__ == "__main__":
    print(f"[OK] SO: {platform.system()} | Dispositivo: {DEVICE.upper()} ({DTYPE})")
    print(f"[OK] Carpeta Base: {BASE_DIR}")
    print(f"[OK] SDXL Base: {SDXL_BASE_PATH.exists()} | LoRA: {SDXL_LORA_PATH.exists()}")
