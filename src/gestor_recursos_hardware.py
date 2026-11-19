import os
import gc
import psutil
import torch

class GestorRecursosHardware:
    @staticmethod
    def obtener_estado_sistema():
        ram = psutil.virtual_memory()
        ram_total_gb = ram.total / (1024 ** 3)
        ram_disp_gb = ram.available / (1024 ** 3)
        nucleos_cpu = os.cpu_count() or 4

        if torch.cuda.is_available():
            vram_total_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            gpu_nombre = torch.cuda.get_device_name(0)
            info_gpu = f"{gpu_nombre} ({vram_total_gb:.1f} GB VRAM Exclusiva Imagenes)"
        else:
            info_gpu = "Modo CPU Local (Sin GPU dedicada)"

        return {
            "nucleos_cpu": nucleos_cpu,
            "ram_total_gb": round(ram_total_gb, 2),
            "ram_disponible_gb": round(ram_disp_gb, 2),
            "gpu_info": info_gpu
        }

    @staticmethod
    def configurar_hilos_cpu_ram():
        """Asigna todos los nucleos CPU y RAM normal para Audio, Voz, PDF, Telegram y Video."""
        nucleos = os.cpu_count() or 4
        os.environ["OMP_NUM_THREADS"] = str(nucleos)
        os.environ["MKL_NUM_THREADS"] = str(nucleos)
        torch.set_num_threads(nucleos)
        return nucleos

    @staticmethod
    def preparar_gpu_solo_imagenes():
        """Activa la GPU/VRAM exclusivamente antes de generar fotogramas SDXL."""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            return "cuda"
        return "cpu"

    @staticmethod
    def liberar_gpu_tras_imagenes():
        """Vacia por completo la VRAM grafica al terminar las imagenes para dejarla libre."""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
