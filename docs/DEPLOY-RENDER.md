# Deploy no Render

Este documento descreve como hospedar o projeto no [Render](https://render.com), usando o Supabase como banco de dados (já configurado no projeto).

---

## Visão geral da arquitetura

```
┌──────────────────────────── Render ────────────────────────────┐
│                                                                 │
│  ┌─────────────────────────┐   ┌─────────────────────────────┐ │
│  │ Web Service             │   │ Cron Job                    │ │
│  │ pipeline-api            │   │ pipeline-coleta             │ │
│  │ (Django + Gunicorn)     │   │ (run_pipeline.py --all)     │ │
│  └────────────┬────────────┘   └──────────────┬──────────────┘ │
│               │                               │                │
└───────────────┼───────────────────────────────┼────────────────┘
                │ SQLAlchemy                    │ SQLAlchemy
                ▼                               ▼
       ┌─────────────────────────────────────────────┐
       │            Supabase (Postgres)              │
       └─────────────────────────────────────────────┘
```

| Componente | Serviço no Render | Função |
|---|---|---|
| API REST (`/opportunities`) | **Web Service** | Atende o frontend 24/7 |
| Pipeline de coleta | **Cron Job** | Roda a cada 6h para **todas** as empresas cadastradas |
| Banco Postgres | — (fica no Supabase) | Persistência |
| Frontend React (futuro) | Static Site (Render/Vercel) | Consome a API |

O arquivo [`render.yaml`](../render.yaml) na raiz do repositório já descreve os dois serviços (Blueprint).

---

## Pré-requisitos no código (já atendidos)

| Item | Onde |
|---|---|
| `Django` e `gunicorn` no `requirements.txt` | `backend/requirements.txt` |
| Entrypoint WSGI | `backend/wsgi.py` |
| `DEBUG` e `ALLOWED_HOSTS` via variáveis de ambiente | `backend/settings.py` |
| Health check `GET /health` | `backend/api/views.py` + `backend/urls.py` |
| Blueprint dos serviços | `render.yaml` |
| Pipeline para todas as empresas | `python run_pipeline.py --all` |

---

## Passo a passo do deploy

### 1. Suba o código para o GitHub

Os arquivos acima precisam estar na branch `main` do repositório.

### 2. Crie a conta e conecte o repositório

1. Acesse [render.com](https://render.com) e faça login com GitHub.
2. Autorize o acesso ao repositório `pipeline-de-sistema-inteligente-para-empresas`.

### 3. Deploy via Blueprint

1. No dashboard do Render: **New → Blueprint**.
2. Selecione o repositório — o Render detecta o `render.yaml` e propõe os 2 serviços (`pipeline-api` e `pipeline-coleta`).
3. Preencha as variáveis marcadas como manuais (`sync: false`):

| Variável | Serviço | Valor |
|---|---|---|
| `DATABASE_URL` | ambos | URL do **pooler** do Supabase (porta `6543`), a mesma do `.env` local |
| `CORS_ALLOWED_ORIGINS` | API | URL do frontend (ex.: `https://seu-front.onrender.com`). Pode usar um placeholder enquanto o front não existir |

4. Clique em **Apply** — o Render builda e sobe os dois serviços.

Observações:

- `DJANGO_SECRET_KEY` é **gerada automaticamente** pelo Render (`generateValue: true`).
- `DEBUG=false` e `ALLOWED_HOSTS=pipeline-api.onrender.com` já vêm do blueprint. Se renomear o serviço, ajuste `ALLOWED_HOSTS` no `render.yaml` para o novo domínio.

### 4. Verifique a API

```bash
curl https://pipeline-api.onrender.com/health
# → {"status": "ok"}

curl "https://pipeline-api.onrender.com/opportunities?page_size=5"
curl "https://pipeline-api.onrender.com/opportunities/top?limit=10"
```

### 5. Verifique o Cron Job

- O agendamento padrão é `0 */6 * * *` (a cada 6 horas).
- O comando `python run_pipeline.py --all` coleta os editais **uma única vez** e avalia a relevância para **todas as empresas** cadastradas em `company_profile`.
- Para testar sem esperar o horário, use **Trigger Run** no painel do serviço `pipeline-coleta` e acompanhe os logs.

### 6. (Futuro) Frontend

Quando o frontend React existir:

1. Hospede como **Static Site** (Render) ou na Vercel/Netlify.
2. Configure `VITE_API_URL=https://pipeline-api.onrender.com` no front.
3. Atualize `CORS_ALLOWED_ORIGINS` na API com a URL real do front.

Detalhes de integração: [GUIA-FRONTEND.md](GUIA-FRONTEND.md).

---

## Variáveis de ambiente (referência)

| Variável | Serviço | Origem | Descrição |
|---|---|---|---|
| `DATABASE_URL` | API + Cron | manual | Conexão Postgres (pooler do Supabase, porta 6543) |
| `DJANGO_SECRET_KEY` | API | gerada pelo Render | Chave secreta do Django |
| `DEBUG` | API | blueprint (`false`) | Nunca deixar `true` em produção |
| `ALLOWED_HOSTS` | API | blueprint | Domínio(s) do serviço, separados por vírgula |
| `CORS_ALLOWED_ORIGINS` | API | manual | Origens do frontend, separadas por vírgula |

> **Importante:** o `.env` local **nunca** vai para o repositório. Em produção, as credenciais entram apenas no painel do Render.

---

## Rodando localmente em "modo produção" (teste)

```bash
cd backend
DEBUG=false ALLOWED_HOSTS=localhost,127.0.0.1 \
  ../venv/bin/gunicorn wsgi:application --bind 0.0.0.0:8000
```

---

## Limitações do plano gratuito

| Tema | Detalhe |
|---|---|
| Cold start | O Web Service "dorme" após ~15 min sem tráfego; a 1ª requisição seguinte leva ~30s |
| Cron Job | Tem limite de tempo de execução; o pipeline atual roda em ~1–3 min, dentro do limite |
| Produção real | Considere o plano pago (~US$ 7/mês por serviço) para evitar cold starts |

---

## Solução de problemas

| Sintoma | Causa provável | Solução |
|---|---|---|
| Build falha com `ModuleNotFoundError: django` | `requirements.txt` desatualizado | Confirmar `Django` e `gunicorn` listados |
| `400 Bad Request` em todas as rotas | `ALLOWED_HOSTS` sem o domínio do serviço | Ajustar env var `ALLOWED_HOSTS` |
| Erro de CORS no frontend | Origem do front não liberada | Ajustar `CORS_ALLOWED_ORIGINS` |
| `OperationalError` de conexão | `DATABASE_URL` errada ou rede | Conferir URL do pooler do Supabase (porta 6543) |
| Cron termina sem salvar nada | Nenhum edital com score ≥ 6 | Comportamento normal; conferir perfil da empresa |
