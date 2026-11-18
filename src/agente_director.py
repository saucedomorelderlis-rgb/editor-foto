import json
from google import genai
from google.genai import types
from voz_interactiva import VozInteractivaAgente
from config_rutas import HISTORIAL_PROYECTO_PATH
import servidor_mcp as mcp_tools

class AgenteDirectorAutonomo:
    def __init__(self):
        self.voz_agente = VozInteractivaAgente()
        self.bitacora = []

    def log(self, texto):
        self.bitacora.append(texto)

    # Sub-parte 11.1: Clasificador autonomo de intenciones y control de archivos
    def procesar_interaccion(self, api_key, mensaje_usuario, pasos_sdxl=12, idioma_audio="es", modo_subs="Ambos (ES + EN)", guionista_chatgpt_fn=None, openai_key=""):
        client = genai.Client(api_key=api_key.strip(), http_options={"api_version": "v1beta"})

        sistema_clasificador = """
Eres un Agente de Inteligencia Artificial especializado en Creacion, Direccion y Edicion Profesional de Video conectado mediante protocolo MCP.
Comprendes perfectamente que tu proposito es crear videos coherentes, gestionar archivos de proyecto, dirigir voces y editar secuencias.
Analiza la orden del usuario y clasifica la accion:
- "producir_video": si solicita crear una historia, pelicula, guion nuevo o video.
- "re_editar": si solicita modificar el video actual (cambiar idioma a ingles o espanol, cambiar subtitulos o ritmo).
- "gestion_archivo": si pide crear, leer o modificar una nota o guion en archivos sin renderizar video aun.
- "conversar": si saluda, pide consejo de cine o consulta capacidades.

Devuelve SOLO JSON valido:
{
  "accion": "producir_video | re_editar | gestion_archivo | conversar",
  "respuesta_hablada": "Respuesta natural, cercana y profesional para hablarle al usuario",
  "archivo_accion": "crear | leer | listar | ninguno",
  "archivo_nombre": "nombre.txt",
  "archivo_contenido": "contenido si aplica"
}
"""
        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=mensaje_usuario,
            config=types.GenerateContentConfig(
                system_instruction=sistema_clasificador,
                response_mime_type="application/json",
                temperature=0.4
            )
        )
        decision = json.loads(res.text)
        accion = decision.get("accion", "conversar")
        resp_txt = decision.get("respuesta_hablada", "Entendido, me encargo de ello.")

        if decision.get("archivo_accion") in ("crear", "leer", "listar"):
            out_arch = mcp_tools.mcp_gestionar_archivo(
                decision["archivo_accion"],
                decision.get("archivo_nombre", "notas_director.txt"),
                decision.get("archivo_contenido", mensaje_usuario)
            )
            if decision["archivo_accion"] == "leer":
                resp_txt = f"Esto es lo que dice el archivo: {out_arch[:400]}"

        audio_resp = self.voz_agente.hablar_respuesta(resp_txt, idioma="es")

        if accion == "re_editar":
            lang = "en" if ("ingles" in mensaje_usuario.lower() or "english" in mensaje_usuario.lower()) else "es"
            ed = json.loads(mcp_tools.mcp_editar_y_renderizar_video(lang, modo_subs, True, 0.35))
            return resp_txt, audio_resp, "Video re-editado por orden directa al Agente.", "{}", [], ed.get("video_mp4"), ed.get("subtitulos_srt")

        elif accion == "producir_video":
            bitacora, plan, galeria, mp4, srt = self.producir_pelicula(
                api_key, mensaje_usuario, pasos_sdxl, idioma_audio, modo_subs, guionista_chatgpt_fn, openai_key
            )
            fin_txt = f"{resp_txt} La produccion ha terminado y el video ya esta listo."
            audio_fin = self.voz_agente.hablar_respuesta(fin_txt, idioma="es")
            return fin_txt, audio_fin, bitacora, plan, galeria, mp4, srt

        return resp_txt, audio_resp, "Agente Director MCP en escucha activa.", "{}", [], None, None

    # Sub-parte 11.2: Planificacion cinematografica, Biblia Visual y guionista opcional ChatGPT
    def producir_pelicula(self, api_key, instruccion, pasos_sdxl=15, idioma_audio="es", modo_subs="Ambos (ES + EN)", guionista_chatgpt_fn=None, openai_key=""):
        self.bitacora = []
        client = genai.Client(api_key=api_key.strip(), http_options={"api_version": "v1beta"})

        borrador_guion = instruccion
        if guionista_chatgpt_fn and openai_key and openai_key.strip():
            self.log("[Asistente ChatGPT Opcional] Redactando propuesta literaria del guion...")
            borrador_guion = guionista_chatgpt_fn(openai_key, instruccion)

        self.log("[Cerebro Gemini MCP] Estructurando Biblia Visual, casting ilimitado y plan de edicion...")

        prompt_director = """
Eres un Agente Autonomo Director de Cine y Editor de Video conectado por MCP.
Estructura la historia (sin limite de personajes ni escenas) tomando decisiones profesionales de ritmo y continuidad:
1. 'biblia_visual': Rasgos fisicos, ropa e iluminacion constantes para coherencia total cuadro a cuadro.
2. 'decisiones_edicion': 'fuerza_coherencia' (0.50 a 0.72), 'zoom_camara' (true/false), 'pausa_escenas' (0.25 a 0.65).
3. En 'texto_es' y 'texto_en' escribe SOLO lo que dice el personaje (NUNCA escribas el nombre del personaje).
4. Incluye 'tipo_plano' (ej. Wide shot, Medium shot, Close-up) en el prompt visual.

Devuelve SOLO JSON valido:
{
  "titulo": "Titulo de la obra",
  "razonamiento_director": "Decisiones de ritmo, camara y casting",
  "biblia_visual": "Descripcion visual fija",
  "decisiones_edicion": {"fuerza_coherencia": 0.65, "zoom_camara": true, "pausa_escenas": 0.35},
  "escenas": [
    {
      "escena": 1,
      "personaje": "NombrePersonaje",
      "genero": "M",
      "tono_hz": -2,
      "texto_es": "Dialogo limpio en espanol",
      "texto_en": "Clean dialogue in English",
      "prompt_imagen": "Detailed English visual prompt"
    }
  ]
}
"""
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=borrador_guion,
            config=types.GenerateContentConfig(
                system_instruction=prompt_director,
                response_mime_type="application/json",
                temperature=0.68
            )
        )
        plan = json.loads(resp.text)
        self.log(f"[Decision Director] {plan.get('razonamiento_director')}")
        mcp_tools.mcp_gestionar_archivo("crear", "ultimo_plan_director.json", json.dumps(plan, indent=2, ensure_ascii=False))

        # Sub-parte 11.3: Ejecucion encadenada MCP, liberacion bajo demanda y renderizado
        dec = plan.get("decisiones_edicion", {})
        coherencia = float(dec.get("fuerza_coherencia", 0.65))
        zoom = bool(dec.get("zoom_camara", True))
        pausa = float(dec.get("pausa_escenas", 0.35))
        biblia = plan.get("biblia_visual", "")

        imagen_previa = ""
        escenas_listas = []

        try:
            for idx, esc in enumerate(plan.get("escenas", []), start=1):
                pers = esc.get("personaje", f"Personaje_{idx}")
                gen = esc.get("genero", "M")
                tono = int(esc.get("tono_hz", 0))

                voz_cfg = json.loads(mcp_tools.mcp_asignar_voz_personaje(pers, gen, tono, 0))
                self.log(f"[MCP Voz] '{pers}' -> {voz_cfg['perfil']['voz_es']} ({voz_cfg['perfil']['asignada_por']})")

                prompt_full = f"{biblia}, {esc['prompt_imagen']}"
                self.log(f"[MCP Imagen] Generando cuadro {idx} encadenado al anterior...")
                ruta_img = mcp_tools.mcp_generar_cuadro_coherente(
                    prompt_visual=prompt_full,
                    ruta_imagen_anterior=imagen_previa,
                    fuerza_coherencia=coherencia,
                    pasos=int(pasos_sdxl),
                    semilla=2000 + idx
                )
                imagen_previa = ruta_img

                aud_es = json.loads(mcp_tools.mcp_sintetizar_voz_dialogo(pers, esc["texto_es"], "es", gen, tono))
                aud_en = json.loads(mcp_tools.mcp_sintetizar_voz_dialogo(pers, esc["texto_en"], "en", gen, tono))

                escenas_listas.append({
                    "escena": idx,
                    "personaje": pers,
                    "imagen": ruta_img,
                    "audio_es": aud_es["audio"],
                    "audio_en": aud_en["audio"],
                    "texto_es": aud_es["texto"],
                    "texto_en": aud_en["texto"]
                })
        finally:
            mcp_tools.mcp_liberar_gpu_imagen()

        HISTORIAL_PROYECTO_PATH.write_text(json.dumps(escenas_listas, indent=2, ensure_ascii=False), encoding="utf-8")
        self.log(f"[MCP Editor] Renderizando pelicula con subtitulos '{modo_subs}'...")
        res_vid = json.loads(mcp_tools.mcp_editar_y_renderizar_video(idioma_audio, modo_subs, zoom, pausa))
        self.log("[Completado] Produccion finalizada.")

        return (
            "\n".join(self.bitacora),
            json.dumps(plan, indent=2, ensure_ascii=False),
            [(e["imagen"], f"Escena {e['escena']} - {e['personaje']}") for e in escenas_listas],
            res_vid["video_mp4"],
            res_vid["subtitulos_srt"]
        )
