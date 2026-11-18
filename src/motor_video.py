from datetime import datetime
from pathlib import Path
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from motor_subtitulos import MotorSubtitulos
from config_rutas import VIDEO_OUT_DIR

class SalaEdicionVideo:
    def __init__(self):
        self.subs = MotorSubtitulos()

    def renderizar_secuencia(self, escenas_listas, idioma_audio="es", modo_subs="Ambos (ES + EN)", zoom=True, pausa_escenas=0.35, fps=24, nombre_archivo_base="video"):
        clips = []
        srt_bloques = []
        cursor = 0.0

        for i, esc in enumerate(escenas_listas, start=1):
            aud_path = esc["audio_es"] if idioma_audio == "es" else esc["audio_en"]
            aud_clip = AudioFileClip(str(aud_path))
            dur = aud_clip.duration + float(pausa_escenas)

            texto_sub = self.subs.obtener_texto_subtitulo(esc, modo_subs)
            frame_path = self.subs.estampar_en_imagen(esc["imagen"], texto_sub)

            clip = ImageClip(str(frame_path)).with_duration(dur).with_audio(aud_clip)
            if zoom:
                clip = clip.resized(lambda t, d=dur: 1.0 + 0.04 * (t / d))

            clips.append(clip)

            ts_ini = self.subs.formatear_tiempo_srt(cursor)
            ts_fin = self.subs.formatear_tiempo_srt(cursor + dur)
            srt_texto = texto_sub if texto_sub else esc.get("texto_es", "")
            srt_bloques.append(f"{i}\n{ts_ini} --> {ts_fin}\n{srt_texto}\n")
            cursor += dur

        video_final = concatenate_videoclips(clips, method="compose")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        mp4_out = VIDEO_OUT_DIR / f"{nombre_archivo_base}_{idioma_audio}_{ts}.mp4"
        srt_out = VIDEO_OUT_DIR / f"{nombre_archivo_base}_{idioma_audio}_{ts}.srt"

        video_final.write_videofile(str(mp4_out), fps=fps, codec="libx264", audio_codec="aac", logger=None)
        srt_out.write_text("\n".join(srt_bloques), encoding="utf-8")

        for c in clips:
            c.close()
        video_final.close()
        return str(mp4_out), str(srt_out)
