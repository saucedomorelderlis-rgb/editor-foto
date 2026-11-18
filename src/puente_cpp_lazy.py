import gc
import ctypes
import platform
import subprocess
import numpy as np
import torch
from PIL import Image
import soundfile as sf
from config_rutas import BASE_DIR

BIN_CPP_DIR = BASE_DIR / "bin_cpp"
CPP_SRC = BIN_CPP_DIR / "optimizador.cpp"

class MotorOptimizadorCPP:
    def __init__(self):
        self.lib = None
        self.ext = ".dll" if platform.system() == "Windows" else ".so"
        self.bin_path = BIN_CPP_DIR / f"optimizador_{platform.system().lower()}{self.ext}"

    def _asegurar_compilado_y_cargar(self):
        if self.lib is not None:
            return True
        if not self.bin_path.exists() and CPP_SRC.exists():
            try:
                subprocess.run(
                    ["g++", "-O3", "-shared", "-fPIC", str(CPP_SRC), "-o", str(self.bin_path)],
                    check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            except Exception:
                return False
        if self.bin_path.exists():
            self.lib = ctypes.CDLL(str(self.bin_path))
            self.lib.optimizar_audio_f32.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_int, ctypes.c_float]
            self.lib.armonizar_color_escena_rgb.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ctypes.c_int, ctypes.c_float]
            return True
        return False

    def descargar_de_memoria(self):
        """Libera el motor C++ y limpia RAM/VRAM cuando deja de usarse."""
        self.lib = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def optimizar_pista_audio(self, ruta_wav, pico_objetivo=0.92):
        data, sr = sf.read(str(ruta_wav), dtype="float32")
        if self._asegurar_compilado_y_cargar():
            flat = np.ascontiguousarray(data.reshape(-1), dtype=np.float32)
            self.lib.optimizar_audio_f32(flat.ctypes.data_as(ctypes.POINTER(ctypes.c_float)), flat.size, ctypes.c_float(pico_objetivo))
            data = flat.reshape(data.shape)
        else:
            max_v = np.max(np.abs(data))
            if max_v > 1e-6:
                data = np.clip(data * (pico_objetivo / max_v), -1.0, 1.0)
        sf.write(str(ruta_wav), data, sr)
        self.descargar_de_memoria()
        return str(ruta_wav)

    def armonizar_coherencia_color(self, ruta_img_actual, ruta_img_anterior, factor=0.18):
        if not ruta_img_anterior:
            return str(ruta_img_actual)
        img_act = Image.open(ruta_img_actual).convert("RGB")
        img_ant = Image.open(ruta_img_anterior).convert("RGB").resize(img_act.size)
        arr_act = np.ascontiguousarray(np.array(img_act, dtype=np.uint8))
        arr_ant = np.ascontiguousarray(np.array(img_ant, dtype=np.uint8))

        if self._asegurar_compilado_y_cargar():
            self.lib.armonizar_color_escena_rgb(
                arr_act.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
                arr_ant.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
                arr_act.size,
                ctypes.c_float(factor)
            )
        else:
            arr_act = np.clip(arr_act * (1.0 - factor) + arr_ant * factor, 0, 255).astype(np.uint8)

        Image.fromarray(arr_act).save(ruta_img_actual)
        self.descargar_de_memoria()
        return str(ruta_img_actual)

class GestorBajoDemanda:
    """Activa un modulo pesado solo durante su ejecucion y libera VRAM/RAM inmediatamente despues."""
    @staticmethod
    def ejecutar_y_liberar(funcion, *args, **kwargs):
        try:
            return funcion(*args, **kwargs)
        finally:
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
