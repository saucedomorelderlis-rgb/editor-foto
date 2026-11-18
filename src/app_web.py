import json
import gradio as gr
from agente_director import AgenteDirectorAutonomo
from clonador_voz import MotorCastingYVozPropia
from gestor_voces import VOCES_DISPONIBLES
from motor_video import SalaEdicionVideo
from puente_telegram import iniciar_puente_telegram
from config_rutas import DEVICE, cargar_config, guardar_config, HISTORIAL_PROYECTO_PATH

# Sub-parte 13.1: Inicializacion y funciones puente de interfaz
agente = AgenteDirectorAutonomo()
casting = MotorCastingYVozPropia()
editor_vid = SalaEdicionVideo()
cfg_inicial = cargar_config()

if cfg_inicial.get("telegram_token"):
    iniciar_puente_telegram(cfg_inicial["telegram_token"])

def ui_hablar_con_agente(api_key, openai_key, audio_mic, pdf_doc, texto_orden, pasos, idioma_aud, modo_subs):
    if not api_key.strip():
        return "Falta tu Gemini API Key.", None, "Sin API Key", "{}", [], None, None
    guardar_config(gemini_key=api_key, openai_key=openai_key)

    instruccion = texto_orden.strip()
    if audio_mic:
        transcripcion = agente.voz_agente.escuchar_audio(api_key, audio_mic)
        instruccion = f"{transcripcion} {instruccion}".strip()

    if pdf_doc:
        try:
            from lector_guiones_pdf import LectorGuionesPDF
            datos_pdf = LectorGuionesPDF().analizar_pdf(api_key, pdf_doc)
            instruccion = f"{instruccion}\n\nGuion extraido del PDF:\n{datos_pdf}".strip()
        except Exception:
            instruccion = f"{instruccion}\n\nProcesa el PDF ubicado en: {pdf_doc}".strip()

    if not instruccion:
        return "Habla por microfono, sube un PDF o escribe una orden.", None, "", "{}", [], None, None

    guionista_fn = None
    if openai_key and openai_key.strip():
        try:
            from gestor_documentos_guionista import redactar_con_chatgpt_opcional
            guionista_fn = redactar_con_chatgpt_opcional
        except Exception:
            guionista_fn = None

    return agente.procesar_interaccion(
        api_key, instruccion, int(pasos), idioma_aud, modo_subs, guionista_fn, openai_key
    )

def ui_guardar_voz_personal(personaje, v_es, v_en, vel, tono, vol, archivo_audio, frase_test):
    msg = casting.registrar_voz_usuario(personaje, v_es, v_en, vel, tono, vol, archivo_voz_propia=archivo_audio)
    aud_path, _ = casting.generar_voz_personaje(personaje, frase_test or "Esta es mi voz configurada para el proyecto.", idioma="es", tag="test")
    return msg, aud_path, json.dumps(casting.gestor.perfiles, indent=2, ensure_ascii=False)

def ui_reexportar_video(idioma_aud, modo_subs, zoom, pausa):
    if not HISTORIAL_PROYECTO_PATH.exists():
        return None, None, "Primero genera una historia en la Pestana 1."
    escenas = json.loads(HISTORIAL_PROYECTO_PATH.read_text(encoding="utf-8"))
    mp4, srt = editor_vid.renderizar_secuencia(escenas, idioma_aud, modo_subs, zoom, pausa)
    return mp4, srt, f"Video re-editado en audio '{idioma_aud.upper()}' con subtitulos '{modo_subs}'."

