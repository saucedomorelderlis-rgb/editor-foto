from motor_imagen import MotorImagenSDXL
from motor_voz import MotorVozChatTTS
from motor_video import MotorVideoSync

class EstudioMultimodal:
    def __init__(self):
        self.motor_img = MotorImagenSDXL()
        self.motor_voz = MotorVozChatTTS()
        self.motor_vid = MotorVideoSync()

    def crear_escena_completa(self, prompt_imagen, texto_narracion, pasos=20, velocidad_voz=5, semilla_voz=42):
        ruta_img, info_img = self.motor_img.generar(prompt=prompt_imagen, pasos=pasos)
        ruta_aud, info_aud = self.motor_voz.generar(texto=texto_narracion, velocidad=velocidad_voz, semilla=semilla_voz)
        ruta_vid, info_vid = self.motor_vid.combinar_imagen_audio(ruta_img, ruta_aud)
        resumen = f"{info_img} | {info_aud} | {info_vid}"
        return ruta_img, ruta_aud, ruta_vid, resumen

    def unir_existentes(self, ruta_imagen, ruta_audio):
        return self.motor_vid.combinar_imagen_audio(ruta_imagen, ruta_audio)
