
from __future__ import annotations
import os, sqlite3, hashlib, hmac
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from passlib.hash import bcrypt
import jwt  # PyJWT

# --- Config ---
BASE_DIR = Path(__file__).resolve().parents[2]  # raiz do repo (app/api/.. -> raiz)
DATA_DIR = BASE_DIR / "data"
DB_PATH  = DATA_DIR / "app.db"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SECRET_KEY = os.getenv("FASTAPI_SECRET", "CHANGE-ME-SECRET")
ALGO = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

# --- App ---
app = FastAPI(title="DoneApp API", openapi_url="/api/openapi.json", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# --- Static (frontend simples) ---
WEB_DIR = BASE_DIR / "app" / "web"
WEB_DIR.mkdir(parents=True, exist_ok=True)
from fastapi.responses import FileResponse
app.mount("/web", StaticFiles(directory=str(WEB_DIR), html=True), name="web")

@app.get("/", include_in_schema=False)
def root_index():
    return FileResponse(WEB_DIR / "index.html")

# --- DB helpers ---
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      created_at TEXT NOT NULL
    );
    """)
    conn.commit()
    conn.close()

init_db()

# --- Schemas ---
class SignUp(BaseModel):
    username: str
    password: str

class Login(BaseModel):
    username: str
    password: str

# --- Auth helpers ---
def create_access_token(sub: str, expires_delta: Optional[timedelta] = None) -> str:
    now = datetime.now(timezone.utc)
    exp = now + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    payload = {"sub": sub, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGO)

def verify_password(pw: str, pw_hash: str) -> bool:
    try:
        return bcrypt.verify(pw, pw_hash)
    except Exception:
        return False

def get_current_user(request: Request) -> str:
    auth = request.headers.get("Authorization") or ""
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token = auth.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGO])
        return str(payload.get("sub"))
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

# --- Routes ---
@app.post("/api/signup")
def api_signup(body: SignUp):
    if not body.username or not body.password:
        raise HTTPException(status_code=400, detail="Missing username/password")
    conn = get_db()
    try:
        pw_hash = bcrypt.hash(body.password)
        conn.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (body.username, pw_hash, datetime.utcnow().isoformat()+"Z"),
        )
        conn.commit()
        return {"ok": True}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()

@app.post("/api/login")
def api_login(body: Login):
    conn = get_db()
    try:
        row = conn.execute("SELECT password_hash FROM users WHERE username = ?", (body.username,)).fetchone()
        if not row or not verify_password(body.password, row[0]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_access_token(sub=body.username)
        return {"access_token": token, "token_type": "bearer"}
    finally:
        conn.close()

@app.post("/api/logout")
def api_logout():
    # logout é client-side (descartar token). Sem blacklist aqui.
    return {"ok": True}

@app.get("/api/me")
def api_me(user: str = Depends(get_current_user)):
    return {"user": user}

# Health
@app.get("/api/healthz")
def healthz():
    return {"ok": True}
