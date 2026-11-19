import json
import gradio as gr
from agente_director import AgenteDirectorAutonomo
from clonador_voz import MotorCastingYVozPropia
from gestor_voces import VOCES_DISPONIBLES
from motor_voces_kokoro import CATALOGO_KOKORO_DESCRITO
from sincronizador_av import SincronizadorPrecisionAV
from gestor_proyectos_resume import GestorProyectosResume
from puente_telegram import iniciar_puente_telegram
from puente_cpp_lazy import MotorOptimizadorCPP
import servidor_mcp as mcp_srv
from config_rutas import DEVICE, cargar_config, guardar_config, HISTORIAL_PROYECTO_PATH

# Parte 1/5: Inicializacion de los 26 motores y funciones de control
agente = AgenteDirectorAutonomo()
casting = MotorCastingYVozPropia()
sync_av = SincronizadorPrecisionAV()
proyectos_mgr = GestorProyectosResume()
cpp_opt = MotorOptimizadorCPP()
cfg_inicial = cargar_config()

tg_estado_inicial = "Inactivo"
if cfg_inicial.get("telegram_token"):
    tg_estado_inicial = iniciar_puente_telegram(cfg_inicial["telegram_token"])

def ui_ejecutar_estudio(api_key, openai_key, nom_proyecto, reanudar_chk, audio_mic, pdf_doc, texto_orden, pasos, idioma_aud, modo_subs):
    if not api_key.strip():
        return "Falta Gemini API Key.", None, "Sin API Key", "{}", [], None, None, None, None
    guardar_config(gemini_key=api_key, openai_key=openai_key, proyecto_activo=nom_proyecto)

    instruccion = texto_orden.strip()
    if audio_mic:
        transcripcion = agente.voz_agente.escuchar_audio(api_key, audio_mic)
        instruccion = f"{transcripcion} {instruccion}".strip()

    if pdf_doc:
        from lector_guiones_pdf import LectorGuionesPDF
        datos_pdf = LectorGuionesPDF().analizar_pdf(api_key, pdf_doc)
        instruccion = f"{instruccion}\n\nGuion extraido del PDF:\n{datos_pdf}".strip()

    if not instruccion and not reanudar_chk:
        return "Habla por microfono, sube un PDF o escribe una instruccion.", None, "", "{}", [], None, None, None, None

    res = agente.procesar_interaccion(
        api_key,
        instruccion or f"Continuar proyecto {nom_proyecto}",
        nombre_proyecto=nom_proyecto.strip() or "Proyecto_Principal",
        pasos_sdxl=int(pasos),
        idioma_audio=idioma_aud,
        modo_subs=modo_subs,
        openai_key=openai_key,
        reanudar=reanudar_chk
    )
    srt_ultimo = None
    estado_p = proyectos_mgr.cargar_estado_proyecto(nom_proyecto.strip() or "Proyecto_Principal")
    if estado_p.get("srts_renderizados"):
        srt_ultimo = estado_p["srts_renderizados"][-1]
    return res[0], res[1], res[2], res[3], res[4], res[5], res[6], res[7], srt_ultimo

def ui_guardar_voz(personaje, v_es, v_en, vel, tono, vol, archivo_audio, frase_test):
    msg = casting.registrar_voz_usuario(personaje, v_es, v_en, vel, tono, vol, archivo_voz_propia=archivo_audio)
    aud_path, _ = casting.generar_voz_personaje(personaje, frase_test or "Esta es mi voz configurada para el proyecto.", idioma="es", tag="test")
    return msg, aud_path, json.dumps(casting.gestor.perfiles, indent=2, ensure_ascii=False)

def ui_reexportar(idioma_aud, modo_subs):
    if not HISTORIAL_PROYECTO_PATH.exists():
        return None, None, "Primero genera una historia en la Estacion 1."
    escenas = json.loads(HISTORIAL_PROYECTO_PATH.read_text(encoding="utf-8"))
    mp4, srt = sync_av.compilar_bloque_sincronizado(escenas, idioma_audio=idioma_aud, modo_subs=modo_subs, nombre_archivo="reedicion_pro")
    return mp4, srt, f"Nueva version renderizada en '{idioma_aud.upper()}' con subtitulos '{modo_subs}'."

def ui_limpiar_memoria_cpp():
    mcp_srv.mcp_liberar_gpu_imagen()
    cpp_opt.descargar_de_memoria()
    return f"Memoria VRAM/RAM liberada bajo demanda ({DEVICE.upper()})."

def ui_refrescar_proyectos():
    lista = proyectos_mgr.listar_proyectos_guardados()
    return gr.Dropdown(choices=lista if lista else ["Proyecto_Principal"])

tabla_kokoro = [[k, v["nombre"], v["idioma"], v["genero"], v["descripcion"]] for k, v in CATALOGO_KOKORO_DESCRITO.items()]

