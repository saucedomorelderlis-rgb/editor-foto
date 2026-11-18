import re
import shutil
from pathlib import Path
from gestor_voces import GestorVoces, VOCES_DISPONIBLES
from config_rutas import VOCES_PROPIAS_DIR

class MotorCastingYVozPropia:
    def __init__(self):
        self.gestor = GestorVoces()

    def registrar_voz_usuario(self, personaje, voz_es, voz_en, velocidad=0, tono=0, volumen=0, archivo_voz_propia=None, motor_preferido="Auto"):
        nombre = personaje.strip()
        if not nombre:
            return "Error: Debes escribir el nombre del personaje."

        ruta_muestra = ""
        if archivo_voz_propia:
            src = Path(archivo_voz_propia)
            if src.exists():
                seguro = re.sub(r"[^a-zA-Z0-9_-]", "_", nombre)
                destino = VOCES_PROPIAS_DIR / f"muestra_{seguro}{src.suffix}"
                shutil.copy2(src, destino)
                ruta_muestra = str(destino)

        self.gestor.perfiles[nombre] = {
            "voz_es": voz_es,
            "voz_en": voz_en,
            "rate": f"{int(velocidad):+d}%",
            "pitch": f"{int(tono):+d}Hz",
            "volume": f"{int(volumen):+d}%",
            "motor": motor_preferido,
            "voz_propia_muestra": ruta_muestra,
            "asignada_por": "Manual Usuario"
        }
        self.gestor.guardar_disco()
        aviso = f" + Muestra de voz propia guardada ({Path(ruta_muestra).name})" if ruta_muestra else ""
        return f"Personaje '{nombre}' guardado y afinado{aviso}."

    def obtener_o_asignar_automatico(self, personaje, genero_ia="M", tono_ia=0, velocidad_ia=0):
        nombre = personaje.strip()
        if nombre in self.gestor.perfiles:
            return self.gestor.perfiles[nombre]

        # Auto-casting inteligente: evita repetir voces ya asignadas a otros personajes
        usadas_es = {p.get("voz_es") for p in self.gestor.perfiles.values()}
        usadas_en = {p.get("voz_en") for p in self.gestor.perfiles.values()}

        cand_es = [k for k, v in VOCES_DISPONIBLES.items() if v["idioma"] == "es" and v["genero"] == genero_ia]
        cand_en = [k for k, v in VOCES_DISPONIBLES.items() if v["idioma"] == "en" and v["genero"] == genero_ia]

        libres_es = [k for k in cand_es if k not in usadas_es] or cand_es
        libres_en = [k for k in cand_en if k not in usadas_en] or cand_en

        idx = len(self.gestor.perfiles)
        perfil_auto = {
            "voz_es": libres_es[idx % len(libres_es)],
            "voz_en": libres_en[idx % len(libres_en)],
            "rate": f"{int(velocidad_ia):+d}%",
            "pitch": f"{int(tono_ia):+d}Hz",
            "volume": "+0%",
            "motor": "Auto",
            "voz_propia_muestra": "",
            "asignada_por": "Auto-Casting IA"
        }
        self.gestor.perfiles[nombre] = perfil_auto
        self.gestor.guardar_disco()
        return perfil_auto

    def generar_voz_personaje(self, personaje, dialogo, idioma="es", tag="esc", genero_ia="M", tono_ia=0):
        perfil = self.obtener_o_asignar_automatico(personaje, genero_ia=genero_ia, tono_ia=tono_ia)
        return self.gestor.sintetizar_con_perfil(personaje, dialogo, perfil, idioma=idioma, tag=tag)
