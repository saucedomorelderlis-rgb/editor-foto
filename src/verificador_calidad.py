from pathlib import Path
from PIL import Image
import numpy as np
from moviepy import AudioFileClip

# Sub-parte 20.1: Auditoria automatica de fotogramas, pistas de audio y bloques
class VerificadorCalidadTotal:
    def verificar_imagen(self, ruta_img):
        p = Path(str(ruta_img))
        if not p.exists() or p.stat().st_size < 2048:
            return False, "Archivo de imagen inexistente o demasiado pequeno."
        try:
            with Image.open(p) as im:
                arr = np.array(im.convert("RGB"), dtype=np.float32)
                brillo_medio = float(np.mean(arr))
                varianza = float(np.std(arr))
                if brillo_medio < 3.0 or varianza < 2.0:
                    return False, "Imagen detectada en negro o sin detalle visual."
            return True, "Imagen aprobada."
        except Exception as e:
            return False, f"Error leyendo imagen: {e}"

    def verificar_audio(self, ruta_audio):
        p = Path(str(ruta_audio))
        if not p.exists() or p.stat().st_size < 1024:
            return False, 0.0, "Archivo de audio vacio o inexistente."
        try:
            clip = AudioFileClip(str(p))
            dur = float(clip.duration)
            clip.close()
            if dur <= 0.15:
                return False, dur, "Audio demasiado corto."
            return True, dur, "Audio aprobado."
        except Exception as e:
            return False, 0.0, f"Error leyendo audio: {e}"

    def auditar_escena_completa(self, escena_dict):
        ok_img, msg_img = self.verificar_imagen(escena_dict.get("imagen", ""))
        ok_es, dur_es, msg_es = self.verificar_audio(escena_dict.get("audio_es", ""))
        ok_en, dur_en, msg_en = self.verificar_audio(escena_dict.get("audio_en", ""))
        aprobado = ok_img and ok_es and ok_en
        detalle = f"Img: {msg_img} | ES ({dur_es:.1f}s): {msg_es} | EN ({dur_en:.1f}s): {msg_en}"
        return aprobado, detalle
