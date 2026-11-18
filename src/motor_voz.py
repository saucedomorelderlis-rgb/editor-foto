import sys
import time
from datetime import datetime
import torch
import soundfile as sf
from config_rutas import CHATTTS_DIR, AUDIO_OUT_DIR, DEVICE

# Agregar ChatTTS-main al path de Python sin importar el SO
if CHATTTS_DIR.exists() and str(CHATTTS_DIR) not in sys.path:
    sys.path.insert(0, str(CHATTTS_DIR))

class MotorVozChatTTS:
    def __init__(self):
        self.chat = None

    def cargar_modelo(self):
        if self.chat is None:
            print("[ChatTTS] Inicializando motor de voz...")
            import ChatTTS
            self.chat = ChatTTS.Chat()
            self.chat.load(compile=False)

    def generar(self, texto, velocidad=5, semilla=42):
        self.cargar_modelo()
        inicio = time.time()

        torch.manual_seed(int(semilla))
        rand_spk = self.chat.sample_random_speaker()

        params_infer = {
            "spk_emb": rand_spk,
            "temperature": 0.3,
            "top_P": 0.7,
            "top_K": 20,
            "prompt": f"[speed_{int(velocidad)}]"
        }

        wavs = self.chat.infer([texto], params_infer_code=params_infer)
        audio_data = wavs[0]
        if len(audio_data.shape) > 1:
            audio_data = audio_data.squeeze()

        nombre_archivo = f"voz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        ruta_salida = AUDIO_OUT_DIR / nombre_archivo
        sf.write(str(ruta_salida), audio_data, 24000)

        tiempo = round(time.time() - inicio, 2)
        print(f"[ChatTTS] Audio guardado en {ruta_salida} ({tiempo}s)")
        return str(ruta_salida), f"Audio generado en {tiempo}s"
