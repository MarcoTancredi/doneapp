from fastapi import FastAPI, Request, Form, Depends, HTTPException, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import subprocess
import sys
from pathlib import Path
import asyncio
import threading
import sqlite3
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, List

# TOO/APP/MAIAA - Configuracao JWT
SECRET_KEY = "doneapp-super-secret-key-change-in-production-2025"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas

security = HTTPBearer(auto_error=False)

# TOO/APP/MAIBB - Database class inline
class Database:
    def __init__(self, db_path="data/doneapp.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.init_tables()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_tables(self):
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    phone TEXT,
                    company TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                );
                
                CREATE TABLE IF NOT EXISTS user_auth_methods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    method TEXT NOT NULL,
                    is_enabled BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                );
                
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            """)
    
    def create_user(self, username: str, email: str, password: str, phone: str = None, company: str = None):
        try:
            password_hash = self.hash_password(password)
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO users (username, email, password_hash, phone, company)
                    VALUES (?, ?, ?, ?, ?)
                """, (username, email, password_hash, phone, company))
                user_id = cursor.lastrowid
                self.log_action(user_id, "user_created", f"User {username} created")
                return user_id
        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                raise ValueError("Nome de usuario ja existe")
            elif "email" in str(e):
                raise ValueError("Email ja existe")
            else:
                raise ValueError("Erro ao criar usuario")
    
    def authenticate_user(self, login: str, password: str):
        with self.get_connection() as conn:
            user = conn.execute("""
                SELECT * FROM users WHERE (email = ? OR username = ?) AND is_active = 1
            """, (login, login)).fetchone()
            
            if user and self.verify_password(password, user['password_hash']):
                self.log_action(user['id'], "login_success", f"User {user['username']} logged in")
                return dict(user)
            else:
                self.log_action(None, "login_failed", f"Failed login for: {login}")
                return None
    
    def get_user_by_id(self, user_id: int):
        with self.get_connection() as conn:
            user = conn.execute("SELECT * FROM users WHERE id = ? AND is_active = 1", (user_id,)).fetchone()
            return dict(user) if user else None
    
    def set_auth_methods(self, user_id: int, methods: List[str]):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM user_auth_methods WHERE user_id = ?", (user_id,))
            for method in methods:
                conn.execute("INSERT INTO user_auth_methods (user_id, method) VALUES (?, ?)", (user_id, method))
    
    def log_action(self, user_id: Optional[int], action: str, details: str, ip_address: str = None):
        with self.get_connection() as conn:
            conn.execute("INSERT INTO logs (user_id, action, details, ip_address) VALUES (?, ?, ?, ?)", 
                        (user_id, action, details, ip_address))
    
    @staticmethod
    def hash_password(password: str) -> str:
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        try:
            salt, password_hash = stored_hash.split(":")
            return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
        except ValueError:
            return False

# TOO/APP/MAICC - Auth service inline
class AuthService:
    @staticmethod
    def create_access_token(user_data: Dict) -> str:
        to_encode = {
            "user_id": user_data["id"],
            "username": user_data["username"],
            "email": user_data["email"],
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            "iat": datetime.utcnow()
        }
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if datetime.utcfromtimestamp(payload["exp"]) < datetime.utcnow():
                return None
            return payload
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def register_user(username: str, email: str, password: str, phone: str = None, 
                     company: str = None, auth_methods: list = None) -> Dict:
        try:
            if len(username) < 3:
                raise ValueError("Nome de usuario deve ter pelo menos 3 caracteres")
            if len(password) < 6:
                raise ValueError("Senha deve ter pelo menos 6 caracteres")
            if not email or "@" not in email:
                raise ValueError("Email invalido")
            
            user_id = db.create_user(username, email, password, phone, company)
            
            if auth_methods:
                db.set_auth_methods(user_id, auth_methods)
            
            user_data = db.get_user_by_id(user_id)
            access_token = AuthService.create_access_token(user_data)
            
            return {
                "success": True,
                "message": "Usuario criado com sucesso",
                "user": {
                    "id": user_data["id"],
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "company": user_data["company"]
                },
                "access_token": access_token
            }
        except ValueError as e:
            return {"success": False, "message": str(e)}
        except Exception as e:
            return {"success": False, "message": "Erro interno do servidor"}
    
    @staticmethod
    def login_user(login: str, password: str, remember_me: bool = False) -> Dict:
        user_data = db.authenticate_user(login, password)
        
        if not user_data:
            return {"success": False, "message": "Email/usuario ou senha incorretos"}
        
        access_token = AuthService.create_access_token(user_data)
        
        return {
            "success": True,
            "message": "Login realizado com sucesso",
            "user": {
                "id": user_data["id"],
                "username": user_data["username"],
                "email": user_data["email"],
                "company": user_data["company"]
            },
            "access_token": access_token
        }

