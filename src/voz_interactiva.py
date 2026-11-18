import json
from google import genai
import servidor_mcp as mcp_tools

class VozInteractivaAgente:
    # Sub-parte 10.1: Escucha y transcripcion multimodal del usuario
    def escuchar_audio(self, api_key, ruta_audio):
        """Escucha una nota de voz o grabacion de microfono y devuelve la transcripcion exacta."""
        client = genai.Client(api_key=api_key.strip(), http_options={"api_version": "v1beta"})
        archivo = client.files.upload(file=str(ruta_audio))
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                "Transcribe con exactitud lo que dice el usuario en este audio. Devuelve unicamente el texto hablado.",
                archivo
            ]
        )
        return resp.text.strip()

    # Sub-parte 10.2: Respuesta hablada del propio Agente Director
    def hablar_respuesta(self, texto_respuesta, idioma="es"):
        """Genera la respuesta hablada con la voz del Agente Director."""
        res = json.loads(mcp_tools.mcp_sintetizar_voz_dialogo(
            personaje="Agente_Director",
            dialogo_limpio=texto_respuesta,
            idioma=idioma,
            genero="M",
            tono_hz=-2
        ))
        return res["audio"]
