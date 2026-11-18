import json
from datetime import datetime
from fpdf import FPDF
from openai import OpenAI
from config_rutas import DOCS_OUT_DIR

def _limpiar_latin1(texto):
    """Evita errores de codificacion con tildes o caracteres especiales en fuentes estandar PDF."""
    return str(texto).encode("latin-1", errors="replace").decode("latin-1")

# Sub-parte 16.1: Generacion de PDFs estructurados del guion y plan de rodaje
class ExportadorGuionPDF:
    def exportar_plan_a_pdf(self, plan_dict, nombre_base="guion_produccion"):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        titulo = _limpiar_latin1(plan_dict.get("titulo", "Guion de Produccion Audiovisual"))
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, titulo, ln=True, align="C")
        pdf.ln(4)

        biblia = _limpiar_latin1(plan_dict.get("biblia_visual", ""))
        if biblia:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 8, "BIBLIA VISUAL Y CONTINUIDAD:", ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 6, biblia)
            pdf.ln(4)

        for esc in plan_dict.get("escenas", []):
            num = esc.get("escena", 1)
            pers = _limpiar_latin1(esc.get("personaje", "Narrador"))
            txt_es = _limpiar_latin1(esc.get("texto_es", ""))
            txt_en = _limpiar_latin1(esc.get("texto_en", ""))
            prompt_v = _limpiar_latin1(esc.get("prompt_imagen", ""))

            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 8, f"ESCENA {num} - PERSONAJE: {pers.upper()}", ln=True)

            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 6, f"[ES]: {txt_es}")
            if txt_en:
                pdf.multi_cell(0, 6, f"[EN]: {txt_en}")
            pdf.set_font("Helvetica", "I", 9)
            pdf.multi_cell(0, 5, f"Direccion Visual: {prompt_v}")
            pdf.ln(3)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta_pdf = DOCS_OUT_DIR / f"{nombre_base}_{ts}.pdf"
        pdf.output(str(ruta_pdf))
        return str(ruta_pdf)

def redactar_con_chatgpt_opcional(openai_api_key, idea_o_borrador):
    if not openai_api_key or not openai_api_key.strip():
        return idea_o_borrador
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_api_key.strip())
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Eres un guionista literario profesional. Desarrolla una historia atrapante con dialogos naturales diferenciados por personaje (Narrador: ..., Personaje: ...)."
                },
                {"role": "user", "content": idea_o_borrador}
            ],
            temperature=0.75
        )
        return resp.choices.message.content.strip()
    except Exception as e:
        print(f"[Aviso ChatGPT Opcional] Continuando solo con Gemini: {e}")
        return idea_o_borrador
