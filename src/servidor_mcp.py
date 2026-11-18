import json
from mcp.server.mcpserver import MCPServer
from gestor_archivos import GestorArchivosProyecto
from clonador_voz import MotorCastingYVozPropia
from motor_coherencia_visual import MotorCoherenciaVisual
from sincronizador_av import SincronizadorPrecisionAV
from gestor_documentos_guionista import ExportadorGuionPDF
from lector_guiones_pdf import LectorGuionesPDF
from motor_voces_kokoro import MotorKokoroOpenSource
from puente_cpp_lazy import MotorOptimizadorCPP
from config_rutas import HISTORIAL_PROYECTO_PATH

mcp = MCPServer("EstudioCineIA-MCP-26Partes")

archivos_srv = GestorArchivosProyecto()
casting_srv = MotorCastingYVozPropia()
coherencia_srv = MotorCoherenciaVisual()
sync_av_srv = SincronizadorPrecisionAV()
pdf_exp_srv = ExportadorGuionPDF()
pdf_lec_srv = LectorGuionesPDF()
kokoro_srv = MotorKokoroOpenSource()
cpp_srv = MotorOptimizadorCPP()

@mcp.tool()
def mcp_gestionar_archivo(accion: str, nombre_archivo: str, contenido: str = "") -> str:
    """Crea, lee, modifica o lista archivos en la carpeta del proyecto."""
    if accion == "listar":
        return json.dumps({"archivos": archivos_srv.listar_archivos()}, ensure_ascii=False)
    elif accion == "leer":
        return archivos_srv.leer_archivo(nombre_archivo)
    elif accion in ("crear", "modificar"):
        return archivos_srv.escribir_archivo(nombre_archivo, contenido, modo="sobrescribir")
    return "Accion no valida."

@mcp.tool()
def mcp_leer_guion_pdf(api_key: str, ruta_pdf: str) -> str:
    """Lee un documento PDF en cualquier formato de guion e identifica todos sus personajes y dialogos."""
    return pdf_lec_srv.analizar_pdf(api_key, ruta_pdf)

@mcp.tool()
def mcp_exportar_guion_pdf(plan_json_str: str, nombre_base: str = "guion_produccion") -> str:
    """Genera un archivo PDF profesional con el guion, Biblia Visual y dialogos ES/EN."""
    plan = json.loads(plan_json_str) if isinstance(plan_json_str, str) else plan_json_str
    return pdf_exp_srv.exportar_plan_a_pdf(plan, nombre_base=nombre_base)

@mcp.tool()
def mcp_listar_voces_kokoro() -> str:
    """Lista las voces open-source Kokoro-82M disponibles con su descripcion detallada."""
    return json.dumps(kokoro_srv.listar_voces_con_descripcion(), ensure_ascii=False)

@mcp.tool()
def mcp_asignar_voz_personaje(personaje: str, genero: str = "M", tono_hz: int = 0, velocidad_pct: int = 0) -> str:
    """Asigna automaticamente una voz unica si el personaje no tiene una configurada."""
    perfil = casting_srv.obtener_o_asignar_automatico(personaje, genero_ia=genero, tono_ia=tono_hz, velocidad_ia=velocidad_pct)
    return json.dumps({"personaje": personaje, "perfil": perfil}, ensure_ascii=False)

@mcp.tool()
def mcp_generar_cuadro_coherente(biblia_visual: str, prompt_escena: str, accion_narrada: str = "", indice_escena: int = 1, fuerza_coherencia: float = 0.64, pasos: int = 20) -> str:
    """Genera un fotograma coherente con la imagen anterior y armonizado en C++ portable."""
    return coherencia_srv.generar_escena_coherente(biblia_visual, prompt_escena, accion_narrada, indice_escena, fuerza_coherencia, pasos)

@mcp.tool()
def mcp_liberar_gpu_imagen() -> str:
    """Descarga los modelos visuales de VRAM/RAM cuando termina el bloque."""
    coherencia_srv.liberar_recursos()
    cpp_srv.descargar_de_memoria()
    return "Memoria liberada bajo demanda."

@mcp.tool()
def mcp_sintetizar_voz_dialogo(personaje: str, dialogo_limpio: str, idioma: str = "es", genero: str = "M", tono_hz: int = 0) -> str:
    """Sintetiza el dialogo limpio (sin nombre del personaje) usando su perfil o voz propia."""
    ruta_audio, texto_final = casting_srv.generar_voz_personaje(personaje, dialogo_limpio, idioma=idioma, genero_ia=genero, tono_ia=tono_hz)
    return json.dumps({"audio": ruta_audio, "texto": texto_final}, ensure_ascii=False)

@mcp.tool()
def mcp_editar_y_renderizar_video(idioma_audio: str = "es", modo_subtitulos: str = "Ambos (ES + EN)", nombre_base: str = "historia") -> str:
    """Renderiza el video sincronizado al milisegundo con subtitulos ES/EN y exporta MP4 + SRT."""
    if not HISTORIAL_PROYECTO_PATH.exists():
        return json.dumps({"error": "No hay escenas generadas."})
    escenas = json.loads(HISTORIAL_PROYECTO_PATH.read_text(encoding="utf-8"))
    mp4, srt = sync_av_srv.compilar_bloque_sincronizado(escenas, idioma_audio=idioma_audio, modo_subs=modo_subtitulos, nombre_archivo=nombre_base)
    return json.dumps({"video_mp4": mp4, "subtitulos_srt": srt}, ensure_ascii=False)

if __name__ == "__main__":
    mcp.run()

