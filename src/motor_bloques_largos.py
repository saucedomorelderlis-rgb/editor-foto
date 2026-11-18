import json
import zipfile
from pathlib import Path
from datetime import datetime
from config_rutas import VIDEO_OUT_DIR

# Sub-parte 18.1: Division automatica en bloques de 10 minutos (600 segundos)
class GestorBloquesLargos:
    def dividir_en_bloques_10min(self, lista_escenas, max_segundos_bloque=600.0):
        bloques = []
        bloque_actual = []
        tiempo_acumulado = 0.0

        for esc in lista_escenas:
            palabras = len(str(esc.get("texto_es", "")).split())
            duracion_est = max(3.5, (palabras / 140.0) * 60.0)

            if bloque_actual and (tiempo_acumulado + duracion_est) > max_segundos_bloque:
                bloques.append(bloque_actual)
                bloque_actual = [esc]
                tiempo_acumulado = duracion_est
            else:
                bloque_actual.append(esc)
                tiempo_acumulado += duracion_est

        if bloque_actual:
            bloques.append(bloque_actual)
        return bloques

    # Sub-parte 18.2: Empaquetado final de todos los bloques y subtitulos en un unico ZIP
    def empaquetar_produccion_zip(self, nombre_proyecto, lista_videos_mp4, lista_srts, ruta_guion_pdf=None):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        seguro = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in nombre_proyecto.strip())
        zip_path = VIDEO_OUT_DIR / f"{seguro}_COMPLETO_{ts}.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for idx, mp4 in enumerate(lista_videos_mp4, start=1):
                p_mp4 = Path(mp4)
                if p_mp4.exists():
                    zf.write(p_mp4, arcname=f"Bloque_{idx:02d}_{p_mp4.name}")
            for idx, srt in enumerate(lista_srts, start=1):
                p_srt = Path(srt)
                if p_srt.exists():
                    zf.write(p_srt, arcname=f"Bloque_{idx:02d}_{p_srt.name}")
            if ruta_guion_pdf and Path(ruta_guion_pdf).exists():
                zf.write(ruta_guion_pdf, arcname=Path(ruta_guion_pdf).name)

        return str(zip_path)
