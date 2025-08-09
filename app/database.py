

# TOO/APP/DATAA - Sistema de banco de dados SQLite

import sqlite3

from pathlib import Path

from datetime import datetime

import hashlib

import secrets

from typing import Optional, Dict, List



class Database:

    def __init__(self, db_path="data/doneapp.db"):

        # TOO/APP/DATBB - Inicializar conexao com banco

        self.db_path = Path(db_path)

        self.db_path.parent.mkdir(exist_ok=True)

        self.init_tables()

    

    def get_connection(self):

        # TOO/APP/DATCC - Criar conexao com row factory

        conn = sqlite3.connect(self.db_path)

        conn.row_factory = sqlite3.Row

        return conn

    

    def init_tables(self):

        # TOO/APP/DATDD - Criar todas as tabelas necessarias

        with self.get_connection() as conn:

            conn.executescript("""

                CREATE TABLE IF NOT EXISTS users (

                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    username TEXT UNIQUE NOT NULL,

                    email TEXT UNIQUE NOT NULL,

                    password_hash TEXT NOT NULL,

                    phone TEXT,

                    company TEXT,

                    remember_token TEXT,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    is_active BOOLEAN DEFAULT 1

                );

                

                CREATE TABLE IF NOT EXISTS user_auth_methods (

                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    user_id INTEGER NOT NULL,

                    method TEXT NOT NULL,

                    is_enabled BOOLEAN DEFAULT 0,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE

                );

                

                CREATE TABLE IF NOT EXISTS social_platforms (

                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    user_id INTEGER NOT NULL,

                    platform TEXT NOT NULL,

                    platform_user_id TEXT,

                    access_token TEXT,

                    refresh_token TEXT,

                    expires_at TIMESTAMP,

                    scope TEXT,

                    is_active BOOLEAN DEFAULT 1,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE

                );

                

                CREATE TABLE IF NOT EXISTS posts (

                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    user_id INTEGER NOT NULL,

                    title TEXT NOT NULL,

                    content TEXT NOT NULL,

                    media_urls TEXT,

                    platforms TEXT,

                    scheduled_time TIMESTAMP,

                    status TEXT DEFAULT 'draft',

                    published_at TIMESTAMP,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE

                );

                

                CREATE TABLE IF NOT EXISTS logs (

                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    user_id INTEGER,

                    action TEXT NOT NULL,

                    details TEXT,

                    ip_address TEXT,

                    user_agent TEXT,

                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL

                );

                

                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

                CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

                CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts(user_id);

                CREATE INDEX IF NOT EXISTS idx_logs_user_id ON logs(user_id);

                CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);

            """)

    

    def create_user(self, username: str, email: str, password: str, 

                   phone: str = None, company: str = None) -> Optional[int]:

        # TOO/APP/DATEE - Criar novo usuario

        try:

            password_hash = self.hash_password(password)

            

            with self.get_connection() as conn:

                cursor = conn.execute("""

                    INSERT INTO users (username, email, password_hash, phone, company)

                    VALUES (?, ?, ?, ?, ?)

                """, (username, email, password_hash, phone, company))

                user_id = cursor.lastrowid

                

                # TOO/APP/DATFF - Log de criacao de usuario

                self.log_action(user_id, "user_created", 

                              f"User {username} ({email}) created")

                

                return user_id

                

        except sqlite3.IntegrityError as e:

            if "username" in str(e):

                raise ValueError("Nome de usuario ja existe")

            elif "email" in str(e):

                raise ValueError("Email ja existe")

            else:

                raise ValueError("Erro ao criar usuario")

    

    def authenticate_user(self, login: str, password: str) -> Optional[Dict]:

        # TOO/APP/DATGG - Autenticar usuario por email ou username

        with self.get_connection() as conn:

            user = conn.execute("""

                SELECT * FROM users 

                WHERE (email = ? OR username = ?) AND is_active = 1

            """, (login, login)).fetchone()

            

            if user and self.verify_password(password, user['password_hash']):

                # TOO/APP/DATHH - Log de login bem-sucedido

                self.log_action(user['id'], "login_success", 

                              f"User {user['username']} logged in")

                

                return dict(user)

            else:

                # TOO/APP/DATII - Log de tentativa de login falhada

                self.log_action(None, "login_failed", 

                              f"Failed login attempt for: {login}")

                return None

    

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:

        # TOO/APP/DATJJ - Buscar usuario por ID

        with self.get_connection() as conn:

            user = conn.execute("""

                SELECT * FROM users WHERE id = ? AND is_active = 1

            """, (user_id,)).fetchone()

            

            return dict(user) if user else None

    

    def set_auth_methods(self, user_id: int, methods: List[str]):

        # TOO/APP/DATKK - Definir metodos de autenticacao do usuario

        with self.get_connection() as conn:

            # Limpar metodos existentes

            conn.execute("DELETE FROM user_auth_methods WHERE user_id = ?", (user_id,))

            

            # Inserir novos metodos

            for method in methods:

                conn.execute("""

                    INSERT INTO user_auth_methods (user_id, method, is_enabled)

                    VALUES (?, ?, 1)

                """, (user_id, method))

            

            self.log_action(user_id, "auth_methods_updated", 

                          f"Updated auth methods: {', '.join(methods)}")

    

    def log_action(self, user_id: Optional[int], action: str, details: str, 

                   ip_address: str = None, user_agent: str = None):

        # TOO/APP/DATLL - Registrar acao no log

        with self.get_connection() as conn:

            conn.execute("""

                INSERT INTO logs (user_id, action, details, ip_address, user_agent)

                VALUES (?, ?, ?, ?, ?)

            """, (user_id, action, details, ip_address, user_agent))

    

    @staticmethod

    def hash_password(password: str) -> str:

        # TOO/APP/DATMM - Hash seguro da senha usando SHA-256 + salt

        salt = secrets.token_hex(16)

        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()

        return f"{salt}:{password_hash}"

    

    @staticmethod

    def verify_password(password: str, stored_hash: str) -> bool:

        # TOO/APP/DATNN - Verificar senha contra hash armazenado

        try:

            salt, password_hash = stored_hash.split(":")

            return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash

        except ValueError:

            return False



# TOO/APP/DATOO - Instancia global do banco

db = Database()
