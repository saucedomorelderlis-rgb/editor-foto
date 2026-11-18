import re
import shutil
from pathlib import Path
from config_rutas import DRIVE_PROYECTOS_DIR

# Sub-parte 23.1: Guardado automatico inmediato en Google Drive por cada bloque terminado
class SincronizadorGoogleDrive:
    def obtener_carpeta_proyecto(self, nombre_proyecto):
        limpio = re.sub(r"[^a-zA-Z0-9_-]", "_", nombre_proyecto.strip() or "Proyecto_Sin_Nombre")
        carpeta = DRIVE_PROYECTOS_DIR / limpio
        for sub in ["bloques_video", "imagenes", "audios", "checkpoints"]:
            (carpeta / sub).mkdir(parents=True, exist_ok=True)
        return carpeta

    def respaldar_bloque_inmediato(self, nombre_proyecto, numero_bloque, ruta_mp4, ruta_srt, escenas_bloque):
        carpeta_proj = self.obtener_carpeta_proyecto(nombre_proyecto)

        # 1. Guardar inmediatamente el video MP4 y subtitulos SRT del bloque de 10 min
        for archivo in [ruta_mp4, ruta_srt]:
            if archivo and Path(archivo).exists():
                src = Path(archivo)
                dst = carpeta_proj / "bloques_video" / f"Bloque_{numero_bloque:02d}_{src.name}"
                shutil.copy2(src, dst)

        # 2. Respaldar imagenes y audios individuales de ese bloque
        for esc in escenas_bloque:
            for clave_img in ["imagen"]:
                p = Path(str(esc.get(clave_img, "")))
                if p.exists():
                    shutil.copy2(p, carpeta_proj / "imagenes" / p.name)
            for clave_aud in ["audio_es", "audio_en"]:
                p = Path(str(esc.get(clave_aud, "")))
                if p.exists():
                    shutil.copy2(p, carpeta_proj / "audios" / p.name)

        return str(carpeta_proj / "bloques_video")

    def respaldar_archivo_final(self, nombre_proyecto, ruta_archivo):
        carpeta_proj = self.obtener_carpeta_proyecto(nombre_proyecto)
        src = Path(str(ruta_archivo))
        if src.exists():
            dst = carpeta_proj / src.name
            shutil.copy2(src, dst)
            return str(dst)
        return ""
