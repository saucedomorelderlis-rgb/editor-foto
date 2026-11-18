import json
from datetime import datetime
from pathlib import Path
from config_rutas import PROYECTOS_DIR

class GestorArchivosProyecto:
    def _ruta_segura(self, nombre_archivo):
        limpio = Path(nombre_archivo).name
        if not limpio:
            limpio = f"nota_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        return (PROYECTOS_DIR / limpio).resolve()

    def listar_archivos(self):
        return [f.name for f in PROYECTOS_DIR.iterdir() if f.is_file()]

    def leer_archivo(self, nombre_archivo):
        ruta = self._ruta_segura(nombre_archivo)
        if not ruta.exists():
            return f"El archivo '{ruta.name}' no existe en proyectos."
        return ruta.read_text(encoding="utf-8")

    def escribir_archivo(self, nombre_archivo, contenido, modo="sobrescribir"):
        ruta = self._ruta_segura(nombre_archivo)
        if modo == "anexar" and ruta.exists():
            anterior = ruta.read_text(encoding="utf-8")
            contenido = f"{anterior}\n\n{contenido}"
        ruta.write_text(str(contenido), encoding="utf-8")
        return f"Archivo '{ruta.name}' guardado correctamente en proyectos."

    # Sub-parte 3.2: Guardado JSON estructurado y respaldos versionados
    def guardar_json(self, nombre_archivo, diccionario):
        ruta = self._ruta_segura(nombre_archivo)
        ruta.write_text(json.dumps(diccionario, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(ruta)

    def leer_json(self, nombre_archivo, defecto=None):
        ruta = self._ruta_segura(nombre_archivo)
        if not ruta.exists():
            return defecto if defecto is not None else {}
        try:
            return json.loads(ruta.read_text(encoding="utf-8"))
        except Exception:
            return defecto if defecto is not None else {}

    def crear_respaldo_versionado(self, nombre_archivo):
        ruta = self._ruta_segura(nombre_archivo)
        if not ruta.exists():
            return ""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        copia = PROYECTOS_DIR / f"{ruta.stem}_v{ts}{ruta.suffix}"
        copia.write_text(ruta.read_text(encoding="utf-8"), encoding="utf-8")
        return str(copia)
