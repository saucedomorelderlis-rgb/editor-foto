# Sub-parte 21.1: Direccion cinematografica profesional (planos, camara y ritmo)
class DirectorCinematografico:
    PLANOS_PROGRESION = [
        "establishing wide angle shot, sweeping atmospheric perspective",
        "medium shot, rule of thirds composition, cinematic depth of field",
        "over-the-shoulder shot, dramatic rim lighting, shallow focus",
        "close-up portrait shot, expressive facial detail, 85mm lens bokeh"
    ]

    def enriquecer_direccion_escena(self, indice_escena, prompt_base, texto_dialogo):
        texto_lower = str(texto_dialogo).lower()

        # Seleccion inteligente de plano y movimiento de camara segun emocion del guion
        if any(p in texto_lower for p in ["!", "cuidado", "corre", "peligro", "fuego", "ahora", "danger", "run"]):
            plano = "dynamic Dutch angle medium close-up, high contrast action lighting, 35mm anamorphic"
            zoom_factor = 0.07
            pausa_corte = 0.20
        elif any(p in texto_lower for p in ["?", "recuerdo", "nunca", "secreto", "verdad", "secret", "truth"]):
            plano = "intimate close-up shot, soft dramatic chiaroscuro lighting, 85mm lens"
            zoom_factor = 0.05
            pausa_corte = 0.50
        else:
            plano = self.PLANOS_PROGRESION[(int(indice_escena) - 1) % len(self.PLANOS_PROGRESION)]
            zoom_factor = 0.04
            pausa_corte = 0.35

        prompt_dirigido = f"{plano}, {prompt_base}, masterwork cinematography, color graded"
        return {
            "prompt_dirigido": prompt_dirigido,
            "zoom_factor": zoom_factor,
            "pausa_corte": pausa_corte
        }

# Verificacion final de Partes 18, 19, 20 y 21
