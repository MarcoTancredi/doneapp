

# TOO/APP/AUTAA - Sistema de autenticacao e sessoes

from fastapi import HTTPException, Depends, Request, Cookie

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from typing import Optional, Dict

import secrets

import jwt

from datetime import datetime, timedelta

from .database import db



# TOO/APP/AUTBB - Configuracao JWT

SECRET_KEY = "your-super-secret-jwt-key-change-in-production"

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas



security = HTTPBearer(auto_error=False)



class AuthService:

    @staticmethod

    def create_access_token(user_data: Dict) -> str:

        # TOO/APP/AUTCC - Criar token JWT para usuario

        to_encode = {

            "user_id": user_data["id"],

            "username": user_data["username"],

            "email": user_data["email"],

            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),

            "iat": datetime.utcnow(),

            "type": "access"

        }

        

        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    

    @staticmethod

    def verify_token(token: str) -> Optional[Dict]:

        # TOO/APP/AUTDD - Verificar e decodificar token JWT

        try:

            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

            

            # Verificar se token nao expirou

            if datetime.utcfromtimestamp(payload["exp"]) < datetime.utcnow():

                return None

                

            return payload

            

        except jwt.InvalidTokenError:

            return None

    

    @staticmethod

    def register_user(username: str, email: str, password: str, 

                     phone: str = None, company: str = None, 

                     auth_methods: list = None) -> Dict:

        # TOO/APP/AUTEE - Registrar novo usuario

        try:

            # Validacoes basicas

            if len(username) < 3:

                raise ValueError("Nome de usuario deve ter pelo menos 3 caracteres")

            

            if len(password) < 6:

                raise ValueError("Senha deve ter pelo menos 6 caracteres")

            

            if not email or "@" not in email:

                raise ValueError("Email invalido")

            

            # Criar usuario no banco

            user_id = db.create_user(username, email, password, phone, company)

            

            # Definir metodos de autenticacao se fornecidos

            if auth_methods:

                db.set_auth_methods(user_id, auth_methods)

            

            # Buscar dados completos do usuario

            user_data = db.get_user_by_id(user_id)

            

            # Criar token de acesso

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

            return {

                "success": False,

                "message": str(e)

            }

        except Exception as e:

            return {

                "success": False,

                "message": "Erro interno do servidor"

            }

    

    @staticmethod

    def login_user(login: str, password: str, remember_me: bool = False) -> Dict:

        # TOO/APP/AUTFF - Fazer login do usuario

        user_data = db.authenticate_user(login, password)

        

        if not user_data:

            return {

                "success": False,

                "message": "Email/usuario ou senha incorretos"

            }

        

        # Criar token de acesso

        access_token = AuthService.create_access_token(user_data)

        

        # TOO/APP/AUTGG - Se remember_me, criar token de longa duracao

        remember_token = None

        if remember_me:

            remember_token = secrets.token_urlsafe(32)

            # Atualizar token no banco (implementar depois)

        

        return {

            "success": True,

            "message": "Login realizado com sucesso",

            "user": {

                "id": user_data["id"],

                "username": user_data["username"],

                "email": user_data["email"],

                "company": user_data["company"]

            },

            "access_token": access_token,

            "remember_token": remember_token

        }



# TOO/APP/AUTHH - Dependency para obter usuario atual

async def get_current_user(

    request: Request,

    credentials: HTTPAuthorizationCredentials = Depends(security),

    token: Optional[str] = Cookie(None, alias="access_token")

) -> Optional[Dict]:

    

    # Tentar obter token do header Authorization ou cookie

    access_token = None

    

    if credentials:

        access_token = credentials.credentials

    elif token:

        access_token = token

    

    if not access_token:

        return None

    

    # Verificar token

    payload = AuthService.verify_token(access_token)

    if not payload:

        return None

    

    # Buscar dados atualizados do usuario

    user_data = db.get_user_by_id(payload["user_id"])

    if not user_data:

        return None

    

    return user_data



# TOO/APP/AUTII - Dependency que requer autenticacao

async def require_auth(current_user: Dict = Depends(get_current_user)) -> Dict:

    if not current_user:

        raise HTTPException(status_code=401, detail="Usuario nao autenticado")

    return current_user
