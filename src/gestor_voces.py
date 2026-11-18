import json
import re
import asyncio
from datetime import datetime
import edge_tts
from config_rutas import PERFILES_VOCES_PATH, AUDIO_OUT_DIR

VOCES_DISPONIBLES = {
    "ES (Espana) - Alvaro (Hombre Natural)": {"id": "es-ES-AlvaroNeural", "genero": "M", "idioma": "es", "desc": "Voz masculina castellana clara y equilibrada."},
    "ES (Espana) - Elvira (Mujer Expresiva)": {"id": "es-ES-ElviraNeural", "genero": "F", "idioma": "es", "desc": "Voz femenina castellana expresiva y dinamica."},
    "ES (Mexico) - Jorge (Hombre Profundo)": {"id": "es-MX-JorgeNeural", "genero": "M", "idioma": "es", "desc": "Voz masculina grave y seria, ideal para narradores."},
    "ES (Mexico) - Dalia (Mujer Calida)": {"id": "es-MX-DaliaNeural", "genero": "F", "idioma": "es", "desc": "Voz femenina calida, cercana y natural."},
    "ES (Argentina) - Tomas (Hombre Narrador)": {"id": "es-AR-TomasNeural", "genero": "M", "idioma": "es", "desc": "Voz masculina rioplatense firme y dramatica."},
    "ES (Argentina) - Elena (Mujer Suave)": {"id": "es-AR-ElenaNeural", "genero": "F", "idioma": "es", "desc": "Voz femenina suave y emotiva."},
    "ES (Colombia) - Gonzalo (Hombre Serio)": {"id": "es-CO-GonzaloNeural", "genero": "M", "idioma": "es", "desc": "Voz masculina neutra, limpia y autoritaria."},
    "ES (Colombia) - Salome (Mujer Clara)": {"id": "es-CO-SalomeNeural", "genero": "F", "idioma": "es", "desc": "Voz femenina articulada y juvenil."},
    "EN (US) - Andrew (Hombre Natural)": {"id": "en-US-AndrewNeural", "genero": "M", "idioma": "en", "desc": "Voz masculina estadounidense muy natural y conversacional."},
    "EN (US) - Ava (Mujer Expresiva)": {"id": "en-US-AvaNeural", "genero": "F", "idioma": "en", "desc": "Voz femenina estadounidense expresiva y cinematografica."},
    "EN (US) - Brian (Hombre Profundo)": {"id": "en-US-BrianNeural", "genero": "M", "idioma": "en", "desc": "Voz masculina profunda de documental o trailer."},
    "EN (US) - Emma (Mujer Clara)": {"id": "en-US-EmmaNeural", "genero": "F", "idioma": "en", "desc": "Voz femenina limpia y profesional."},
    "EN (US) - Christopher (Hombre Epico)": {"id": "en-US-ChristopherNeural", "genero": "M", "idioma": "en", "desc": "Voz masculina resonante para historias epicas."},
    "EN (US) - Jenny (Mujer Dinamica)": {"id": "en-US-JennyNeural", "genero": "F", "idioma": "en", "desc": "Voz femenina energica y versatil."},
    "EN (UK) - Ryan (Hombre Britanico)": {"id": "en-GB-RyanNeural", "genero": "M", "idioma": "en", "desc": "Voz masculina britanica elegante."},
    "EN (UK) - Sonia (Mujer Britanica)": {"id": "en-GB-SoniaNeural", "genero": "F", "idioma": "en", "desc": "Voz femenina britanica sofisticada."}
}

class GestorVoces:
    def __init__(self):
        self.perfiles = self._cargar()

    def _cargar(self):
        if PERFILES_VOCES_PATH.exists():
            try:
                return json.loads(PERFILES_VOCES_PATH.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def guardar_disco(self):
        PERFILES_VOCES_PATH.write_text(json.dumps(self.perfiles, indent=2, ensure_ascii=False), encoding="utf-8")

    # Sub-parte 4.2: Limpieza estricta de prefijos y sintesis neural afinada
    def limpiar_nombre_personaje(self, personaje, texto):
        patron = rf"^\s*[\[\(]?{re.escape(personaje.strip())}[\]\)]?\s*[:\-]\s*"
        limpio = re.sub(patron, "", str(texto).strip(), flags=re.IGNORECASE)
        return re.sub(r"^\s*[A-ZÁÉÍÓÚÑ0-9_ ]{2,25}:\s*", "", limpio)

    async def _sintetizar_edge_async(self, texto, voice_id, rate, pitch, volume, salida):
        comm = edge_tts.Communicate(text=texto, voice=voice_id, rate=rate, pitch=pitch, volume=volume)
        await comm.save(str(salida))

    def sintetizar_con_perfil(self, personaje, texto, perfil, idioma="es", tag="esc"):
        texto_limpio = self.limpiar_nombre_personaje(personaje, texto)
        clave_voz = perfil.get("voz_es") if idioma == "es" else perfil.get("voz_en")
        info_voz = VOCES_DISPONIBLES.get(clave_voz) or VOCES_DISPONIBLES["ES (Mexico) - Jorge (Hombre Profundo)"]
        ruta = AUDIO_OUT_DIR / f"{tag}_{idioma}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.mp3"

        asyncio.run(self._sintetizar_edge_async(
            texto_limpio,
            info_voz["id"],
            perfil.get("rate", "+0%"),
            perfil.get("pitch", "+0Hz"),
            perfil.get("volume", "+0%"),
            ruta
        ))
        return str(ruta), texto_limpio
