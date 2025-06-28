import subprocess
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from datetime import datetime


import secrets
print(secrets.token_urlsafe(32))

API_KEY = "kKe_shlLl2UhGQcLVQcQABeD4qPsErZ28EGExXEikCU"  # Change this and keep secret

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Hello from FastAPI!"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your domain for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# def verify_api_key(x_api_key: str = Header(None)):
#     if x_api_key != API_KEY:
#         raise HTTPException(status_code=401, detail="Unauthorized")

def query_ollama(prompt: str) -> str:
    try:
        result = subprocess.run(
            ["ollama", "run", "llama2", prompt],
            capture_output=True,
            text=True,
            timeout=20,  # Increase timeout for slower startup
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error from Ollama: {result.stderr.strip()}"
    except Exception as e:
        return f"Exception when calling Ollama: {str(e)}"

def init_db():
    conn = sqlite3.connect("chat_logs.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_id TEXT,
            prompt TEXT,
            reply TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Run this once on startup
init_db()


# @app.post("/chat")
# async def chat(req: Request, x_api_key: str = Header(None)):
#     verify_api_key(x_api_key)
#     data = await req.json()
#     prompt = data.get("prompt", "")

#     reply = query_ollama(prompt)

#     # Log chats to a file
#     with open("chat_logs.json", "a", encoding="utf-8") as f:
#         f.write(f'{{"prompt": "{prompt}", "reply": "{reply}"}}\n')

#     return {"reply": reply}

def verify_api_key(x_api_key: str = Header(None)):
    print(f"📥 Received API Key: {x_api_key}")
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.post("/chat")
async def chat(req: Request, x_api_key: str = Header(None)):
    verify_api_key(x_api_key)
    data = await req.json()
    prompt = data.get("prompt", "")
    user_id = data.get("userId", "anonymous")

    reply = query_ollama(prompt)

    # Log to SQLite
    conn = sqlite3.connect("chat_logs.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO logs (timestamp, user_id, prompt, reply) VALUES (?, ?, ?, ?)",
        (datetime.utcnow().isoformat(), user_id, prompt, reply)
    )
    conn.commit()
    conn.close()

    return {"reply": reply}
