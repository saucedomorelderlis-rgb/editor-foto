import asyncio
import traceback
import threading
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from agente_director import AgenteDirectorAutonomo
from config_rutas import cargar_config, guardar_config, AUDIO_OUT_DIR, DOCS_OUT_DIR, DEVICE

agente_tg = AgenteDirectorAutonomo()
_hilo_tg = None

# Parte 4/6: Manejador de errores y comando /start
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("[Error Telegram]:", context.error)
    traceback.print_exc()
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(f"Ocurrio un detalle tecnico al procesar tu mensaje: {context.error}")

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    guardar_config(telegram_chat_id=update.effective_chat.id)
    await update.message.reply_text(
        f"Hola! Soy tu Asistente IA y Director de Cine ({DEVICE.upper()}).\n"
        "Podemos conversar normalmente por texto o nota de voz. Cuando quieras que cree o edite un video, solo pidemelo."
    )

# Parte 5/6: Flujo conversacional y entrega multimedia en Telegram
async def manejar_entrada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    cfg = cargar_config()
    api_key = cfg.get("gemini_api_key", "")
    if not api_key:
        await update.message.reply_text("Configura primero tu Gemini API Key en la interfaz web.")
        return

    guardar_config(telegram_chat_id=update.effective_chat.id)
    pasos = 10 if DEVICE == "cpu" else 22
    texto_orden = ""

    if update.message.voice or update.message.audio:
        f_tg = await (update.message.voice or update.message.audio).get_file()
        ruta_ogg = AUDIO_OUT_DIR / f"tg_voz_{update.message.message_id}.ogg"
        await f_tg.download_to_drive(str(ruta_ogg))
        texto_orden = await asyncio.to_thread(agente_tg.voz_agente.escuchar_audio, api_key, ruta_ogg)
    elif update.message.document and update.message.document.file_name.lower().endswith(".pdf"):
        await update.message.reply_text("Analizando tu documento PDF...")
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

    res = await asyncio.to_thread(
        agente_tg.procesar_interaccion,
        api_key,
        texto_orden,
        cfg.get("proyecto_activo", "Proyecto_Telegram"),
        pasos,
        "es",
        "Ambos (ES + EN)",
        cfg.get("openai_api_key", ""),
        True
    )

    resp_txt = res[0]
    ruta_voz = res[1]
    ruta_mp4 = res[5] if len(res) > 5 else None
    ruta_zip = res[6] if len(res) > 6 else None
    ruta_pdf = res[7] if len(res) > 7 else None

    await update.message.reply_text(resp_txt[:4000])
    if ruta_voz and Path(ruta_voz).exists():
        with open(ruta_voz, "rb") as vf:
            await update.message.reply_voice(voice=vf)

    if ruta_mp4 and Path(ruta_mp4).exists():
        with open(ruta_mp4, "rb") as vid:
            await update.message.reply_video(video=vid, caption="Video renderizado con audio y subtitulos.")
    if ruta_zip and Path(ruta_zip).exists():
        with open(ruta_zip, "rb") as zf:
            await update.message.reply_document(document=zf, caption="Paquete completo comprimido (.ZIP).")
    if ruta_pdf and Path(ruta_pdf).exists():
        with open(ruta_pdf, "rb") as pf:
            await update.message.reply_document(document=pf, caption="Guion y Biblia Visual (.PDF).")

def iniciar_puente_telegram(token):
    global _hilo_tg
    if not token or not token.strip():
        return "Ingresa un Token de Bot de Telegram valido."
    guardar_config(telegram_token=token)
    if _hilo_tg and _hilo_tg.is_alive():
        return "Puente Telegram (@asitem_bot) ya esta activo y escuchando."

    def _worker():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        app = Application.builder().token(token.strip()).build()
        app.add_handler(CommandHandler("start", cmd_start))
        app.add_handler(MessageHandler((filters.TEXT | filters.VOICE | filters.AUDIO | filters.Document.ALL) & ~filters.COMMAND, manejar_entrada))
        app.add_error_handler(error_handler)
        app.run_polling(drop_pending_updates=True, stop_signals=None)

    _hilo_tg = threading.Thread(target=_worker, daemon=True)
    _hilo_tg.start()
    return "Puente Telegram ACTIVADO (@asitem_bot escuchando chat normal y ordenes de video)."
