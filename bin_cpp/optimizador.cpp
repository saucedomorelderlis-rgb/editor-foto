#include <cmath>
#include <cstdint>
#include <algorithm>

#ifdef _WIN32
  #define EXPORT_API extern "C" __declspec(dllexport)
#else
  #define EXPORT_API extern "C" __attribute__((visibility("default")))
#endif

// Normaliza un buffer de audio float32 al volumen objetivo y suaviza clics
EXPORT_API void optimizar_audio_f32(float* samples, int length, float target_peak) {
    if (!samples || length <= 0) return;
    float max_val = 0.0f;
    for (int i = 0; i < length; ++i) {
        float abs_v = std::fabs(samples[i]);
        if (abs_v > max_val) max_val = abs_v;
    }
    if (max_val > 1e-6f) {
        float gain = target_peak / max_val;
        for (int i = 0; i < length; ++i) {
            samples[i] = std::clamp(samples[i] * gain, -1.0f, 1.0f);
        }
    }
}

// Armoniza los canales RGB de la imagen actual con la imagen anterior para coherencia visual
EXPORT_API void armonizar_color_escena_rgb(uint8_t* img_actual, const uint8_t* img_anterior, int total_bytes, float factor_coherencia) {
    if (!img_actual || !img_anterior || total_bytes <= 0) return;
    float alpha = std::clamp(factor_coherencia, 0.0f, 0.45f);
    float beta = 1.0f - alpha;
    for (int i = 0; i < total_bytes; ++i) {
        float blended = (img_actual[i] * beta) + (img_anterior[i] * alpha);
        img_actual[i] = static_cast<uint8_t>(std::clamp(blended, 0.0f, 255.0f));
    }
}
