import asyncio
import threading
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from agente_director import AgenteDirectorAutonomo
from config_rutas import cargar_config, guardar_config, AUDIO_OUT_DIR, DOCS_OUT_DIR, DEVICE

agente_tg = AgenteDirectorAutonomo()
_hilo_tg = None

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    guardar_config(telegram_chat_id=update.effective_chat.id)
    await update.message.reply_text(
        f"Agente Director de Cine IA conectado ({DEVICE.upper()}).\n"
        "Enviame texto, una NOTA DE VOZ o un archivo PDF con tu guion. Te respondere por voz y te enviare el video MP4 terminado."
    )

async def manejar_entrada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = cargar_config()
    api_key = cfg.get("gemini_api_key", "")
    if not api_key:
        await update.message.reply_text("Configura primero tu Gemini API Key en la interfaz web.")
        return
    guardar_config(telegram_chat_id=update.effective_chat.id)
    pasos = 10 if DEVICE == "cpu" else 22
    texto_orden = ""
    if update.message.voice or update.message.audio:
        await update.message.reply_text("Escuchando tu nota de voz...")
        f_tg = await (update.message.voice or update.message.audio).get_file()
        ruta_ogg = AUDIO_OUT_DIR / f"tg_voz_{update.message.message_id}.ogg"
        await f_tg.download_to_drive(str(ruta_ogg))
        texto_orden = await asyncio.to_thread(agente_tg.voz_agente.escuchar_audio, api_key, ruta_ogg)
        await update.message.reply_text(f"Entendi: \"{texto_orden}\"")
    elif update.message.document and update.message.document.file_name.lower().endswith(".pdf"):
        await update.message.reply_text("Recibi tu guion PDF. Analizando estructura y personajes...")
        f_doc = await update.message.document.get_file()
        ruta_pdf = DOCS_OUT_DIR / update.message.document.file_name
        await f_doc.download_to_drive(str(ruta_pdf))
        from lector_guiones_pdf import LectorGuionesPDF
        datos_pdf = await asyncio.to_thread(LectorGuionesPDF().analizar_pdf, api_key, ruta_pdf)
        texto_orden = f"Produce un video basado en este guion extraido del PDF:\n{datos_pdf}"
    else:
        texto_orden = update.message.text or ""
    if not texto_orden.strip():
        return
    await update.message.reply_text("Agente Director MCP trabajando en tu solicitud...")
    res = await asyncio.to_thread(
        agente_tg.procesar_interaccion, api_key, texto_orden, cfg.get("proyecto_activo", "Proyecto_Telegram"), pasos, "es", "Ambos (ES + EN)", cfg.get("openai_api_key", ""), True
    )
    resp_txt, ruta_voz = res, res
    ruta_mp4 = res if len(res) > 5 else None
    ruta_zip = res if len(res) > 6 else None
    if ruta_voz and Path(ruta_voz).exists():
        with open(ruta_voz, "rb") as vf:
            await update.message.reply_voice(voice=vf, caption=resp_txt[:1000])
    else:
        await update.message.reply_text(resp_txt)
    if ruta_mp4 and Path(ruta_mp4).exists():
        with open(ruta_mp4, "rb") as vid:
            await update.message.reply_video(video=vid, caption="Video renderizado con audio y subtitulos.")
    if ruta_zip and Path(ruta_zip).exists():
        with open(ruta_zip, "rb") as zf:
            await update.message.reply_document(document=zf, caption="Paquete completo ZIP del proyecto.")

def iniciar_puente_telegram(token):
    global _hilo_tg
    if not token or not token.strip():
        return "Ingresa un Token de Bot de Telegram valido."
    guardar_config(telegram_token=token)
    if _hilo_tg and _hilo_tg.is_alive():
        return "Puente Telegram ya esta activo."
    def _worker():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        app = Application.builder().token(token.strip()).build()
        app.add_handler(CommandHandler("start", cmd_start))
        app.add_handler(MessageHandler((filters.TEXT | filters.VOICE | filters.AUDIO | filters.Document.ALL) & ~filters.COMMAND, manejar_entrada))
        app.run_polling(drop_pending_updates=True, stop_signals=None)
    _hilo_tg = threading.Thread(target=_worker, daemon=True)
    _hilo_tg.start()
    return "Puente Telegram ACTIVADO (Texto, Notas de Voz y PDFs)."