# Sub-parte 13.2: Interfaz grafica web unificada en puerto 18789
with gr.Blocks(title="Agente Autonomo Cine IA + MCP + Telegram", theme=gr.themes.Soft()) as demo:
    gr.Markdown(f"# Agente Autonomo de Cine IA + MCP + Voz + Telegram (`{DEVICE.upper()}`)")
    gr.Markdown("Habla con el **Agente Director**, sube guiones **PDF**, conecta **Telegram** y exporta videos coherentes en **Espanol e Ingles**.")

    with gr.Tabs():
        with gr.TabItem("1. Agente Director Conversacional (Voz / PDF / Video)"):
            with gr.Row():
                with gr.Column(scale=1):
                    with gr.Row():
                        api_in = gr.Textbox(label="Gemini API Key (Principal)", value=cfg_inicial.get("gemini_api_key", ""), type="password")
                        openai_in = gr.Textbox(label="ChatGPT API Key (Guionista Opcional)", value=cfg_inicial.get("openai_api_key", ""), type="password", placeholder="Opcional...")
                    with gr.Row():
                        mic_in = gr.Audio(label="Habla al Agente (Microfono)", sources=["microphone"], type="filepath")
                        pdf_in = gr.File(label="Subir Guion PDF (Opcional)", file_types=[".pdf"])
                    orden_in = gr.Textbox(label="Orden o Guion (Personajes ilimitados)", lines=3, placeholder="Ej: Crea una historia de 3 escenas o dile 'Cambia el video anterior a ingles'...")
                    with gr.Row():
                        pasos_in = gr.Slider(6, 35, value=10 if DEVICE=="cpu" else 25, step=1, label="Pasos SDXL")
                        aud_lang = gr.Radio(["es", "en"], value="es", label="Audio")
                        subs_mode = gr.Dropdown(["Ambos (ES + EN)", "Espanol", "Ingles", "Sin Subtitulos"], value="Ambos (ES + EN)", label="Subtitulos")
                    btn_run = gr.Button("Enviar Orden al Agente Director", variant="primary")
                    resp_txt_out = gr.Textbox(label="Respuesta del Agente")
                    resp_voz_out = gr.Audio(label="Voz del Agente Director", autoplay=True)
                    bitacora_out = gr.Textbox(label="Bitacora de Herramientas MCP Ejecutadas", lines=5)

                with gr.Column(scale=1):
                    plan_json_out = gr.Code(label="Plan Director JSON", language="json", lines=7)
                    galeria_out = gr.Gallery(label="Cuadros Coherentes Generados", columns=3, height=200)
                    video_out = gr.Video(label="Pelicula Renderizada (MP4)")
                    srt_out = gr.File(label="Subtitulos (.SRT)")

            btn_run.click(
                ui_hablar_con_agente,
                [api_in, openai_in, mic_in, pdf_in, orden_in, pasos_in, aud_lang, subs_mode],
                [resp_txt_out, resp_voz_out, bitacora_out, plan_json_out, galeria_out, video_out, srt_out]
            )

        with gr.TabItem("2. Protocolo Conexion Telegram"):
            gr.Markdown("Conecta tu Bot de Telegram (`@BotFather`). Puedes enviarle **texto, notas de voz o archivos PDF** y te respondera por voz con el video terminado.")
            tg_token_in = gr.Textbox(label="Token del Bot de Telegram", value=cfg_inicial.get("telegram_token", ""), type="password")
            btn_tg = gr.Button("Activar / Guardar Conexion Telegram", variant="primary")
            tg_status_out = gr.Textbox(label="Estado del Puente Telegram")
            btn_tg.click(iniciar_puente_telegram, [tg_token_in], [tg_status_out])

        with gr.TabItem("3. Personajes Ilimitados y Propia Voz"):
            with gr.Row():
                with gr.Column():
                    p_nom = gr.Textbox(label="Nombre del Personaje (Ilimitados)", placeholder="Ej: Sofia, Capitan, Villano...")
                    v_es_dd = gr.Dropdown(list(VOCES_DISPONIBLES.keys()), value="ES (Mexico) - Jorge (Hombre Profundo)", label="Voz Espanol")
                    v_en_dd = gr.Dropdown(list(VOCES_DISPONIBLES.keys()), value="EN (US) - Brian (Hombre Profundo)", label="Voz Ingles")
                    voz_propia_in = gr.Audio(label="Grabar o Subir Tu Propia Voz (Opcional)", sources=["microphone", "upload"], type="filepath")
                    with gr.Row():
                        vel_s = gr.Slider(-40, 40, value=0, step=5, label="Velocidad (%)")
                        tono_s = gr.Slider(-25, 25, value=0, step=1, label="Tono (Hz)")
                        vol_s = gr.Slider(-30, 30, value=0, step=5, label="Volumen (%)")
                    test_txt = gr.Textbox(label="Frase de Prueba", value="Mi voz esta lista para entrar en escena.")
                    btn_save_v = gr.Button("Guardar Voz Afinada", variant="primary")
                    msg_v = gr.Textbox(label="Estado")
                    aud_test = gr.Audio(label="Escuchar Voz")
                with gr.Column():
                    perfiles_box = gr.Code(label="Perfiles de Personajes (Manuales + Auto-Casting IA)", value=json.dumps(casting.gestor.perfiles, indent=2, ensure_ascii=False), language="json", lines=18)

            btn_save_v.click(ui_guardar_voz_personal, [p_nom, v_es_dd, v_en_dd, vel_s, tono_s, vol_s, voz_propia_in, test_txt], [msg_v, aud_test, perfiles_box])

        with gr.TabItem("4. Editor de Video (Audio ES/EN y Subtitulos)"):
            with gr.Row():
                with gr.Column():
                    ed_lang = gr.Radio(["es", "en"], value="en", label="Idioma de Pista de Audio")
                    ed_subs = gr.Dropdown(["Ambos (ES + EN)", "Espanol", "Ingles", "Sin Subtitulos"], value="Ambos (ES + EN)", label="Subtitulos")
                    ed_zoom = gr.Checkbox(value=True, label="Zoom Cinematografico")
                    ed_pausa = gr.Slider(0.0, 2.0, value=0.35, step=0.05, label="Pausa entre Cortes (segundos)")
                    btn_ed = gr.Button("Renderizar Nueva Edicion MP4", variant="primary")
                    ed_status = gr.Textbox(label="Estado")
                with gr.Column():
                    ed_vid_out = gr.Video(label="Video Editado")
                    ed_srt_out = gr.File(label="Subtitulos (.SRT)")

            btn_ed.click(ui_reexportar_video, [ed_lang, ed_subs, ed_zoom, ed_pausa], [ed_vid_out, ed_srt_out, ed_status])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=18789, share=False)

