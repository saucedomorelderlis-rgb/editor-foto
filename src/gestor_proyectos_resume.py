import json
from pathlib import Path
from sincronizador_drive import SincronizadorGoogleDrive
from config_rutas import DRIVE_PROYECTOS_DIR

# Sub-parte 24.1: Puntos de control por nombre de proyecto y recuperacion ante cortes en Colab
class GestorProyectosResume:
    def __init__(self):
        self.drive_sync = SincronizadorGoogleDrive()

    def listar_proyectos_guardados(self):
        if not DRIVE_PROYECTOS_DIR.exists():
            return []
        return sorted([d.name for d in DRIVE_PROYECTOS_DIR.iterdir() if d.is_dir()])

    def ruta_checkpoint(self, nombre_proyecto):
        carpeta = self.drive_sync.obtener_carpeta_proyecto(nombre_proyecto)
        return carpeta / "checkpoints" / "estado_proyecto.json"

    def cargar_estado_proyecto(self, nombre_proyecto):
        ckpt = self.ruta_checkpoint(nombre_proyecto)
        if ckpt.exists():
            try:
                return json.loads(ckpt.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "nombre_proyecto": nombre_proyecto,
            "plan_director": {},
            "escenas_completadas": {},
            "bloques_renderizados": [],
            "srts_renderizados": [],
            "ultimo_fotograma": "",
            "finalizado": False
        }

    def guardar_progreso_escena(self, nombre_proyecto, estado_dict, indice_escena, datos_escena, ruta_img_actual):
        estado_dict["escenas_completadas"][str(indice_escena)] = datos_escena
        estado_dict["ultimo_fotograma"] = str(ruta_img_actual)
        ckpt = self.ruta_checkpoint(nombre_proyecto)
        ckpt.write_text(json.dumps(estado_dict, indent=2, ensure_ascii=False), encoding="utf-8")

    def registrar_bloque_terminado(self, nombre_proyecto, estado_dict, numero_bloque, ruta_mp4, ruta_srt, escenas_bloque):
        self.drive_sync.respaldar_bloque_inmediato(nombre_proyecto, numero_bloque, ruta_mp4, ruta_srt, escenas_bloque)
        if ruta_mp4 not in estado_dict["bloques_renderizados"]:
            estado_dict["bloques_renderizados"].append(ruta_mp4)
        if ruta_srt not in estado_dict["srts_renderizados"]:
            estado_dict["srts_renderizados"].append(ruta_srt)
        ckpt = self.ruta_checkpoint(nombre_proyecto)
        ckpt.write_text(json.dumps(estado_dict, indent=2, ensure_ascii=False), encoding="utf-8")
