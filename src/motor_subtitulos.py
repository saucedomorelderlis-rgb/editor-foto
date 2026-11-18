from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from config_rutas import IMG_OUT_DIR

class MotorSubtitulos:
    @staticmethod
    def formatear_tiempo_srt(seg):
        h = int(seg // 3600)
        m = int((seg % 3600) // 60)
        s = int(seg % 60)
        ms = int((seg - int(seg)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    def obtener_texto_subtitulo(self, escena_dict, modo_subs):
        if modo_subs == "Espanol":
            return escena_dict.get("texto_es", "")
        elif modo_subs == "Ingles":
            return escena_dict.get("texto_en", "")
        elif modo_subs == "Ambos (ES + EN)":
            es = escena_dict.get("texto_es", "")
            en = escena_dict.get("texto_en", "")
            return f"{es}\n({en})" if es and en else (es or en)
        return ""

    def estampar_en_imagen(self, ruta_img, texto):
        if not texto or not texto.strip():
            return str(ruta_img)

        img = Image.open(ruta_img).convert("RGBA")
        w, h = img.size
        capa = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(capa)

        tam = max(18, int(h * 0.035))
        try:
            font = ImageFont.truetype("arial.ttf", tam)
        except Exception:
            font = ImageFont.load_default()

        lineas, actual = [], ""
        for parrafo in texto.split("\n"):
            for palabra in parrafo.split():
                prueba = f"{actual} {palabra}".strip()
                if len(prueba) <= 54:
                    actual = prueba
                else:
                    lineas.append(actual)
                    actual = palabra
            if actual:
                lineas.append(actual)
                actual = ""

        bloque = "\n".join(lineas)
        bbox = draw.multiline_textbbox((0, 0), bloque, font=font, align="center")
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (w - tw) // 2
        y = h - th - int(h * 0.05)

        draw.rectangle([x - 14, y - 10, x + tw + 14, y + th + 10], fill=(0, 0, 0, 185), radius=10)
        draw.multiline_text((x, y), bloque, font=font, fill=(255, 255, 255, 255), align="center")

        final = Image.alpha_composite(img, capa).convert("RGB")
        out_img = IMG_OUT_DIR / f"sub_{datetime.now().strftime('%H%M%S_%f')}.png"
        final.save(out_img)
        return str(out_img)
