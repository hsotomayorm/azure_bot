# app.py (Flask + Azure OpenAI Assistants via OpenAI SDK)
# Adaptado para IBM Cloud Code Engine (usa variables de entorno)
from flask import Flask, request, jsonify
from openai import OpenAI, APIError
from typing import Optional
import os

# ----- Config desde ENV -----
AZURE_API_KEY      = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_ENDPOINT     = os.getenv("AZURE_OPENAI_ENDPOINT")  # p.ej. https://<tu-recurso>.openai.azure.com/
AZURE_API_VERSION  = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
AZURE_ASSISTANT_ID = os.getenv("AZURE_ASSISTANT_ID")

for k,v in {
    "AZURE_OPENAI_API_KEY": AZURE_API_KEY,
    "AZURE_OPENAI_ENDPOINT": AZURE_ENDPOINT,
    "AZURE_OPENAI_API_VERSION": AZURE_API_VERSION,
    "AZURE_ASSISTANT_ID": AZURE_ASSISTANT_ID
}.items():
    if not v:
        raise RuntimeError(f"Falta variable: {k}")

client = OpenAI(
    api_key=AZURE_API_KEY,
    base_url=f"{AZURE_ENDPOINT}/openai",
    default_query={"api-version": AZURE_API_VERSION},
    default_headers={"api-key": AZURE_API_KEY},
)

app = Flask(__name__)

# --- helpers ---
def normalize_thread_id(raw: Optional[str]) -> Optional[str]:
    """Convierte "null", "None", "", None -> None. Deja pasar IDs válidos."""
    if raw is None:
        return None
    s = str(raw).strip()
    if s == "" or s.lower() in {"null", "none"}:
        return None
    return s

def ensure_thread(thread_id: Optional[str]) -> str:
    if thread_id:
        return thread_id
    t = client.beta.threads.create()
    return t.id

def ask_assistant(thread_id: str, question: str) -> str:
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=question
    )
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=AZURE_ASSISTANT_ID
    )
    if getattr(run, "status", None) != "completed":
        raise RuntimeError(f"Run no completado. Estado: {getattr(run, 'status', 'desconocido')}")

    msgs = client.beta.threads.messages.list(thread_id=thread_id)
    for m in getattr(msgs, "data", []):
        if getattr(m, "role", None) == "assistant" and getattr(m, "content", None):
            try:
                return m.content[0].text.value
            except Exception:
                return str(m.content)
    return ""

# --- routes ---
@app.route("/health", methods=["GET"])
def health():
    return jsonify(ok=True), 200

@app.route("/ask", methods=["GET", "POST"])
def ask():
    payload   = request.get_json(silent=True) or {}
    question  = request.args.get("q")         or payload.get("q")
    raw_tid   = request.args.get("thread_id") or payload.get("thread_id")
    thread_id = normalize_thread_id(raw_tid)

    app.logger.info(f"[ask] q={question!r} thread_in={raw_tid!r} -> thread_norm={thread_id!r}")

    if not question or not str(question).strip():
        return jsonify(error="Falta parámetro 'q' con la pregunta."), 400

    try:
        thread_id = ensure_thread(thread_id)
        answer = ask_assistant(thread_id, str(question).strip())
        return jsonify(answer=answer, thread_id=thread_id)
    except APIError as e:
        return jsonify(error=f"APIError: {e}"), 502
    except Exception as e:
        return jsonify(error=f"Error: {e}"), 500

# Alias opcional si algún cliente usa /api/messages
@app.route("/api/messages", methods=["POST"])
def api_messages_alias():
    return ask()

@app.route("/new_thread", methods=["POST"])
def new_thread():
    t = client.beta.threads.create()
    return jsonify(thread_id=t.id)

if __name__ == "__main__":
    # Para desarrollo local; en Code Engine se usa gunicorn + wsgi.py
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=True)
