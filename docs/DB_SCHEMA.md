
# DoneApp — Esquema de Banco & Fluxos (DEV)

> **Ler primeiro**: Em **desenvolvimento**, sempre que houver ajuste de campos em tabelas já criadas, **NÃO** faremos rotinas de migração.  
> **Procedimento dev**: eu aviso → **você deleta a(s) tabela(s)** → ao iniciar, o app recria o **SQLite** com o schema novo.

## 0) Contexto rápido
- DB: **SQLite** (`data/app.db`).
- API: FastAPI.
- Auth atual: login simples + **SSO YouTube (Google OAuth)**: `/api/oauth/google/...`.
- Criptografia: `cryptography` (Fernet) — tokens de integrações serão guardados **criptografados**.
- Rate limiting & IP rules: já há UI/arquivo; pode virar tabela no futuro.

## 1) Tabelas

### 1.1) `users`
Usuários do sistema (inclui locais e SSO).

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
  sso_google_sub    TEXT UNIQUE,                     -- 'sub' do OIDC (se SSO Google/YouTube)
  status            TEXT    NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending','approved','blocked')),
  is_admin          INTEGER NOT NULL DEFAULT 0,      -- 0/1
  created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_used_at      TIMESTAMP,
  last_accessed_ip  TEXT                             -- IP textual
);

Regras:
	•	username e email únicos.
	•	status:
	•	pending (aguardando liberação),
	•	approved (liberado),
	•	blocked (bloqueado).
	•	Seed admin: se users estiver vazia na inicialização, criar admin a partir de .env
(ADMIN_USER, ADMIN_EMAIL, ADMIN_PASSWORD, opcional ADMIN_FULL_NAME).
is_admin=1, status='approved'.

1.2) logs

Auditoria de tudo por IP/usuário.

CREATE TABLE IF NOT EXISTS logs (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     INTEGER,           -- pode ser NULL (ex.: erro login antes de identificar)
  username    TEXT,              -- cópia momentânea (ajuda em auditoria)
  ip          TEXT NOT NULL,
  action      TEXT NOT NULL,     -- ex.: 'signup.request', 'login.ok', 'login.fail', 'sso.google.connect', ...
  details     TEXT,              -- JSON/texto livre
  created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

Eventos que devem logar: criação de usuário, tentativas de login (ok/fail), logout, refresh, bloqueios, alterações de perfil, criação/remoção de integrações, admin actions etc.

1.3) config

Chave-valor para parametrizações do sistema.

CREATE TABLE IF NOT EXISTS config (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  key         TEXT NOT NULL UNIQUE,    -- ex.: 'rate.login.per_ip.10m', 'smtp.host'
  description TEXT,
  value       TEXT NOT NULL,           -- string sempre (números também como string)
  updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
Usos: limites por IP, janelas de tempo, toggles, templates default, chaves públicas, etc.

1.4) integrations

Tokens e contas externas (YouTube/Google inicialmente).

CREATE TABLE IF NOT EXISTS integrations (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id          INTEGER NOT NULL,
  provider         TEXT    NOT NULL,              -- 'google'
  account_id       TEXT,                          -- ex.: OIDC 'sub' ou id do canal
  display_name     TEXT,
  scopes           TEXT,                          -- string única com escopos
  enc_access_token BLOB,                          -- Fernet
  enc_refresh_token BLOB,
  expires_at       TIMESTAMP,                     -- quando expira o access_token
  created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (user_id, provider),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

	•	Criptografia: usar chave Fernet vinda do .env (FERNET_KEY).
	•	Rotação: ideal ter key_version futuramente.

Observação: Limites por IP hoje vivem em arquivo/JSON; quando migrarmos para DB, criar uma tabela ip_rules (admin) e ip_events (para contagem/estatística), mas por ora mantemos como está.

⸻

2) Campo class (string de 10 dígitos)

Representa pedidos e confirmações de meios de autenticação/contato.
	•	Cada dígito: um canal.
	•	Valores: 0 = não solicitado; 1 = solicitado; 2 = confirmado.

Mapa sugerido (10 posições):
	1.	class[0] → E-mail
	2.	class[1] → SMS
	3.	class[2] → WhatsApp
	4.	class[3] → Ligação
	5.	class[4] → Admin
	6.	class[5] → YouTube/Google SSO
	7.	class[6] → Facebook SSO
	8.	class[7] → GitHub SSO
	9.	class[8] → TikTok SSO
	10.	class[9] → Reserva/Futuro

Exemplos:
	•	Usuário pediu SMS: class[1] de 0 → 1.
	•	Confirmou SMS: class[1] de 1 → 2.
	•	Conectou via Google SSO com sucesso: class[5] = 2.
	•	Se apenas tentou e negou, pode ficar 1.

Validação: CHECK(length(class)=10) para manter consistência.

⸻

3) Fluxos

3.1) Cadastro via SSO YouTube
	1.	Usuário clica YouTube no login.
	2.	Google OAuth → callback → criamos sid em memória (10 min) com profile + tokens.
	3.	Redireciona para /web/register_v2.html?sid=....
	4.	Tela pré-preenche Nome/Email/Avatar; senha opcional (SSO).
	5.	Ao confirmar:
	•	se email já existe:
	•	se status='pending': informar “aguardando liberação”.
	•	se approved: informar “usuário já cadastrado”.
	•	se não existe:
	•	cria em users com sso_google_sub, status conforme política (ex.: pending por padrão).
	•	cria/atualiza integrations com tokens criptografados.
	•	class[5]='2' (SSO confirmado).
	6.	Logar tudo em logs.

3.2) Cadastro manual (sem SSO)
	1.	Usuário abre /web/register_v2.html sem sid.
	2.	Preenche dados, aceita termos; senha obrigatória.
	3.	Backend cria users com status='pending' (ou approved se política permitir).
	4.	Log correspondente em logs.

3.3) Login
	•	Por e-mail ou username (se contiver @ → email; senão, username).
	•	Verifica status:
	•	pending → negar com mensagem “aguardando liberação”.
	•	blocked → negar com “acesso bloqueado”.
	•	approved → ok.

⸻

4) Seed do Admin

Na inicialização:
	•	Se SELECT COUNT(*) FROM users = 0:
	•	ler .env: ADMIN_USER, ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_FULL_NAME (opcional).
	•	inserir com is_admin=1, status='approved'.
	•	class pode iniciar com class[4]='2' (via Admin).

⸻

5) Notas de implementação
	•	Criptografia Fernet: FERNET_KEY no .env; usar MultiFernet para rotação futura.
	•	Validações: username sem @ e sem espaços; email válido; phone livre.
	•	Logs: padronizar action (namespace) e guardar details como JSON.
	•	Dev reset: em mudança de schema, deletar tabela → app cria novamente.

⸻

6) Próximos passos sugeridos
	•	Ligar register_v2.html ao backend real (endpoints /api/signup e /api/sso/finalize).
	•	Persistir tokens YouTube criptografados em integrations.
	•	Tela Admin: aprovar usuários (status), ver logs, gerenciar templates.
	•	Migrar rate-limit/ban IP para tabelas (ou manter arquivo + cache).