# TOO/APP/MAIDD - Dependencies para autenticacao
async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token: Optional[str] = Cookie(None, alias="access_token")
) -> Optional[Dict]:
    
    access_token = None
    if credentials:
        access_token = credentials.credentials
    elif token:
        access_token = token
    
    if not access_token:
        return None
    
    payload = AuthService.verify_token(access_token)
    if not payload:
        return None
    
    user_data = db.get_user_by_id(payload["user_id"])
    return user_data

async def require_auth(current_user: Dict = Depends(get_current_user)) -> Dict:
    if not current_user:
        raise HTTPException(status_code=401, detail="Usuario nao autenticado")
    return current_user

# TOO/APP/MAIEE - Instanciar database
db = Database()

# TOO/APP/MAIAA - App FastAPI principal
app = FastAPI(title="DoneApp", description="Publicacao Multicanal Automatizada")

templates = Jinja2Templates(directory="app/templates")

# Criar diretorio static se nao existir
static_dir = Path("app/static")
static_dir.mkdir(parents=True, exist_ok=True)

if static_dir.exists():
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    """Redireciona para /login"""
    return RedirectResponse(url="/login", status_code=302)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Tela de login com UI Neon responsiva"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/cadastro", response_class=HTMLResponse)
async def cadastro_page(request: Request):
    """Tela de cadastro com checklist de autenticacao"""
    return templates.TemplateResponse("cadastro.html", {"request": request})

@app.post("/api/register")
async def register_user_endpoint(
    request: Request,
    nome: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    telefone: str = Form(...),
    empresa: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    auth_sms: bool = Form(False),
    auth_whatsapp: bool = Form(False),
    auth_phone: bool = Form(False),
    auth_email: bool = Form(False),
    auth_admin: bool = Form(False),
    auth_youtube: bool = Form(False)
):
    """API para registrar novo usuario"""
    if password != confirm_password:
        return JSONResponse(status_code=400, content={"success": False, "message": "Senhas nao coincidem"})
    
    auth_methods = []
    if auth_sms: auth_methods.append("sms")
    if auth_whatsapp: auth_methods.append("whatsapp")
    if auth_phone: auth_methods.append("phone")
    if auth_email: auth_methods.append("email")
    if auth_admin: auth_methods.append("admin")
    if auth_youtube: auth_methods.append("youtube")
    
    result = AuthService.register_user(username, email, password, telefone, empresa, auth_methods)
    
    if result["success"]:
        client_ip = request.client.host
        db.log_action(result["user"]["id"], "registration_success", f"User registered from {client_ip}", client_ip)
        
        response = JSONResponse(content=result)
        response.set_cookie(key="access_token", value=result["access_token"], httponly=True, max_age=60*60*24, samesite="lax")
        return response
    else:
        return JSONResponse(status_code=400, content=result)

