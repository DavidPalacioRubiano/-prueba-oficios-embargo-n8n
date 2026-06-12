# Gestión de Oficios de Embargo y Enrutamiento de Casos

Este es mi desarrollo para la prueba técnica. Es un flujo en n8n que recibe oficios de embargo, los valida, los clasifica hacia la plataforma que mejor encaje (Appian, n8n, microservicio, etc.), les asigna una prioridad, genera un resumen con un modelo de IA y deja todo registrado. Le agregué además un servidor MCP en Python como valor extra, que es donde viven los criterios de decisión.

Hay dos versiones del flujo:

- Oficios de Embargo - Enrutamiento: la versión base. Hace todo con nodos de n8n, sin depender de nada externo.
- Oficios de Embargo - Enrutamiento MCP: la misma, pero además consulta el servidor MCP para traer los criterios de clasificación desde afuera.

La idea de tener las dos es que la base funciona siempre, y la de MCP muestra la parte más avanzada (que sí depende de levantar el servidor).

## Qué hay en el repo

- `Flujos de trabajo/` — los tres workflows exportados de n8n (los dos de oficios + el de manejo de errores).
- `Servidor/servidor_mcp.py` — el servidor MCP en Python.
- `Documentación/` — la explicación técnica completa, en Word y PDF. Ahí están los supuestos, riesgos y posibles mejoras.
- `Pantallazos de prueba y apoyo/` — capturas del MCP funcionando (el servidor recibiendo peticiones, ngrok, y la consulta desde n8n).
- `requirements.txt` — lo que necesita el servidor de Python.

## Cómo funciona

El oficio entra por un webhook (JSON). Primero se valida que traiga los campos mínimos; si le falta algo, se rechaza diciendo qué falta. Si está completo, sigue el camino normal: se enriquece (deduce el tipo de caso, la jurisdicción, a quién enrutarlo), se clasifica por un árbol de decisión, se le calcula la prioridad con un sistema de puntaje, se le genera un resumen con Gemini, y al final se arma el JSON de salida, el acuse para el solicitante y la bitácora.

La clasificación se determina de lo más exigente a lo más simple: si necesita aprobación humana y maneja datos sensibles o urgencia legal, va a Appian; si es algo de integración pura, a n8n; y así. El orden importa para que un caso crítico no se cuele en una categoría más liviana.

## Para correrlo

### Los flujos en n8n

1. Abrir n8n e importa los tres archivos de `Flujos de trabajo/` (menú de los tres puntos , luego a Import from File).
2. En el flujo principal, entrar a Settings, luego a Error Workflow y vuelve a seleccionar "Manejo de Errores - Oficios". Al importar se pierde ese vínculo, hay que reconectarlo.
3. En el nodo de Gemini ("Generar Resumen") se pondrá la propia API key de Gemini. La mía no va incluida en el export. Se saca en https://aistudio.google.com/apikey.

Para probarlo, activa el webhook (Listen for Test Event) y mándale el JSON de ejemplo que dejo más abajo por POST.

### El servidor MCP

Esto solo hace falta si se requiere probar con MCP.

```bash
pip install -r requirements.txt
python "Servidor/servidor_mcp.py"
```

El servidor queda escuchando en el puerto 8000.

**Si corres n8n en tu propia máquina (local)**, es lo más sencillo: no necesitas nada más. En el nodo MCP Client del flujo apunta la URL directamente a:

```
http://localhost:8000/sse
```

**Si usas n8n en la nube** (como hice yo en el desarrollo), ahí sí necesitas exponer el servidor con ngrok, porque la nube no puede ver tu localhost:

```bash
ngrok http 8000
```

ngrok te da una URL pública; esa la pones en el nodo MCP Client con `/sse` al final. Ojo que esa URL cambia cada vez que reinicias ngrok en el plan gratis.

En el nodo MCP Client, deja el Server Transport en SSE y la autenticación en None.

> Nota de por qué uso ngrok: yo desarrollé todo sobre n8n Cloud, y la nube no alcanza un servidor local, por eso el túnel. Si tú lo corres local, te saltas ese paso y vas directo a localhost.

## Ejemplo de entrada

```json
{
  "case_id": "EMB-2026-00421",
  "requester_name": "Carolina Torres",
  "requester_email": "carolina.torres@empresa.com",
  "area": "Cumplimiento y Operaciones",
  "process_name": "Embargo judicial sobre cuenta de cliente",
  "document_type": "oficio_embargo",
  "description": "Oficio judicial recibido para aplicar embargo preventivo sobre productos del cliente.",
  "channel": "correo",
  "monthly_volume": 320,
  "current_solution": "rpa",
  "has_api_available": false,
  "requires_human_approval": true,
  "uses_sensitive_data": true,
  "regulatory_urgency": true,
  "estimated_manual_time_minutes": 25,
  "attachments": ["oficio_embargo.pdf", "anexos_judiciales.pdf"]
}
```

Con ese caso, la salida clasifica en Appian con prioridad Alta (tiene aprobación humana, datos sensibles y urgencia regulatoria, que es justo el escenario que pide Appian).

## El servidor MCP

Expone tres cosas: los criterios de clasificación, las reglas de prioridad y la plantilla del acuse. La gracia es que las reglas de negocio no quedan "quemadas" dentro del flujo, sino que viven en el servidor y se consultan por protocolo. Así se pueden cambiar sin tocar el flujo. Va por SSE y acepta cualquier host (lo necesité para que ngrok pudiera reenviarle las peticiones).

## Un par de aclaraciones

- La entrada la hice por webhook con JSON, que el enunciado permite. Asumo que la conversión del PDF escaneado a JSON pasa en un paso anterior (un OCR o similar), no lo metí dentro del flujo.
- El acuse al solicitante lo genero como mensaje (el campo `acknowledgement_message`), no lo mando por correo de verdad porque el destinatario es de prueba. En producción se le conectaría un nodo de Gmail/SMTP que lo envíe.
- En la documentación de la carpeta `Documentación/` está todo más a fondo, con los supuestos, riesgos y lo que mejoraría si tuviera más tiempo.

Cualquier cosa quedo atento.
