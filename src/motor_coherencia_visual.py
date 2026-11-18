from motor_imagen import MotorVisualSDXL

# Sub-parte 19.1: Continuidad visual estricta cuadro a cuadro y entre bloques de 10 min
class MotorCoherenciaVisual:
    def __init__(self):
        self.sdxl = MotorVisualSDXL()
        self.ultimo_fotograma_valido = ""
        self.semilla_maestra = 4200

    def reiniciar_secuencia(self, semilla_base=4200):
        self.ultimo_fotograma_valido = ""
        self.semilla_maestra = int(semilla_base)

    def generar_escena_coherente(self, biblia_visual, prompt_escena, accion_narrada="", indice_escena=1, fuerza_coherencia=0.64, pasos=20):
        # Combina Biblia Visual fija + accion especifica + contexto narrado
        contexto_nar = f", depicting: {accion_narrada[:120]}" if accion_narrada else ""
        prompt_blindado = f"{biblia_visual}, {prompt_escena}{contexto_nar}, consistent character face and clothing, same lighting, cinematic continuity"

        ruta_actual = self.sdxl.generar_fotograma(
            prompt=prompt_blindado,
            ruta_img_previa=self.ultimo_fotograma_valido if self.ultimo_fotograma_valido else None,
            fuerza_coherencia=fuerza_coherencia,
            pasos=pasos,
            semilla=self.semilla_maestra + int(indice_escena)
        )

        # Aplicar armonizacion cromatica en C++ portable si existe imagen previa
        if self.ultimo_fotograma_valido:
            try:
                from puente_cpp_lazy import MotorOptimizadorCPP
                MotorOptimizadorCPP().armonizar_coherencia_color(ruta_actual, self.ultimo_fotograma_valido, factor=0.14)
            except Exception:
                pass

        self.ultimo_fotograma_valido = ruta_actual
        return ruta_actual

    def liberar_recursos(self):
        self.sdxl.liberar_memoria()
