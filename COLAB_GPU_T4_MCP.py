# ==============================================================================
# DESPLIEGUE EN GOOGLE COLAB (GPU T4 + GITHUB + GOOGLE DRIVE + CLOUDFLARE)
# ==============================================================================
from google.colab import drive
drive.mount('/content/drive')

# 1. Clonar o actualizar tu repositorio desde GitHub (CAMBIA TU_USUARIO por tu usuario real de GitHub)
GITHUB_REPO = "https://github.com"

!rm -rf /content/estudio
!git clone {GITHUB_REPO} /content/estudio
%cd /content/estudio

# 2. Enlazar tus modelos pesados (.safetensors) y configuracion desde Google Drive sin duplicarlos
!ln -sf "/content/drive/MyDrive/editor_foto/sd_xl_base_1.0.safetensors" /content/estudio/sd_xl_base_1.0.safetensors
!ln -sf "/content/drive/MyDrive/editor_foto/sd_xl_offset_example-lora_1.0.safetensors" /content/estudio/sd_xl_offset_example-lora_1.0.safetensors
!cp -f "/content/drive/MyDrive/editor_foto/config_estudio.json" /content/estudio/proyectos/config_estudio.json 2>/dev/null || true

# 3. Descargar pesos ligeros de Kokoro-82M en la nube
!mkdir -p modelos/kokoro
!wget -q -O modelos/kokoro/kokoro-v1.0.onnx https://github.com
!wget -q -O modelos/kokoro/voices-v1.0.bin https://github.com

# 4. Instalar dependencias manteniendo PyTorch CUDA nativo de GPU T4 y compilar C++
!grep -vE "^(torch|torchvision|torchaudio)$" requirements.txt > req_colab.txt
!pip install -q -r req_colab.txt
!g++ -O3 -shared -fPIC bin_cpp/optimizador.cpp -o bin_cpp/optimizador_linux.so

# 5. Exponer puerto 18789 con Cloudflare Tunnel
!curl -sL --output cloudflared https://github.com
!chmod +x cloudflared

import subprocess, time, re
get_ipython().system_raw('python3 src/app_web.py &')
time.sleep(6)

tunel = subprocess.Popen(['./cloudflared', 'tunnel', '--url', 'http://localhost:18789'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
for linea in tunel.stdout:
    match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', linea)
    if match:
        print("\n==================================================================")
        print("ESTUDIO CINE IA (GITHUB + GPU T4) ACTIVO EN:", match.group(0))
        print("==================================================================\n")
        break

