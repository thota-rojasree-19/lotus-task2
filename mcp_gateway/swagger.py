import json
import yaml
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route
from mcp_gateway.config import OPENAPI_FILE

def get_openapi_spec(request):
    try:
        with open(OPENAPI_FILE, "r") as f:
            if OPENAPI_FILE.endswith(".yaml") or OPENAPI_FILE.endswith(".yml"):
                spec = yaml.safe_load(f)
            else:
                spec = json.load(f)
        return JSONResponse(spec)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

def swagger_ui(request):
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>Swagger UI</title>
      <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css" />
      <style>
        body { margin: 0; padding: 0; }
      </style>
    </head>
    <body>
      <div id="swagger-ui"></div>
      <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
      <script>
        window.onload = function() {
          window.ui = SwaggerUIBundle({
            url: "/openapi.json",
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [
              SwaggerUIBundle.presets.apis,
              SwaggerUIBundle.SwaggerUIStandalonePreset
            ],
          });
        };
      </script>
    </body>
    </html>
    """
    return HTMLResponse(html)

def get_swagger_routes():
    return [
        Route("/docs", endpoint=swagger_ui, methods=["GET"]),
        Route("/openapi.json", endpoint=get_openapi_spec, methods=["GET"])
    ]
