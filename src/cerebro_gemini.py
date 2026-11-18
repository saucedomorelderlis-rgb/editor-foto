import json
from google import genai
from google.genai import types

class CerebroGemini:
    def orquestar_historia(self, api_key, guion_o_idea, num_escenas=4, estilo_visual="cinematic film still, photorealistic, 8k, consistent lighting"):
        client = genai.Client(
            api_key=api_key.strip(),
            http_options={"api_version": "v1beta"}
        )
        instrucciones = f"""
Eres el director creativo y guionista de un estudio de historias alternativas y ficcion.
Convierte la entrada del usuario en {num_escenas} escenas totalmente coherentes entre si.
REGLAS OBLIGATORIAS:
1. 'biblia_visual': Define rasgos fijos de los personajes (ropa, edad, rostro, colores) y del mundo para que todas las escenas parezcan de la misma pelicula.
2. 'texto_es' y 'texto_en': Escribe UNICAMENTE lo que dice el personaje o narrador. JAMAS pongas el nombre del personaje al inicio del texto (ejemplo incorrecto: 'Elena: Hola', ejemplo correcto: 'Hola').
3. 'prompt_imagen': En INGLES, incluye siempre los detalles de la 'biblia_visual' + la accion puntual de esa escena + continuidad visual con la escena previa.
Devuelve SOLO un JSON valido:
{{
  "titulo": "Titulo",
  "biblia_visual": "Descripcion fija",
  "personajes": ["Narrador", "Personaje2"],
  "escenas": [
    {{
      "escena": 1,
      "personaje": "Narrador",
      "texto_es": "Dialogo limpio en espanol",
      "texto_en": "Clean dialogue in English",
      "prompt_imagen": "Detailed English prompt for SDXL"
    }}
  ]
}}
"""
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Estilo visual: {estilo_visual}\n\nGuion o idea del usuario:\n{guion_o_idea}",
            config=types.GenerateContentConfig(
                system_instruction=instrucciones,
                response_mime_type="application/json",
                temperature=0.65
            )
        )
        return json.loads(resp.text)