@app.post("/api/login")
async def login_user_endpoint(
    request: Request,
    login: str = Form(...),
    password: str = Form(...),
    remember_me: bool = Form(False)
):
    """API para fazer login"""
    result = AuthService.login_user(login, password, remember_me)
    
    if result["success"]:
        client_ip = request.client.host
        db.log_action(result["user"]["id"], "login_success", f"User logged in from {client_ip}", client_ip)
        
        response = JSONResponse(content=result)
        max_age = 60*60*24 if remember_me else 60*60
        response.set_cookie(key="access_token", value=result["access_token"], httponly=True, max_age=max_age, samesite="lax")
        return response
    else:
        return JSONResponse(status_code=401, content=result)

@app.post("/api/logout")
async def logout_user_endpoint():
    """API para fazer logout"""
    response = JSONResponse(content={"success": True, "message": "Logout realizado"})
    response.delete_cookie(key="access_token")
    return response

@app.get("/api/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """API para obter informacoes do usuario atual"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Usuario nao autenticado")
    
    return {
        "success": True,
        "user": {
            "id": current_user["id"],
            "username": current_user["username"],
            "email": current_user["email"],
            "company": current_user["company"],
            "phone": current_user["phone"]
        }
    }

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, current_user: dict = Depends(require_auth)):
    """Dashboard principal (requer autenticacao)"""
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": current_user})

@app.get("/updota", response_class=HTMLResponse)
async def updota_page(request: Request):
    """UI para aplicar patches (admin only)"""
    return templates.TemplateResponse("updota.html", {"request": request})

@app.post("/updota/apply")
async def apply_patch(request: Request, patch_content: str = Form(...)):
    """Aplica patch enviado via formulario"""
    try:
        inbox_dir = Path("inbox")
        inbox_dir.mkdir(exist_ok=True)
        
        patch_file = inbox_dir / "patch_input.txt"
        with open(patch_file, "w", encoding="utf-8") as f:
            f.write(patch_content)
        
        result = subprocess.run([
            sys.executable, "tools/apply_changes.py", 
            "--input", str(patch_file)
        ], capture_output=True, text=True, encoding="utf-8", errors="replace")
        
        output = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}\n\nReturn code: {result.returncode}"
        
        return templates.TemplateResponse("updota.html", {
            "request": request,
            "output": output,
            "success": result.returncode == 0,
            "patch_content": output
        })
        
    except Exception as e:
        output = f"Erro ao aplicar patch: {str(e)}"
        return templates.TemplateResponse("updota.html", {
            "request": request,
            "output": output,
            "success": False,
            "patch_content": output
        })

@app.get("/_dev/reload")
async def dev_reload():
    """Endpoint para reload de desenvolvimento"""
    reload_file = Path(".reload")
    reload_file.touch()
    return {"status": "reload triggered", "file": str(reload_file)}

@app.post("/updota/stop")
async def stop_server():
    """Para o servidor (uso em desenvolvimento)"""
    try:
        stop_file = Path(".stop_server")
        stop_file.touch()
        
        response_data = {"status": "stopping server", "message": "Servidor sera parado em 2 segundos"}
        
        def delayed_stop():
            import time
            time.sleep(2)
            import signal
            os.kill(os.getpid(), signal.SIGTERM)
        
        threading.Thread(target=delayed_stop).start()
        return response_data
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/updota/commit")
async def commit_changes():
    """Faz commit das alteracoes via git"""
    try:
        result_add = subprocess.run(
            ["git", "add", "."], 
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        
        result_commit = subprocess.run([
            "git", "commit", "-m", "[apply_changes] Alteracoes via updota"
        ], capture_output=True, text=True, encoding="utf-8", errors="replace")
        
        if result_commit.returncode == 0:
            return {"success": True, "message": "Commit realizado com sucesso"}
        else:
            if "nothing to commit" in result_commit.stdout.lower():
                return {"success": False, "message": "Nada para commitar - working tree limpo"}
            else:
                return {"success": False, "message": result_commit.stderr or result_commit.stdout or "Erro desconhecido no commit"}
            
    except Exception as e:
        return {"success": False, "message": f"Erro ao executar git: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)