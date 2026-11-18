from datetime import datetime
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from motor_subtitulos import MotorSubtitulos
from config_rutas import VIDEO_OUT_DIR

# Sub-parte 22.1: Sincronizacion exacta al milisegundo entre imagen, audio y subtitulos
class SincronizadorPrecisionAV:
    def __init__(self):
        self.subs = MotorSubtitulos()

    def compilar_bloque_sincronizado(self, escenas_bloque, idioma_audio="es", modo_subs="Ambos (ES + EN)", fps=24, nombre_archivo="bloque"):
        clips = []
        srt_lineas = []
        cursor_tiempo = 0.0

        for idx, esc in enumerate(escenas_bloque, start=1):
            ruta_audio = esc["audio_es"] if idioma_audio == "es" else esc["audio_en"]
            aud_clip = AudioFileClip(str(ruta_audio))
            pausa = float(esc.get("pausa_corte", 0.35))
            zoom_factor = float(esc.get("zoom_factor", 0.04))
            duracion_exacta = aud_clip.duration + pausa

            texto_sub = self.subs.obtener_texto_subtitulo(esc, modo_subs)
            ruta_frame_sub = self.subs.estampar_en_imagen(esc["imagen"], texto_sub)

            clip = ImageClip(str(ruta_frame_sub)).with_duration(duracion_exacta).with_audio(aud_clip)
            if zoom_factor > 0:
                clip = clip.resized(lambda t, d=duracion_exacta, z=zoom_factor: 1.0 + z * (t / d))

            clips.append(clip)

            ts_inicio = self.subs.formatear_tiempo_srt(cursor_tiempo)
            ts_fin = self.subs.formatear_tiempo_srt(cursor_tiempo + duracion_exacta)
            contenido_srt = texto_sub if texto_sub else esc.get("texto_es", "")
            srt_lineas.append(f"{idx}\n{ts_inicio} --> {ts_fin}\n{contenido_srt}\n")
            cursor_tiempo += duracion_exacta

        video_bloque = concatenate_videoclips(clips, method="compose")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        mp4_salida = VIDEO_OUT_DIR / f"{nombre_archivo}_{idioma_audio}_{ts}.mp4"
        srt_salida = VIDEO_OUT_DIR / f"{nombre_archivo}_{idioma_audio}_{ts}.srt"

        video_bloque.write_videofile(str(mp4_salida), fps=fps, codec="libx264", audio_codec="aac", logger=None)
        srt_salida.write_text("\n".join(srt_lineas), encoding="utf-8")

        for c in clips:
            c.close()
        video_bloque.close()
        return str(mp4_salida), str(srt_salida)