# Sub-parte 13.2: Interfaz grafica web unificada en puerto 18789
with gr.Blocks(title="Agente Autonomo Cine IA + MCP + Telegram", theme=gr.themes.Soft()) as demo:
    gr.Markdown(f"# Agente Autonomo de Cine IA + MCP + Voz + Telegram (`{DEVICE.upper()}`)")
    gr.Markdown("Habla con el **Agente Director**, sube guiones **PDF**, conecta **Telegram** y exporta videos coherentes en **Espanol e Ingles**.")

    with gr.Tabs():
        with gr.TabItem("1. Agente Director Conversacional (Voz / PDF / Video)"):
            with gr.Row():
                with gr.Column(scale=1):
                    with gr.Row():
                        api_in = gr.Textbox(label="Gemini API Key (Principal)", value=cfg_inicial.get("gemini_api_key", ""), type="password")
                        openai_in = gr.Textbox(label="ChatGPT API Key (Guionista Opcional)", value=cfg_inicial.get("openai_api_key", ""), type="password", placeholder="Opcional...")
                    with gr.Row():
                        mic_in = gr.Audio(label="Habla al Agente (Microfono)", sources=["microphone"], type="filepath")
                        pdf_in = gr.File(label="Subir Guion PDF (Opcional)", file_types=[".pdf"])
                    orden_in = gr.Textbox(label="Orden o Guion (Personajes ilimitados)", lines=3, placeholder="Ej: Crea una historia de 3 escenas o dile 'Cambia el video anterior a ingles'...")
                    with gr.Row():
                        pasos_in = gr.Slider(6, 35, value=10 if DEVICE=="cpu" else 25, step=1, label="Pasos SDXL")
                        aud_lang = gr.Radio(["es", "en"], value="es", label="Audio")
                        subs_mode = gr.Dropdown(["Ambos (ES + EN)", "Espanol", "Ingles", "Sin Subtitulos"], value="Ambos (ES + EN)", label="Subtitulos")
                    btn_run = gr.Button("Enviar Orden al Agente Director", variant="primary")
                    resp_txt_out = gr.Textbox(label="Respuesta del Agente")
                    resp_voz_out = gr.Audio(label="Voz del Agente Director", autoplay=True)
                    bitacora_out = gr.Textbox(label="Bitacora de Herramientas MCP Ejecutadas", lines=5)

                with gr.Column(scale=1):
                    plan_json_out = gr.Code(label="Plan Director JSON", language="json", lines=7)
                    galeria_out = gr.Gallery(label="Cuadros Coherentes Generados", columns=3, height=200)
                    video_out = gr.Video(label="Pelicula Renderizada (MP4)")
                    srt_out = gr.File(label="Subtitulos (.SRT)")

            btn_run.click(
                ui_hablar_con_agente,
                [api_in, openai_in, mic_in, pdf_in, orden_in, pasos_in, aud_lang, subs_mode],
                [resp_txt_out, resp_voz_out, bitacora_out, plan_json_out, galeria_out, video_out, srt_out]
            )

        with gr.TabItem("2. Protocolo Conexion Telegram"):
            gr.Markdown("Conecta tu Bot de Telegram (`@BotFather`). Puedes enviarle **texto, notas de voz o archivos PDF** y te respondera por voz con el video terminado.")
            tg_token_in = gr.Textbox(label="Token del Bot de Telegram", value=cfg_inicial.get("telegram_token", ""), type="password")
            btn_tg = gr.Button("Activar / Guardar Conexion Telegram", variant="primary")
            tg_status_out = gr.Textbox(label="Estado del Puente Telegram")
            btn_tg.click(iniciar_puente_telegram, [tg_token_in], [tg_status_out])

        with gr.TabItem("3. Personajes Ilimitados y Propia Voz"):
            with gr.Row():
                with gr.Column():
                    p_nom = gr.Textbox(label="Nombre del Personaje (Ilimitados)", placeholder="Ej: Sofia, Capitan, Villano...")
                    v_es_dd = gr.Dropdown(list(VOCES_DISPONIBLES.keys()), value="ES (Mexico) - Jorge (Hombre Profundo)", label="Voz Espanol")
                    v_en_dd = gr.Dropdown(list(VOCES_DISPONIBLES.keys()), value="EN (US) - Brian (Hombre Profundo)", label="Voz Ingles")
                    voz_propia_in = gr.Audio(label="Grabar o Subir Tu Propia Voz (Opcional)", sources=["microphone", "upload"], type="filepath")
                    with gr.Row():
                        vel_s = gr.Slider(-40, 40, value=0, step=5, label="Velocidad (%)")
                        tono_s = gr.Slider(-25, 25, value=0, step=1, label="Tono (Hz)")
                        vol_s = gr.Slider(-30, 30, value=0, step=5, label="Volumen (%)")
                    test_txt = gr.Textbox(label="Frase de Prueba", value="Mi voz esta lista para entrar en escena.")
                    btn_save_v = gr.Button("Guardar Voz Afinada", variant="primary")
                    msg_v = gr.Textbox(label="Estado")
                    aud_test = gr.Audio(label="Escuchar Voz")
                with gr.Column():
                    perfiles_box = gr.Code(label="Perfiles de Personajes (Manuales + Auto-Casting IA)", value=json.dumps(casting.gestor.perfiles, indent=2, ensure_ascii=False), language="json", lines=18)

            btn_save_v.click(ui_guardar_voz_personal, [p_nom, v_es_dd, v_en_dd, vel_s, tono_s, vol_s, voz_propia_in, test_txt], [msg_v, aud_test, perfiles_box])

        with gr.TabItem("4. Editor de Video (Audio ES/EN y Subtitulos)"):
            with gr.Row():
                with gr.Column():
                    ed_lang = gr.Radio(["es", "en"], value="en", label="Idioma de Pista de Audio")
                    ed_subs = gr.Dropdown(["Ambos (ES + EN)", "Espanol", "Ingles", "Sin Subtitulos"], value="Ambos (ES + EN)", label="Subtitulos")
                    ed_zoom = gr.Checkbox(value=True, label="Zoom Cinematografico")
                    ed_pausa = gr.Slider(0.0, 2.0, value=0.35, step=0.05, label="Pausa entre Cortes (segundos)")
                    btn_ed = gr.Button("Renderizar Nueva Edicion MP4", variant="primary")
                    ed_status = gr.Textbox(label="Estado")
                with gr.Column():
                    ed_vid_out = gr.Video(label="Video Editado")
                    ed_srt_out = gr.File(label="Subtitulos (.SRT)")

            btn_ed.click(ui_reexportar_video, [ed_lang, ed_subs, ed_zoom, ed_pausa], [ed_vid_out, ed_srt_out, ed_status])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=18789, share=False)
