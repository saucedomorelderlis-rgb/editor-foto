import gc
from datetime import datetime
from PIL import Image
import torch
from diffusers import StableDiffusionXLPipeline, StableDiffusionXLImg2ImgPipeline
from config_rutas import SDXL_BASE_PATH, SDXL_LORA_PATH, IMG_OUT_DIR, DEVICE, DTYPE

class MotorVisualSDXL:
    def __init__(self):
        self.txt2img = None
        self.img2img = None

    def activar_bajo_demanda(self, usar_lora=True, escala_lora=0.75):
        if self.txt2img is None:
            print(f"[SDXL] Activando motor visual en {DEVICE.upper()}...")
            self.txt2img = StableDiffusionXLPipeline.from_single_file(
                str(SDXL_BASE_PATH),
                torch_dtype=DTYPE,
                use_safetensors=True
            )
            if usar_lora and SDXL_LORA_PATH.exists():
                self.txt2img.load_lora_weights(str(SDXL_LORA_PATH.parent), weight_name=SDXL_LORA_PATH.name)
                self.txt2img.fuse_lora(lora_scale=escala_lora)

            if DEVICE == "cuda":
                self.txt2img.enable_model_cpu_offload()
            else:
                self.txt2img.to("cpu")

            self.img2img = StableDiffusionXLImg2ImgPipeline(
                vae=self.txt2img.vae,
                text_encoder=self.txt2img.text_encoder,
                text_encoder_2=self.txt2img.text_encoder_2,
                tokenizer=self.txt2img.tokenizer,
                tokenizer_2=self.txt2img.tokenizer_2,
                unet=self.txt2img.unet,
                scheduler=self.txt2img.scheduler,
            )

    def liberar_memoria(self):
        """Descarga los pesos de VRAM/RAM cuando termina el bloque visual."""
        self.img2img = None
        self.txt2img = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def generar_fotograma(self, prompt, ruta_img_previa=None, fuerza_coherencia=0.65, pasos=20, ancho=1024, alto=1024, semilla=777):
        self.activar_bajo_demanda()
        if DEVICE == "cpu":
            ancho, alto = 512, 512
            pasos = min(int(pasos), 8)

        gen = torch.Generator(device=DEVICE).manual_seed(int(semilla))
        neg = "blurry, deformed, bad anatomy, extra fingers, watermark, text, logo, inconsistent face, lowres"

        if ruta_img_previa:
            base_img = Image.open(ruta_img_previa).convert("RGB").resize((ancho, alto))
            img = self.img2img(
                prompt=prompt,
                negative_prompt=neg,
                image=base_img,
                strength=float(fuerza_coherencia),
                num_inference_steps=int(pasos),
                guidance_scale=7.5,
                generator=gen
            ).images[0]
        else:
            img = self.txt2img(
                prompt=prompt,
                negative_prompt=neg,
                num_inference_steps=int(pasos),
                width=ancho,
                height=alto,
                guidance_scale=7.5,
                generator=gen
            ).images[0]

        salida = IMG_OUT_DIR / f"frame_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
        img.save(salida)
        return str(salida)
