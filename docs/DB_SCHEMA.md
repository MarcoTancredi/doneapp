
# DoneApp — Esquema de Banco & Fluxos (DEV)

> **Regra em desenvolvimento**: sempre que houver ajuste de campos em tabelas já criadas, **NÃO faremos migrações**.  
> Procedimento: eu aviso → **você deleta a(s) tabela(s)** (ou o `data/app.db`) → ao iniciar, a API recria o **SQLite** com o schema novo.

## 0) Contexto rápido
- Banco: **SQLite** (`data/app.db`).
- API: **FastAPI**.
- Auth: login local + **SSO YouTube (Google OAuth)** (`/api/oauth/google/...`).
- Criptografia: `cryptography` (Fernet) — tokens de integrações **criptografados**.
- Rate limit & IP rules: pronto em arquivo/UI; poderá migrar para DB.

---

## 1) Tabelas (DDL — SQLite)

> Índices e `CHECK`s foram incluídos para consistência.  
> O app deve criar estas tabelas na inicialização se não existirem.

### 1.1) `users`
Usuários do sistema (locais e SSO).

```sql
CREATE TABLE IF NOT EXISTS users (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  username          TEXT    NOT NULL UNIQUE,         -- sem '@'
  full_name         TEXT,
  company           TEXT,
  phone             TEXT,                            -- livre: "+55 11 9999-9999" ou "+1 555 999-9999"
  email             TEXT    NOT NULL UNIQUE,
  class             TEXT    NOT NULL DEFAULT '0000000000',   -- 10 dígitos (ver Seção 2)
  password_hash     TEXT,                            -- NULL para contas só-SSO
  sso_google_sub    TEXT UNIQUE,                     -- 'sub' do OIDC (Google/YouTube)
  status            TEXT    NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending','approved','blocked')),
  is_admin          INTEGER NOT NULL DEFAULT 0,      -- 0/1
  created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_used_at      TIMESTAMP,
  last_accessed_ip  TEXT,
  CHECK (length(class)=10)
);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email    ON users(email);

Seed admin: se users estiver vazia na inicialização, criar admin a partir do .env
ADMIN_USER, ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_FULL_NAME (opcional).
Definir is_admin=1, status='approved' e, se configurado, class com dígito Admin (ver Seção 2).

Em DEV, podemos forçar MASTER (class[4]='9') via env (ex.: ADMIN_CLASS=0000900000).

⸻

1.2) logs

Auditoria de tudo por IP/usuário.
CREATE TABLE IF NOT EXISTS logs (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     INTEGER,           -- pode ser NULL (ex.: erro login antes de identificar)
  username    TEXT,              -- cópia útil em auditoria
  ip          TEXT NOT NULL,
  action      TEXT NOT NULL,     -- ex.: 'signup.request', 'login.ok', 'login.fail', 'sso.google.connect'
  details     TEXT,              -- JSON/texto livre
  created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_logs_user ON logs(user_id);
CREATE INDEX IF NOT EXISTS idx_logs_ip   ON logs(ip);
CREATE INDEX IF NOT EXISTS idx_logs_act  ON logs(action);

Eventos a logar: criação de usuário, tentativas de login (ok/fail), logout, refresh, bloqueios, alterações de perfil, criação/remoção de integrações, ações de admin etc.

⸻

1.3) config

Chave-valor para parametrizações do sistema.

CREATE TABLE IF NOT EXISTS config (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  key         TEXT NOT NULL UNIQUE,    -- ex.: 'rate.login.per_ip.10m', 'smtp.host'
  description TEXT,
  value       TEXT NOT NULL,           -- sempre string (números também em string)
  updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

Usos: limites por IP, janelas de tempo, toggles, template default, chaves públicas etc.

⸻

1.4) integrations

Tokens e perfis externos (YouTube/Google inicialmente).

CREATE TABLE IF NOT EXISTS integrations (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id          INTEGER NOT NULL,
  provider         TEXT    NOT NULL,              -- 'google'
  account_id       TEXT,                          -- ex.: OIDC 'sub' ou id do canal
  display_name     TEXT,
  scopes           TEXT,                          -- string única com escopos
  enc_access_token BLOB,                          -- Fernet
  enc_refresh_token BLOB,
  expires_at       TIMESTAMP,                     -- expiração do access_token
  created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (user_id, provider),
  FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_int_user ON integrations(user_id);

Criptografia: usar FERNET_KEY do .env. Para rotação futura: MultiFernet + key_version.

⸻

2) Campo class (string de 10 dígitos)

Representa pedidos e confirmações de meios de autenticação/contato/perfil.
Cada dígito é um canal:
	•	0 = não solicitado
	•	1 = solicitado (pedido do usuário)
	•	2 = confirmado (validado/verificado)

Admin MASTER: se class[4] === '9', o usuário tem privilégios expandidos e vê os painéis de administração.
(Em ambientes não-produtivos, podemos setar ADMIN_CLASS=0000900000 no seed.)

Mapa recomendado (10 posições)
	1.	class[0] → E-mail
	2.	class[1] → SMS
	3.	class[2] → WhatsApp
	4.	class[3] → Ligação
	5.	class[4] → Admin (valores usuais 0/1/2; 9 = MASTER)
	6.	class[5] → YouTube/Google SSO
	7.	class[6] → Facebook SSO
	8.	class[7] → GitHub SSO
	9.	class[8] → TikTok SSO
	10.	class[9] → Reserva/Futuro

Exemplos:
	•	Pediu SMS → class[1]: 0 → 1
	•	Confirmou SMS → class[1]: 1 → 2
	•	Conectou Google SSO com sucesso → class[5] = 2

⸻

3) Fluxos de cadastro

3.1) SSO YouTube
	1.	Login → YouTube → consentimento → callback cria sid (10 min) com profile+tokens.
	2.	Redireciona para /web/register_v2.html?sid=....
	3.	Tela pré-preenche Nome/Email/Avatar; senha opcional.
	4.	Finalizar:
	•	Se email já existe:
	•	status='pending' → “aguardando liberação”
	•	approved → “usuário já cadastrado”
	•	Se não existe:
	•	cria em users com sso_google_sub, status=... (política)
	•	cria/atualiza integrations com tokens criptografados
	•	define class[5]='2'
	5.	Logar tudo em logs.

3.2) Cadastro manual
	1.	/web/register_v2.html sem sid.
	2.	Campos obrigatórios: username, email, senha, termos.
	3.	Backend cria users (status='pending' por padrão).
	4.	Log correspondente em logs.

3.3) Login
	•	Por email ou username (se contém @ ⇒ email; senão ⇒ username).
	•	Checar status:
	•	pending → negar com “aguardando liberação”
	•	blocked → negar com “acesso bloqueado”
	•	approved → ok
	•	Registrar IP em last_accessed_ip e atualizar last_used_at.

⸻

4) Seed do Admin

Na inicialização, se SELECT COUNT(*) FROM users = 0:
	•	Criar usuário admin com .env:
ADMIN_USER, ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_FULL_NAME
	•	is_admin=1, status='approved'.
	•	Se houver ADMIN_CLASS, usar como valor inicial (ex.: 0000900000 para MASTER).
	•	Logar evento em logs.

⸻

5) Notas de implementação
	•	Fernet: FERNET_KEY no .env; guardar tokens em integrations.enc_*.
	•	Validações: username sem @ e sem espaços; email válido; phone livre.
	•	Logs: padronizar action (namespace tipo login.ok, login.fail, sso.google.connect).
	•	Reset DEV: para qualquer mudança de schema, deletar tabela (ou o arquivo app.db) → app recria.
Scripts: tools/dev_db_reset.ps1 / .bat.

⸻

6) Próximos passos
	•	Conectar register_v2.html ao backend real (/api/signup e /api/sso/finalize gravando em DB).
	•	Persistir tokens YouTube criptografados em integrations.
	•	Home: após login, redirecionar para admin.html (MASTER) ou clients.html.
	•	Scheduler: ligar /web/scheduler.html ao endpoint /api/schedule (multipart), e fazer upload de mídia ao WordPress/Hostinger via REST:
	•	.env:

WP_BASE=https://planetamicro.com.br
WP_USER=seu_usuario
WP_APP_PASSWORD=app-password-gerado-no-wp

	•	API: POST wp-json/wp/v2/media (retorna URL do arquivo) e salvar URL no agendamento.
