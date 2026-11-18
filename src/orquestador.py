import json
from cerebro_gemini import CerebroGemini
from gestor_voces import GestorVoces
from motor_imagen import MotorImagenCoherente
from motor_video import EditorVideoStudio
from config_rutas import HISTORIAL_PROYECTO_PATH

class OrquestadorEstudio:
    def __init__(self):
        self.gemini = CerebroGemini()
        self.voces = GestorVoces()
        self.imagen = MotorImagenCoherente()
        self.video = EditorVideoStudio()

    def crear_guion(self, api_key, idea, num_escenas, estilo):
        datos = self.gemini.orquestar_historia(api_key, idea, num_escenas, estilo)
        return datos

    def producir_historia_completa(self, guion_dict, fuerza_coherencia=0.65, pasos=20, semilla_base=777, idioma_audio="es", modo_subs="Ambos (ES + EN)", zoom=True):
        biblia = guion_dict.get("biblia_visual", "")
        escenas = guion_dict.get("escenas", [])
        imagen_anterior = None
        resultado_escenas = []

        for idx, esc in enumerate(escenas):
            prompt_coherente = f"{biblia}, {esc['prompt_imagen']}"
            ruta_img = self.imagen.generar_cuadro(
                prompt_completo=prompt_coherente,
                ruta_imagen_anterior=imagen_anterior,
                fuerza_cambio=fuerza_coherencia,
                pasos=pasos,
                semilla=int(semilla_base) + idx
            )
            imagen_anterior = ruta_img

            pers = esc.get("personaje", "Narrador")
            aud_es, txt_es = self.voces.hablar_dialogo(pers, esc["texto_es"], idioma="es", tag=f"esc{idx+1}")
            aud_en, txt_en = self.voces.hablar_dialogo(pers, esc["texto_en"], idioma="en", tag=f"esc{idx+1}")

            resultado_escenas.append({
                "escena": idx + 1,
                "personaje": pers,
                "imagen": ruta_img,
                "audio_es": aud_es,
                "audio_en": aud_en,
                "texto_es": txt_es,
                "texto_en": txt_en
            })

        HISTORIAL_PROYECTO_PATH.write_text(json.dumps(resultado_escenas, indent=2, ensure_ascii=False), encoding="utf-8")
        mp4, srt = self.video.compilar_pelicula(resultado_escenas, idioma_audio, modo_subs, zoom)
        return mp4, srt, resultado_escenas

    def reexportar_edicion(self, idioma_audio, modo_subs, zoom, pausa):
        if not HISTORIAL_PROYECTO_PATH.exists():
            return None, None, "Primero produce una historia en la Pestana 1."
        escenas = json.loads(HISTORIAL_PROYECTO_PATH.read_text(encoding="utf-8"))
        mp4, srt = self.video.compilar_pelicula(escenas, idioma_audio, modo_subs, zoom, pausa)
        return mp4, srt, f"Video re-exportado en audio '{idioma_audio.upper()}' con subtitulos '{modo_subs}'."
