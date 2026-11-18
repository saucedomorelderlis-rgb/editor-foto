from datetime import datetime
import soundfile as sf
from kokoro_onnx import Kokoro
from config_rutas import MODELS_DIR, AUDIO_OUT_DIR

KOKORO_DIR = MODELS_DIR / "kokoro"
MODEL_PATH = KOKORO_DIR / "kokoro-v1.0.onnx"
VOICES_PATH = KOKORO_DIR / "voices-v1.0.bin"

CATALOGO_KOKORO_DESCRITO = {
    "ef_dora": {"nombre": "Dora (Espanol)", "idioma": "es", "genero": "F", "descripcion": "Voz femenina en espanol, calida, expresiva y clara. Ideal para protagonistas y narracion cercana."},
    "em_alex": {"nombre": "Alex (Espanol)", "idioma": "es", "genero": "M", "descripcion": "Voz masculina en espanol, equilibrada, natural y firme. Excelente para narradores y personajes principales."},
    "em_santa": {"nombre": "Santa / Sabio (Espanol)", "idioma": "es", "genero": "M", "descripcion": "Voz masculina en espanol profunda, grave y pausada. Perfecta para mentores, ancianos o historias epicas."},
    "af_heart": {"nombre": "Heart (Ingles US)", "idioma": "en-us", "genero": "F", "descripcion": "Voz femenina estadounidense muy emotiva, natural y cinematografica. La mas realista para drama."},
    "af_bella": {"nombre": "Bella (Ingles US)", "idioma": "en-us", "genero": "F", "descripcion": "Voz femenina estadounidense suave, dulce y juvenil."},
    "af_nicole": {"nombre": "Nicole (Ingles US)", "idioma": "en-us", "genero": "F", "descripcion": "Voz femenina en tono susurrante, intimo y misterioso. Ideal para suspenso."},
    "am_adam": {"nombre": "Adam (Ingles US)", "idioma": "en-us", "genero": "M", "descripcion": "Voz masculina estadounidense grave, resonante y autoritaria. Ideal para trailers y accion."},
    "am_michael": {"nombre": "Michael (Ingles US)", "idioma": "en-us", "genero": "M", "descripcion": "Voz masculina estadounidense profesional, limpia y de documental."},
    "bf_emma": {"nombre": "Emma (Ingles UK)", "idioma": "en-gb", "genero": "F", "descripcion": "Voz femenina britanica elegante, articulada y sofisticada."},
    "bm_george": {"nombre": "George (Ingles UK)", "idioma": "en-gb", "genero": "M", "descripcion": "Voz masculina britanica clasica, teatral y con autoridad historica."}
}

class MotorKokoroOpenSource:
    def __init__(self):
        self.kokoro = None

    def cargar(self):
        if self.kokoro is None and MODEL_PATH.exists() and VOICES_PATH.exists():
            self.kokoro = Kokoro(str(MODEL_PATH), str(VOICES_PATH))

    def listar_voces_con_descripcion(self):
        return CATALOGO_KOKORO_DESCRITO

    def sintetizar(self, texto, voice_id="em_alex", velocidad=1.0, lang="es"):
        self.cargar()
        samples, sample_rate = self.kokoro.create(texto, voice=voice_id, speed=float(velocidad), lang=lang)
        salida = AUDIO_OUT_DIR / f"kokoro_{voice_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.wav"
        sf.write(str(salida), samples, sample_rate)
        return str(salida)