# Parte 2/5: Panel Lateral Desplegable de Configuracion Global y Nube
with gr.Blocks(title="Estudio Cine IA Pro — 26 Partes Unificadas") as demo:
    gr.Markdown(
        f"# 🎬 ESTUDIO DE CINE AUTÓNOMO IA — SUITE PROFESIONAL (26 PARTES EN 1) | `{DEVICE.upper()}`\n"
        "**Gemini + ChatGPT (Opcional) • Protocolo MCP • Motor C++ Bajo Demanda • Kokoro-82M • Telegram `@asitem_bot` • Auto-Respaldo Google Drive**"
    )

    with gr.Sidebar(label="⚙️ Panel de Control y Conexiones", open=True):
        with gr.Accordion("🔑 1. Cerebros IA (Gemini + ChatGPT)", open=False):
            api_in = gr.Textbox(label="Gemini API Key (Principal)", value=cfg_inicial.get("gemini_api_key", ""), type="password")
            openai_in = gr.Textbox(label="ChatGPT API Key (Guionista Opcional)", value=cfg_inicial.get("openai_api_key", ""), type="password", placeholder="Opcional...")

        with gr.Accordion("📱 2. Puente Telegram (@asitem_bot)", open=True):
            tg_token_in = gr.Textbox(label="Token Bot Telegram", value=cfg_inicial.get("telegram_token", ""), type="password")
            btn_tg = gr.Button("Conectar / Reiniciar Telegram", variant="secondary")
            tg_status_out = gr.Textbox(label="Estado Bot", value=tg_estado_inicial, interactive=False)
            btn_tg.click(iniciar_puente_telegram, [tg_token_in], [tg_status_out])

        with gr.Accordion("☁️ 3. Proyectos y Google Drive (Resume)", open=True):
            nom_proj_in = gr.Textbox(label="Nombre del Proyecto Activo", value=cfg_inicial.get("proyecto_activo", "Proyecto_Principal"))
            reanudar_in = gr.Checkbox(value=True, label="Reanudar desde Checkpoint Drive")
            proj_guardados_dd = gr.Dropdown(label="Proyectos en Drive", choices=proyectos_mgr.listar_proyectos_guardados() or ["Proyecto_Principal"])
            btn_ref_proj = gr.Button("Actualizar Lista de Proyectos", size="sm")
            btn_ref_proj.click(ui_refrescar_proyectos, [], [proj_guardados_dd])
            proj_guardados_dd.change(lambda x: x, [proj_guardados_dd], [nom_proj_in])

        with gr.Accordion("⚡ 4. Motor C++ y Servidor MCP", open=False):
            gr.Markdown(f"**Servidor MCP:** `{mcp_srv.mcp.name}`\n**Optimizador C++:** Activación bajo demanda.")
            btn_free_mem = gr.Button("Liberar VRAM / RAM Ahora", size="sm")
            mem_status = gr.Textbox(label="Estado Memoria", interactive=False)
            btn_free_mem.click(ui_limpiar_memoria_cpp, [], [mem_status])

    # Parte 3/5: Estaciones de Trabajo Desplegables (Direccion, Voces y Postproduccion)
    with gr.Row():
        with gr.Column(scale=5):
            with gr.Accordion("🎙️ ESTACIÓN 1: Director Conversacional, Guion y Lector PDF", open=True):
                with gr.Row():
                    mic_in = gr.Audio(label="Hablar al Director (Micrófono)", sources=["microphone"], type="filepath")
                    pdf_in = gr.File(label="Importar Guion PDF (Multi-Formato)", file_types=[".pdf"])
                orden_in = gr.Textbox(
                    label="Instrucción, Idea o Guion Completo (Personajes y duración ilimitados)",
                    lines=4,
                    placeholder="Escribe tu historia o habla por micrófono. Si dura más de 10 min, se dividirá automáticamente en bloques de 10 min respaldados en Google Drive..."
                )
                with gr.Row():
                    pasos_in = gr.Slider(6, 35, value=10 if DEVICE=="cpu" else 25, step=1, label="Calidad Visual (Pasos SDXL)")
                    aud_lang = gr.Dropdown(["es", "en"], value="es", label="Idioma de Voz")
                    subs_mode = gr.Dropdown(["Ambos (ES + EN)", "Espanol", "Ingles", "Sin Subtitulos"], value="Ambos (ES + EN)", label="Subtítulos")

                btn_run = gr.Button("🚀 PRODUCIR / REANUDAR PELÍCULA COMPLETA", variant="primary", size="lg")

                with gr.Row():
                    resp_txt_out = gr.Textbox(label="Respuesta del Agente Director", lines=2)
                    resp_voz_out = gr.Audio(label="Voz del Agente Director", autoplay=True)

            with gr.Accordion("🗣️ ESTACIÓN 2: Reparto Ilimitado, Voz Propia y Catálogo Kokoro-82M", open=False):
                gr.Markdown("Si **no asignas una voz** a un personaje, el Agente IA le asignará una automáticamente según su rol.")
                with gr.Row():
                    p_nom = gr.Textbox(label="Nombre del Personaje", placeholder="Ej: Narrador, Elena, Comandante...")
                    v_es_dd = gr.Dropdown(list(VOCES_DISPONIBLES.keys()), value="ES (Mexico) - Jorge (Hombre Profundo)", label="Voz Español")
                    v_en_dd = gr.Dropdown(list(VOCES_DISPONIBLES.keys()), value="EN (US) - Brian (Hombre Profundo)", label="Voz Inglés")
                voz_propia_in = gr.Audio(label="Grabar o Subir Tu Propia Voz (Opcional)", sources=["microphone", "upload"], type="filepath")
                with gr.Row():
                    vel_s = gr.Slider(-40, 40, value=0, step=5, label="Velocidad (%)")
                    tono_s = gr.Slider(-25, 25, value=0, step=1, label="Tono (Hz)")
                    vol_s = gr.Slider(-30, 30, value=0, step=5, label="Volumen (%)")
                with gr.Row():
                    test_txt = gr.Textbox(label="Frase de Prueba (Sin nombre de personaje)", value="Mi voz está lista para entrar en escena.")
                    btn_save_v = gr.Button("Guardar y Probar Voz", variant="secondary")
                with gr.Row():
                    msg_v = gr.Textbox(label="Estado Perfil")
                    aud_test = gr.Audio(label="Muestra de Voz")

                with gr.Accordion("Ver Perfiles Guardados y Catálogo Kokoro-82M (54 Voces Descritas)", open=False):
                    perfiles_box = gr.Code(label="Perfiles Activos (Manuales + Auto-Casting IA)", value=json.dumps(casting.gestor.perfiles, indent=2, ensure_ascii=False), language="json", lines=8)
                    gr.Dataframe(headers=["ID", "Nombre", "Idioma", "Género", "Descripción de Voz"], value=tabla_kokoro, interactive=False)

                btn_save_v.click(ui_guardar_voz, [p_nom, v_es_dd, v_en_dd, vel_s, tono_s, vol_s, voz_propia_in, test_txt], [msg_v, aud_test, perfiles_box])

            with gr.Accordion("✂️ ESTACIÓN 3: Sala de Postproducción (Re-Editar Idioma y Subtítulos)", open=False):
                gr.Markdown("Cambia el idioma del doblaje (**Español o Inglés**) o los subtítulos de la última historia generada al instante sin volver a renderizar imágenes.")
                with gr.Row():
                    ed_lang = gr.Radio(["es", "en"], value="en", label="Pista de Audio")
                    ed_subs = gr.Dropdown(["Ambos (ES + EN)", "Espanol", "Ingles", "Sin Subtitulos"], value="Ambos (ES + EN)", label="Subtítulos")
                    btn_ed = gr.Button("Exportar Nueva Edición MP4", variant="secondary")
                ed_status = gr.Textbox(label="Estado Postproducción")

        # Parte 4/5: Monitor de Programa, Linea de Tiempo y Descargas
        with gr.Column(scale=6):
            with gr.Accordion("📺 MONITOR DE PROGRAMA Y EXPORTACIÓN FINAL", open=True):
                video_out = gr.Video(label="Monitor Principal de Video (MP4 Sincronizado)")
                with gr.Row():
                    zip_out = gr.File(label="📦 Paquete Completo (.ZIP)")
                    pdf_out = gr.File(label="📄 Guion y Biblia Visual (.PDF)")
                    srt_out = gr.File(label="💬 Subtítulos (.SRT)")

            with gr.Accordion("🎞️ LÍNEA DE TIEMPO VISUAL (CUADROS COHERENTES)", open=True):
                galeria_out = gr.Gallery(label="Secuencia Encadenada Escena a Escena", columns=4, height=230)

            with gr.Accordion("📋 BITÁCORA DE AUDITORÍA, BLOQUES 10 MIN Y PLAN JSON", open=False):
                bitacora_out = gr.Textbox(label="Registro de Decisiones MCP, Auditoría de Calidad y Respaldo Drive", lines=7)
                plan_json_out = gr.Code(label="Plan Cinematográfico Estructurado (JSON)", language="json", lines=10)

    btn_run.click(
        ui_ejecutar_estudio,
        [api_in, openai_in, nom_proj_in, reanudar_in, mic_in, pdf_in, orden_in, pasos_in, aud_lang, subs_mode],
        [resp_txt_out, resp_voz_out, bitacora_out, plan_json_out, galeria_out, video_out, zip_out, pdf_out, srt_out]
    )
    btn_ed.click(ui_reexportar, [ed_lang, ed_subs], [video_out, srt_out, ed_status])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=18789, share=False, theme=gr.themes.Soft())
