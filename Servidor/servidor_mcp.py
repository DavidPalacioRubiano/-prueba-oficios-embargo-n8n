"""
Servidor MCP - Criterios de decisión para oficios de embargo
=============================================================
Expone, vía Model Context Protocol (HTTP/SSE), los criterios de negocio
que el flujo de n8n consulta para clasificar y priorizar oficios de embargo.



from mcp.server.fastmcp import FastMCP

# Creamos el servidor MCP con un nombre identificable
mcp = FastMCP("Criterios Oficios Embargo")


# --- Herramienta 1: criterios de clasificación tecnológica ---
@mcp.tool()
def get_classification_criteria() -> dict:
    """
    Devuelve los criterios para clasificar un oficio de embargo
    hacia la plataforma adecuada (Appian, n8n, Microservicio,
    Power Platform o RPA Selectivo).
    """
    return {
        "criterios": [
            {
                "plataforma": "Appian",
                "condicion": "Requiere aprobación humana Y (datos sensibles O urgencia regulatoria)",
                "motivo": "Apertura formal de caso, aprobaciones, control de estado y trazabilidad legal."
            },
            {
                "plataforma": "Microservicio",
                "condicion": "La descripción indica cálculo o lógica especializada/compleja",
                "motivo": "Reglas complejas o cálculos especializados que requieren robustez y escala."
            },
            {
                "plataforma": "RPA Selectivo",
                "condicion": "Está sobre RPA hoy Y no hay API disponible",
                "motivo": "Interfaz legacy sin alternativa de integración; solo si no hay otra vía."
            },
            {
                "plataforma": "n8n",
                "condicion": "Hay API disponible O no requiere aprobación humana compleja",
                "motivo": "Extracción, validación, normalización, enrute y notificación orquestable vía API."
            },
            {
                "plataforma": "Power Platform",
                "condicion": "Caso por defecto: apoyo operativo simple de baja complejidad",
                "motivo": "Captura simple o apoyo operativo interno de baja complejidad."
            }
        ],
        "orden_evaluacion": "Las reglas se evalúan de la más exigente (Appian) a la más simple (Power Platform)."
    }


# --- Herramienta 2: factores de priorización ---
@mcp.tool()
def get_priority_rules() -> dict:
    """
    Devuelve los factores y pesos para asignar la prioridad
    (Alta, Media, Baja) a un oficio de embargo.
    """
    return {
        "factores": [
            {"factor": "urgencia_regulatoria", "peso": 3},
            {"factor": "datos_sensibles", "peso": 2},
            {"factor": "requiere_aprobacion_humana", "peso": 2},
            {"factor": "volumen_mensual_alto (>=300)", "peso": 2},
            {"factor": "volumen_mensual_moderado (>=100)", "peso": 1},
            {"factor": "tiempo_manual_alto (>=20 min)", "peso": 1},
            {"factor": "actualmente_sobre_rpa", "peso": 1},
            {"factor": "sin_api_disponible", "peso": 1},
            {"factor": "medida_embargo_o_retencion", "peso": 1}
        ],
        "umbrales": {
            "Alta": "puntaje >= 8",
            "Media": "puntaje >= 4",
            "Baja": "puntaje < 4"
        }
    }


# --- Herramienta 3: plantilla de respuesta al solicitante ---
@mcp.tool()
def get_response_template() -> dict:
    """
    Devuelve la plantilla y los elementos que debe incluir
    el acuse de recibo al solicitante.
    """
    return {
        "elementos_requeridos": [
            "confirmación de recepción",
            "categoría de solución recomendada",
            "prioridad asignada",
            "siguiente paso sugerido",
            "advertencia si faltan anexos o datos mínimos"
        ],
        "tono": "formal, breve, claro"
    }


# --- Arranque del servidor en modo HTTP/SSE ---
if __name__ == "__main__":
    import uvicorn
    from starlette.middleware.trustedhost import TrustedHostMiddleware

    app = mcp.sse_app()

    # Acepta cualquier host (resuelve el "Invalid Host header" con ngrok)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

    uvicorn.run(app, host="0.0.0.0", port=8000)