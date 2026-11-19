import json
from pathlib import Path
from google import genai
from google.genai import types
from voz_interactiva import VozInteractivaAgente
from director_cinematografico import DirectorCinematografico
from verificador_calidad import VerificadorCalidadTotal
from motor_bloques_largos import GestorBloquesLargos
from gestor_proyectos_resume import GestorProyectosResume
from gestor_documentos_guionista import ExportadorGuionPDF, redactar_con_chatgpt_opcional
from sincronizador_av import SincronizadorPrecisionAV
from config_rutas import HISTORIAL_PROYECTO_PATH
import servidor_mcp as mcp_tools

class AgenteDirectorAutonomo:
    def __init__(self):
        self.voz_agente = VozInteractivaAgente()
        self.cineasta = DirectorCinematografico()
        self.auditor = VerificadorCalidadTotal()
        self.bloques_mgr = GestorBloquesLargos()
        self.proyectos_mgr = GestorProyectosResume()
        self.pdf_export = ExportadorGuionPDF()
        self.sync_av = SincronizadorPrecisionAV()
        self.bitacora = []

    def log(self, msg):
        self.bitacora.append(msg)

    # Parte 1/6: Clasificador inteligente (Chat normal por defecto, accion solo por orden explicita)
    def procesar_interaccion(self, api_key, mensaje_usuario, nombre_proyecto="Proyecto_Principal", pasos_sdxl=12, idioma_audio="es", modo_subs="Ambos (ES + EN)", openai_key="", reanudar=True):
        client = genai.Client(api_key=api_key.strip(), http_options={"api_version": "v1beta"})

        clasificador = """
Eres un asistente de inteligencia artificial amable, natural y conversacional, que ademas cuenta con herramientas profesionales de produccion y edicion de video por MCP.
REGLA ESTRICTA:
- Si el usuario saluda, charla, hace preguntas, pide ideas o escribe un guion sin pedir todavia que hagas el video, clasifica como "conversar" y responde normalmente como un chat de IA amigable.
- SOLO clasifica como "producir_video" si el usuario te ordena explicitamente crear, generar, hacer o renderizar un video, pelicula o escenas.
- SOLO clasifica como "re_editar" si pide explicitamente modificar un video ya hecho (ej. cambiar idioma a ingles o espanol, cambiar subtitulos o ritmo).
- SOLO clasifica como "gestion_archivo" si pide explicitamente crear, guardar, leer o listar archivos.

Devuelve SOLO JSON valido:
{
  "accion": "conversar | producir_video | re_editar | gestion_archivo",
  "respuesta_chat": "Tu respuesta completa y natural como chat de IA",
  "respuesta_corta_voz": "Resumen breve de 1 o 2 frases para leer en voz alta",
  "archivo_accion": "crear | leer | listar | ninguno",
  "archivo_nombre": "notas.txt",
  "archivo_contenido": ""
}
"""
        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=mensaje_usuario,
            config=types.GenerateContentConfig(
                system_instruction=clasificador,
                response_mime_type="application/json",
                temperature=0.5
            )
        )
        dec = json.loads(res.text)
        accion = dec.get("accion", "conversar")
        resp_chat = dec.get("respuesta_chat", "Hola, en que te puedo ayudar hoy?")
        resp_voz_txt = dec.get("respuesta_corta_voz", resp_chat[:220])

        # Parte 2/6: Enrutamiento segun la intencion detectada
        if accion == "gestion_archivo" and dec.get("archivo_accion") in ("crear", "leer", "listar"):
            out_a = mcp_tools.mcp_gestionar_archivo(
                dec["archivo_accion"],
                dec.get("archivo_nombre", "notas.txt"),
                dec.get("archivo_contenido", mensaje_usuario)
            )
            if dec["archivo_accion"] == "leer":
                resp_chat = f"Contenido de {dec.get('archivo_nombre')}:\n\n{out_a}"
                resp_voz_txt = "Aqui tienes el contenido del archivo solicitado."
            else:
                resp_chat = f"{resp_chat}\n\n({out_a})"
                resp_voz_txt = out_a

        voz_resp = self.voz_agente.hablar_respuesta(resp_voz_txt, idioma="es")

        if accion == "re_editar":
            lang = "en" if ("ingles" in mensaje_usuario.lower() or "english" in mensaje_usuario.lower()) else "es"
            ed = json.loads(mcp_tools.mcp_editar_y_renderizar_video(lang, modo_subs, nombre_proyecto))
            if "error" in ed:
                err_msg = "Aun no hay ningun video generado para re-editar. Pideme crear uno primero."
                return err_msg, self.voz_agente.hablar_respuesta(err_msg), err_msg, "{}", [], None, None, None
            return resp_chat, voz_resp, "Video re-editado por orden explicita.", "{}", [], ed.get("video_mp4"), None, None

        elif accion == "producir_video":
            bit, plan_str, galeria, mp4_principal, zip_final, pdf_guion = self.producir_proyecto_largo(
                api_key, mensaje_usuario, nombre_proyecto, pasos_sdxl, idioma_audio, modo_subs, openai_key, reanudar
            )
            fin_txt = f"{resp_chat}\n\nProduccion completada: el proyecto '{nombre_proyecto}' ya esta renderizado y guardado."
            voz_fin = self.voz_agente.hablar_respuesta(f"Listo, el video del proyecto {nombre_proyecto} ya esta terminado.", idioma="es")
            return fin_txt, voz_fin, bit, plan_str, galeria, mp4_principal, zip_final, pdf_guion

        return resp_chat, voz_resp, "Modo conversacion normal activo.", "{}", [], None, None, None

    # Parte 3/6: Motor completo de produccion por bloques de 10 minutos y respaldo Drive
    def producir_proyecto_largo(self, api_key, instruccion, nombre_proyecto="Proyecto_Principal", pasos_sdxl=15, idioma_audio="es", modo_subs="Ambos (ES + EN)", openai_key="", reanudar=True):
        self.bitacora = []
        client = genai.Client(api_key=api_key.strip(), http_options={"api_version": "v1beta"})
        estado = self.proyectos_mgr.cargar_estado_proyecto(nombre_proyecto) if reanudar else self.proyectos_mgr.cargar_estado_proyecto(f"{nombre_proyecto}_nuevo")

        if reanudar and estado.get("plan_director") and estado.get("escenas_completadas"):
            plan = estado["plan_director"]
            self.log(f"[Recuperacion Colab/Drive] Retomando proyecto '{nombre_proyecto}' con {len(estado['escenas_completadas'])} escenas ya guardadas.")
        else:
            borrador = redactar_con_chatgpt_opcional(openai_key, instruccion) if (openai_key and openai_key.strip()) else instruccion
            if openai_key and openai_key.strip():
                self.log("[ChatGPT Guionista Opcional] Propuesta literaria incorporada.")

            self.log("[Cerebro Gemini] Creando Biblia Visual, casting ilimitado y plan de bloques...")
            prompt_dir = """
Eres un Agente Director de Cine y Editor Profesional conectado por MCP.
Estructura la historia (sin limite de personajes ni duracion) en escenas coherentes:
1. 'biblia_visual': Rasgos fisicos, ropa e iluminacion constantes para continuidad cuadro a cuadro.
2. 'texto_es' y 'texto_en': SOLO lo que dice el personaje (JAMAS pongas el nombre del personaje).
3. Asigna 'genero' ('M' o 'F') y 'tono_hz' (-15 a +15) a cada personaje.

Devuelve SOLO JSON:
{
  "titulo": "Titulo",
  "razonamiento_director": "Decisiones de direccion y ritmo",
  "biblia_visual": "Descripcion visual constante",
  "decisiones_edicion": {"fuerza_coherencia": 0.64},
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
                contents=borrador,
                config=types.GenerateContentConfig(
                    system_instruction=prompt_dir,
                    response_mime_type="application/json",
                    temperature=0.65
                )
            )
            plan = json.loads(resp.text)
            estado["plan_director"] = plan
            self.proyectos_mgr.guardar_progreso_escena(nombre_proyecto, estado, 0, {}, "")

        biblia = plan.get("biblia_visual", "")
        coherencia = float(plan.get("decisiones_edicion", {}).get("fuerza_coherencia", 0.64))
        todas_escenas_plan = plan.get("escenas", [])

        bloques_plan = self.bloques_mgr.dividir_en_bloques_10min(todas_escenas_plan, max_segundos_bloque=600.0)
        self.log(f"[Bloques 10 Min] Historia organizada en {len(bloques_plan)} bloque(s) de hasta 10 minutos.")

        mcp_tools.coherencia_srv.reiniciar_secuencia(semilla_base=5000)
        if estado.get("ultimo_fotograma") and Path(estado["ultimo_fotograma"]).exists():
            mcp_tools.coherencia_srv.ultimo_fotograma_valido = estado["ultimo_fotograma"]

        todas_escenas_renderizadas = []
        videos_bloques = []
        srts_bloques = []

        try:
            for num_bloque, escenas_del_bloque in enumerate(bloques_plan, start=1):
                self.log(f"--- PROCESANDO BLOQUE {num_bloque}/{len(bloques_plan)} ---")
                escenas_bloque_listas = []

                for esc in escenas_del_bloque:
                    idx_global = int(esc.get("escena", len(todas_escenas_renderizadas) + 1))
                    clave_idx = str(idx_global)

                    if clave_idx in estado["escenas_completadas"] and estado["escenas_completadas"][clave_idx]:
                        esc_guardada = estado["escenas_completadas"][clave_idx]
                        ok_prev, _ = self.auditor.auditar_escena_completa(esc_guardada)
                        if ok_prev:
                            self.log(f"[Checkpoint Drive] Escena {idx_global} recuperada sin regenerar.")
                            escenas_bloque_listas.append(esc_guardada)
                            todas_escenas_renderizadas.append(esc_guardada)
                            continue

                    pers = esc.get("personaje", f"Personaje_{idx_global}")
                    gen = esc.get("genero", "M")
                    tono = int(esc.get("tono_hz", 0))

                    dir_cine = self.cineasta.enriquecer_direccion_escena(idx_global, esc["prompt_imagen"], esc["texto_es"])

                    ruta_img = ""
                    for intento in range(2):
                        ruta_img = mcp_tools.mcp_generar_cuadro_coherente(
                            biblia_visual=biblia,
                            prompt_escena=dir_cine["prompt_dirigido"],
                            accion_narrada=esc["texto_en"],
                            indice_escena=idx_global + (intento * 100),
                            fuerza_coherencia=coherencia,
                            pasos=int(pasos_sdxl)
                        )
                        ok_i, _ = self.auditor.verificar_imagen(ruta_img)
                        if ok_i:
                            break
                        self.log(f"[Auditor Calidad] Regenerando cuadro {idx_global} por fallo detectado...")

                    aud_es = json.loads(mcp_tools.mcp_sintetizar_voz_dialogo(pers, esc["texto_es"], "es", gen, tono))
                    aud_en = json.loads(mcp_tools.mcp_sintetizar_voz_dialogo(pers, esc["texto_en"], "en", gen, tono))

                    datos_esc = {
                        "escena": idx_global,
                        "personaje": pers,
                        "imagen": ruta_img,
                        "audio_es": aud_es["audio"],
                        "audio_en": aud_en["audio"],
                        "texto_es": aud_es["texto"],
                        "texto_en": aud_en["texto"],
                        "zoom_factor": dir_cine["zoom_factor"],
                        "pausa_corte": dir_cine["pausa_corte"]
                    }

                    ok_total, msg_aud = self.auditor.auditar_escena_completa(datos_esc)
                    self.log(f"[Escena {idx_global} - {pers}] {msg_aud}")

                    escenas_bloque_listas.append(datos_esc)
                    todas_escenas_renderizadas.append(datos_esc)
                    self.proyectos_mgr.guardar_progreso_escena(nombre_proyecto, estado, idx_global, datos_esc, ruta_img)

                mp4_b, srt_b = self.sync_av.compilar_bloque_sincronizado(
                    escenas_bloque_listas, idioma_audio=idioma_audio, modo_subs=modo_subs, nombre_archivo=f"{nombre_proyecto}_B{num_bloque:02d}"
                )
                videos_bloques.append(mp4_b)
                srts_bloques.append(srt_b)
                self.proyectos_mgr.registrar_bloque_terminado(nombre_proyecto, estado, num_bloque, mp4_b, srt_b, escenas_bloque_listas)
                self.log(f"[Google Drive Auto-Save] Bloque {num_bloque} respaldado automaticamente en Drive.")
        finally:
            mcp_tools.mcp_liberar_gpu_imagen()

        HISTORIAL_PROYECTO_PATH.write_text(json.dumps(todas_escenas_renderizadas, indent=2, ensure_ascii=False), encoding="utf-8")

        ruta_pdf_guion = self.pdf_export.exportar_plan_a_pdf(plan, nombre_base=nombre_proyecto)
        ruta_zip_final = self.bloques_mgr.empaquetar_produccion_zip(nombre_proyecto, videos_bloques, srts_bloques, ruta_pdf_guion)
        self.proyectos_mgr.drive_sync.respaldar_archivo_final(nombre_proyecto, ruta_zip_final)
        self.proyectos_mgr.drive_sync.respaldar_archivo_final(nombre_proyecto, ruta_pdf_guion)
        self.log(f"[ZIP + PDF Listos] Todo empaquetado y respaldado en Drive: {Path(ruta_zip_final).name}")

        return (
            "\n".join(self.bitacora),
            json.dumps(plan, indent=2, ensure_ascii=False),
            [(e["imagen"], f"Escena {e['escena']} - {e['personaje']}") for e in todas_escenas_renderizadas[:18]],
            videos_bloques[0] if videos_bloques else None,
            ruta_zip_final,
            ruta_pdf_guion
        )
