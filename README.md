# Flask en IBM Cloud Code Engine

Este paquete contiene los archivos mínimos para desplegar una app Flask (tu `app.py`) en IBM Cloud Code Engine.

## Estructura
- `Dockerfile`: Imagen de contenedor lista para producción con Gunicorn.
- `requirements.txt`: Dependencias de Python.
- `wsgi.py`: Punto de entrada WSGI que importa `app` desde `app.py` o usa `create_app()` si existe.
- `gunicorn.conf.py`: Configuración de Gunicorn (usa el env `PORT` que provee Code Engine).
- `.dockerignore`: Excluye archivos innecesarios al construir la imagen.

> **Importante**: Debes tener un `app.py` en el mismo directorio que defina `app = Flask(__name__)`
> (o una función `create_app()` que retorne la app). `wsgi.py` la importará automáticamente.

---

## Build & Push de la imagen (IBM Cloud Container Registry)

1. **Inicia sesión en IBM Cloud e instala CLIs** (si aún no lo has hecho):

   ```bash
   ibmcloud login -r us-south
   ibmcloud plugin install code-engine
   ibmcloud plugin install container-registry
   ```

2. **Target al registro** y crea un namespace (reemplaza `mi-namespace` por el tuyo):

   ```bash
   ibmcloud cr region-set us-south
   ibmcloud cr namespace-add mi-namespace
   ibmcloud cr login
   ```

3. **Construye y sube la imagen** (asumiendo que este repo contiene `app.py` y estos archivos):

   ```bash
   # Desde la carpeta del proyecto
   export REGION=us-south
   export NS=mi-namespace
   export IMG=flask-ce:latest

   docker build -t $REGION.icr.io/$NS/$IMG .
   docker push $REGION.icr.io/$NS/$IMG
   ```

---

## Despliegue en Code Engine

1. **Selecciona o crea un proyecto de Code Engine**:

   ```bash
   ibmcloud ce project create --name mi-proyecto || true
   ibmcloud ce project select --name mi-proyecto
   ```

2. **Crea la aplicación** (ajusta recursos y escala según tus necesidades):

   ```bash
   ibmcloud ce app create \
     --name flask-app \
     --image $REGION.icr.io/$NS/$IMG \
     --port 8080 \
     --cpu 0.25 \
     --memory 0.5G \
     --min-scale 0 \
     --max-scale 3 \
     --env PYTHONUNBUFFERED=1
   ```

3. **Obtén la URL**:

   ```bash
   ibmcloud ce app get --name flask-app
   # Mira el campo "URL:"
   ```

4. **Actualizar versión** (nuevo push de imagen):

   ```bash
   docker build -t $REGION.icr.io/$NS/$IMG .
   docker push $REGION.icr.io/$NS/$IMG
   ibmcloud ce app update --name flask-app --image $REGION.icr.io/$NS/$IMG
   ```

---

## Notas útiles

- **Puerto**: Code Engine inyecta el puerto en `PORT`. `gunicorn.conf.py` ya lo usa.
- **Logs**: `ibmcloud ce app logs --name flask-app --follow`
- **Variables de entorno** adicionales: `ibmcloud ce app update --name flask-app --env KEY=VALUE`
- **Healthcheck simple**: agrega en `app.py` una ruta `/health` que retorne 200 ok para sondas.

```python
# En tu app.py
from flask import Flask
app = Flask(__name__)

@app.get("/health")
def health():
    return {"status": "ok"}, 200
```

## Desarrollo local

```bash
pip install -r requirements.txt
export PORT=8080
gunicorn wsgi:app -c gunicorn.conf.py
# Visita http://localhost:8080
```


### Variables de entorno requeridas

Debes configurar estas variables (en Code Engine o local):

- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT` (ej: `https://mi-recurso.openai.azure.com`)
- `AZURE_OPENAI_API_VERSION` (ej: `2024-12-01-preview`)
- `AZURE_ASSISTANT_ID`

**Ejemplo (crear app con envs):**
```bash
ibmcloud ce app create       --name flask-app       --image $REGION.icr.io/$NS/$IMG       --port 8080       --cpu 0.25       --memory 0.5G       --min-scale 0       --max-scale 3       --env AZURE_OPENAI_API_KEY=@/secure/path/azure.key \ 
  --env AZURE_OPENAI_ENDPOINT=https://mi-recurso.openai.azure.com       --env AZURE_OPENAI_API_VERSION=2024-12-01-preview       --env AZURE_ASSISTANT_ID=asst_xxx
```

> TIP: Para mayor seguridad, usa **Secrets** de Code Engine y referencia con `--env-from-secret`.
