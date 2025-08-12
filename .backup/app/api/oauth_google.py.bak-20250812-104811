
import os, time, base64, hashlib, secrets
from urllib.parse import urlencode
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse
import httpx

router = APIRouter(prefix="/api/oauth/google", tags=["oauth-google"])

# Sessões in-memory (dev). TTL curto.
_SESS = {}
_TTL = 10 * 60  # 10min

def _b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")

def _pkce_verifier() -> str:
    # 43–128 chars; usamos 64
    return _b64url(secrets.token_bytes(64))

def _pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return _b64url(digest)

def _gc(key: str):
    # coleta simples de sessões expiradas
    now = time.time()
    for k, v in list(_SESS.items()):
        if now - v["ts"] > _TTL:
            _SESS.pop(k, None)

@router.post("/start")
async def oauth_start():
    _gc("all")
    cid = os.environ.get("GOOGLE_CLIENT_ID")
    redir = os.environ.get("GOOGLE_REDIRECT_URI")
    scopes = os.environ.get("GOOGLE_SCOPES", "openid email profile https://www.googleapis.com/auth/youtube.readonly")
    if not cid or not redir:
        return JSONResponse({"error":"missing_env","msg":"GOOGLE_CLIENT_ID/REDIRECT_URI ausentes"}, status_code=500)

    state = secrets.token_urlsafe(24)
    verifier = _pkce_verifier()
    challenge = _pkce_challenge(verifier)

    _SESS[state] = {"verifier": verifier, "ts": time.time()}

    q = {
        "client_id": cid,
        "redirect_uri": redir,
        "response_type": "code",
        "scope": scopes,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "include_granted_scopes": "true",
        "access_type": "offline",      # tenta refresh_token
        "prompt": "consent",           # força consentimento em dev
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(q)
    return JSONResponse({"url": url})

@router.get("/callback")
async def oauth_callback(request: Request):
    params = dict(request.query_params)
    error = params.get("error")
    if error:
        return RedirectResponse(f"/web/login.html#sso=google&error={error}")

    code = params.get("code")
    state = params.get("state")
    if not code or not state:
        return RedirectResponse("/web/login.html#sso=google&error=missing_code_or_state")

    sess = _SESS.pop(state, None)
    if not sess or (time.time() - sess["ts"] > _TTL):
        return RedirectResponse("/web/login.html#sso=google&error=state_expired")

    cid = os.environ.get("GOOGLE_CLIENT_ID")
    csec = os.environ.get("GOOGLE_CLIENT_SECRET")
    redir = os.environ.get("GOOGLE_REDIRECT_URI")
    if not cid or not csec or not redir:
        return RedirectResponse("/web/login.html#sso=google&error=server_env")

    data = {
        "client_id": cid,
        "client_secret": csec,
        "code": code,
        "code_verifier": sess["verifier"],
        "grant_type": "authorization_code",
        "redirect_uri": redir,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post("https://oauth2.googleapis.com/token", data=data)
        if r.status_code != 200:
            return RedirectResponse(f"/web/login.html#sso=google&error=token_exchange_{r.status_code}")

        tokens = r.json()
        # TODO: salvar tokens criptografados nas tabelas de integração (futuro)
        # access_token = tokens.get("access_token")
        # refresh_token = tokens.get("refresh_token")
        # expires_in = tokens.get("expires_in")

    success = os.environ.get("OAUTH_SUCCESS_REDIRECT", "/web/login.html")
    return RedirectResponse(f"{success}#sso=google&ok=1")
