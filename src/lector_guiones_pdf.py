import json
from pathlib import Path
from pypdf import PdfReader
from google import genai
from google.genai import types

class LectorGuionesPDF:
    # Sub-parte 17.1: Extraccion limpia de texto desde cualquier archivo PDF
    def extraer_texto_bruto(self, ruta_pdf):
        lector = PdfReader(str(ruta_pdf))
        paginas = []
        for idx, page in enumerate(lector.pages, start=1):
            txt = page.extract_text() or ""
            if txt.strip():
                paginas.append(f"--- PAGINA {idx} ---\n{txt.strip()}")
        return "\n\n".join(paginas)

    # Sub-parte 17.2: Reconocimiento multi-formato de guiones y deteccion de personajes
    def analizar_pdf(self, api_key, ruta_pdf):
        texto_pdf = self.extraer_texto_bruto(ruta_pdf)
        if not texto_pdf.strip():
            return json.dumps({"error": "El PDF no contiene texto extraible."}, ensure_ascii=False)

        client = genai.Client(api_key=api_key.strip(), http_options={"api_version": "v1beta"})
        instrucciones = """
Eres un experto analizador de guiones cinematograficos, teatrales y literarios.
El texto proviene de un documento PDF que puede estar escrito en CUALQUIER formato:
- Formato cine Hollywood (NOMBRE EN MAYUSCULAS centrado y dialogo debajo).
- Formato teatral/radio (Personaje: dialogo).
- Prosa narrativa o novela (dialogos con guion largo '—' o comillas + narrador).
- Tablas o escaletas de video.

Tu tarea es:
1. Detectar TODOS los personajes unicos que hablan o narran (ilimitados) y deducir su 'genero' ('M' o 'F').
2. Extraer TODAS las escenas y dialogos en orden cronologico.
3. Separar estrictamente las acotaciones visuales ('accion_visual') del dialogo hablado ('dialogo'). En 'dialogo' NUNCA incluyas el nombre del personaje ni acotaciones entre parentesis.

Devuelve SOLO JSON valido:
{
  "formato_detectado": "cine | teatro | novela | mixto",
  "personajes_detectados": [
    {"nombre": "Narrador", "genero": "M"},
    {"nombre": "Elena", "genero": "F"}
  ],
  "intervenciones": [
    {
      "orden": 1,
      "personaje": "Narrador",
      "genero": "M",
      "dialogo": "Texto limpio que dira la voz",
      "accion_visual": "Descripcion de lo que ocurre en escena para generar la imagen"
    }
  ]
}
"""
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Analiza este guion extraido del PDF:\n\n{texto_pdf[:120000]}",
            config=types.GenerateContentConfig(
                system_instruction=instrucciones,
                response_mime_type="application/json",
                temperature=0.25
            )
        )
        return resp.text
