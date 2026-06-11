# Guia para o desenvolvedor Frontend (React)

Este documento explica como o frontend React deve se integrar com o backend Python deste projeto. Leia com atenção a seção **"Onde ficam as consultas ao banco"** — é o ponto que mais gera confusão.

---

## Visão geral da arquitetura

```
┌─────────────────┐         HTTP (JSON)          ┌──────────────────────────┐
│  React (front)  │  ─────────────────────────►  │  API Python (Django REST) │
│  fetch / axios  │  ◄─────────────────────────  │  backend/api/views.py     │
└─────────────────┘                              └────────────┬─────────────┘
                                                                │
                                                                │ SQLAlchemy
                                                                ▼
                                                     ┌──────────────────────┐
                                                     │  Postgres / Supabase  │
                                                     └──────────────────────┘

┌──────────────────────────┐
│  Pipeline (batch)        │  ──► também escreve no banco (não é chamado pelo React)
│  backend/run_pipeline.py │
└──────────────────────────┘
```

**Resumo:** o React **nunca** fala com o banco de dados. Ele só consome a API REST exposta pelo Python. Quem lê e escreve no Postgres é o backend.

---

## Onde ficam as consultas ao banco (não é no React)

| O que você precisa | Onde está no backend | Quem usa |
|---|---|---|
| Listar / filtrar oportunidades | `backend/api/views.py` → `list_opportunities` | Frontend |
| Top oportunidades por relevância | `backend/api/views.py` → `top_opportunities` | Frontend |
| Detalhe de uma oportunidade | `backend/api/views.py` → `opportunity_detail` | Frontend |
| Coletar editais e salvar no banco | `backend/run_pipeline.py` → `save_to_db` | Job/script (não é o React) |
| Modelos das tabelas | `backend/models/` | Backend apenas |
| Conexão com o banco | `backend/core/database.py` | Backend apenas |

### O que fazer no React

No frontend, crie uma camada de **serviços HTTP** (por exemplo `src/services/api.ts`) que chama os endpoints. **Não** instale `@supabase/supabase-js` para ler oportunidades, **não** use SQL no front, **não** duplique queries do Python.

Exemplo de organização sugerida:

```
src/
├── services/
│   └── api.ts          ← todas as chamadas HTTP ficam aqui
├── types/
│   └── opportunity.ts  ← interfaces TypeScript espelhando o JSON da API
├── hooks/
│   └── useOpportunities.ts
└── pages/
    └── OpportunitiesPage.tsx
```

Se precisar de um endpoint novo (ex.: listar perfis de empresa), peça ao time de backend para implementar em `backend/api/views.py`. O front só consome.

---

## Como conectar com o backend Python

### 1. URL base da API

Em desenvolvimento local, a API roda em:

```
http://localhost:8000
```

No React (Vite), configure uma variável de ambiente:

```env
# .env.local
VITE_API_URL=http://localhost:8000
```

E use no código:

```typescript
const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
```

Em produção, troque `VITE_API_URL` pela URL do servidor onde a API estiver deployada.

### 2. Subir a API localmente

A API Django já está pronta e testada: rotas em `backend/urls.py`, views em `backend/api/views.py` e CORS configurado em `backend/settings.py` (libera `http://localhost:5173` e `http://localhost:3000` por padrão).

Para subir o servidor:

```bash
cd backend
source ../venv/bin/activate  # ou o venv que você usa
python manage.py runserver 8000
```

A API fica disponível em `http://localhost:8000`. Teste rápido:

```bash
curl "http://localhost:8000/opportunities?page_size=5"
curl "http://localhost:8000/opportunities/top?limit=10"
curl "http://localhost:8000/opportunities/366"
```

Pré-requisito: `DATABASE_URL` configurada no `.env` da raiz do projeto (a API lê o banco via SQLAlchemy).

Você também pode validar o contrato JSON olhando os testes em `backend/tests/test_list_opportunities.py`, `test_top_opportunities.py` e `test_opportunity_detail.py`.

### 3. Exemplos de chamadas HTTP

#### Listagem paginada com filtros

```typescript
// src/services/api.ts
const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function fetchOpportunities(params?: {
  search?: string;
  organization?: string;
  location?: string;
  page?: number;
  page_size?: number;
}) {
  const query = new URLSearchParams();
  if (params?.search) query.set("search", params.search);
  if (params?.organization) query.set("organization", params.organization);
  if (params?.location) query.set("location", params.location);
  if (params?.page) query.set("page", String(params.page));
  if (params?.page_size) query.set("page_size", String(params.page_size));

  const res = await fetch(`${API_URL}/opportunities?${query}`);
  if (!res.ok) throw new Error(`Erro ${res.status}`);
  return res.json();
}
```

#### Top oportunidades (dashboard / destaques)

```typescript
export async function fetchTopOpportunities(limit = 10) {
  const res = await fetch(`${API_URL}/opportunities/top?limit=${limit}`);
  if (!res.ok) throw new Error(`Erro ${res.status}`);
  return res.json();
}
```

#### Detalhe por ID

```typescript
export async function fetchOpportunityById(id: number) {
  const res = await fetch(`${API_URL}/opportunities/${id}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Erro ${res.status}`);
  return res.json();
}
```

#### Com axios (alternativa)

```typescript
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
});

export const getOpportunities = (params?: Record<string, string | number>) =>
  api.get("/opportunities", { params }).then((r) => r.data);

export const getTopOpportunities = (limit = 10) =>
  api.get("/opportunities/top", { params: { limit } }).then((r) => r.data);

export const getOpportunity = (id: number) =>
  api.get(`/opportunities/${id}`).then((r) => r.data);
```

---

## Endpoints disponíveis (contrato da API)

Todos os endpoints são **GET** e retornam **JSON**. Não há autenticação por enquanto.

### `GET /opportunities`

Lista oportunidades com paginação e filtros opcionais.

| Query param | Tipo | Default | Descrição |
|---|---|---|---|
| `search` | string | — | Busca em título e descrição (case-insensitive) |
| `organization` | string | — | Filtra por organização |
| `location` | string | — | Filtra por localização |
| `page` | int | `1` | Página atual |
| `page_size` | int | `20` (máx. `100`) | Itens por página |

**Resposta:**

```json
{
  "count": 42,
  "page": 1,
  "page_size": 20,
  "results": [ /* array de oportunidades */ ]
}
```

Ordenação: mais recentes primeiro (`collected_at` desc).

---

### `GET /opportunities/top`

Retorna as oportunidades com maior `relevance_score`.

| Query param | Tipo | Default | Descrição |
|---|---|---|---|
| `limit` | int | `10` (máx. `50`) | Quantidade de resultados |

**Resposta:**

```json
{
  "count": 10,
  "results": [ /* array de oportunidades */ ]
}
```

---

### `GET /opportunities/{id}`

Detalhe de uma oportunidade.

- **200** — objeto da oportunidade
- **404** — `{ "detail": "Oportunidade não encontrada." }`

---

## Formato de uma oportunidade (TypeScript)

Use estas interfaces para tipar o que vem da API:

```typescript
export interface Source {
  id: number;
  name: string;
  base_url: string;
}

export interface Analysis {
  id: number;
  summary: string | null;
  relevance_score: number | null; // 0 a 10
  recommended_action: string | null; // ex.: "Candidatar-se", "Monitorar", "Ignorar"
}

export interface Opportunity {
  id: number;
  title: string;
  description: string | null;
  organization: string | null;
  deadline: string | null;       // formato "YYYY-MM-DD"
  link: string;
  location: string | null;
  collected_at: string | null;   // ISO 8601
  source: Source | null;
  analysis: Analysis | null;
}

export interface PaginatedOpportunities {
  count: number;
  page: number;
  page_size: number;
  results: Opportunity[];
}

export interface TopOpportunities {
  count: number;
  results: Opportunity[];
}
```

### Campos úteis para a UI

| Campo | Uso sugerido |
|---|---|
| `title`, `description` | Card / página de detalhe |
| `deadline` | Badge de prazo; formate com `new Date(deadline + "T00:00:00")` |
| `link` | Botão "Ver edital original" (abre em nova aba) |
| `source.name` | Chip da fonte (Prosas, PNCP, Finep) |
| `analysis.relevance_score` | Barra de relevância (0–10) |
| `analysis.summary` | Texto explicativo da análise |
| `analysis.recommended_action` | CTA ou cor do card |
| `location` | Filtro / exibição geográfica |

**Nota:** `processed_text` existe no banco (`OpportunityAnalysis`) mas **não** é exposto na API atual. Se precisar dele na UI, solicite ao backend.

---

## De onde vêm os dados (fluxo completo)

1. **Pipeline** (`python run_pipeline.py --company-id 1`) roda em background ou via cron:
   - Coleta editais de **Prosas**, **PNCP** e **FINEP**
   - Processa e normaliza campos
   - Calcula relevância com base no perfil da empresa (`CompanyProfile`)
   - Salva no Postgres apenas editais com score ≥ 6

2. **API** lê o que já foi persistido e entrega ao React.

O frontend **não dispara** a coleta de editais hoje. Se no futuro existir um botão "Atualizar editais", será um endpoint POST novo no backend — ainda não implementado.

---

## CORS (importante para desenvolvimento)

O CORS **já está configurado** no backend (`django-cors-headers` em `backend/settings.py`). As origens liberadas por padrão são:

- `http://localhost:5173` (Vite)
- `http://localhost:3000` (CRA/Next)

Se o front rodar em outra porta/host, defina `CORS_ALLOWED_ORIGINS` no `.env` do backend (origens separadas por vírgula):

```env
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:4321
```

Sintoma de CORS mal configurado: erro no console do tipo *"blocked by CORS policy"*. Nesse caso, confira a origem no `.env` — não contorne desabilitando segurança do browser.

Alternativa durante dev: proxy no Vite (`vite.config.ts`):

```typescript
export default defineConfig({
  server: {
    proxy: {
      "/opportunities": "http://localhost:8000",
    },
  },
});
```

Com proxy, use `fetch("/opportunities")` (sem URL absoluta) e o Vite repassa para o Python.

---

## Paginação no React (exemplo)

```typescript
function OpportunitiesList() {
  const [page, setPage] = useState(1);
  const [data, setData] = useState<PaginatedOpportunities | null>(null);

  useEffect(() => {
    fetchOpportunities({ page, page_size: 20 }).then(setData);
  }, [page]);

  const totalPages = data ? Math.ceil(data.count / data.page_size) : 0;

  return (
    <>
      {data?.results.map((opp) => (
        <OpportunityCard key={opp.id} opportunity={opp} />
      ))}
      <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
        Anterior
      </button>
      <span>Página {page} de {totalPages}</span>
      <button disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
        Próxima
      </button>
    </>
  );
}
```

---

## Tratamento de erros

| Status | Significado | O que fazer no front |
|---|---|---|
| `200` | Sucesso | Renderizar dados |
| `404` | Oportunidade não encontrada | Página/mensagem "não encontrado" |
| `500` | Erro interno (banco, etc.) | Toast genérico + retry |
| Rede / CORS | API offline ou CORS mal configurado | Verificar se backend está rodando |

---

## O que ainda **não** existe na API

Útil para não perder tempo implementando algo que não vai funcionar:

| Funcionalidade | Status |
|---|---|
| Autenticação / login | Não implementado |
| POST / PUT / DELETE | Não implementado (somente leitura) |
| Endpoint de `CompanyProfile` | Modelo existe no banco, mas sem rota na API |
| Disparar pipeline pelo front | Não implementado |
| WebSocket / realtime | Não implementado |

---

## Variáveis de ambiente (referência)

São do **backend**, não do React — só para contexto:

| Variável | Onde | Para quê |
|---|---|---|
| `DATABASE_URL` | `.env` (raiz do projeto) | Conexão Postgres (obrigatória) |
| `DJANGO_SECRET_KEY` | `.env` (raiz do projeto) | Django (tem default de dev) |
| `CORS_ALLOWED_ORIGINS` | `.env` (raiz do projeto) | Origens liberadas para o front (default: `localhost:5173,localhost:3000`) |
| `VITE_API_URL` | `frontend/.env.local` | URL da API no React |

O front **não** precisa de `DATABASE_URL` nem credenciais do Supabase.

---

## Checklist para começar

- [ ] Subir a API com `python manage.py runserver 8000` dentro de `backend/` (CORS já está liberado para `localhost:5173` e `localhost:3000`)
- [ ] Criar `src/services/api.ts` com as 3 funções (list, top, detail)
- [ ] Criar types em `src/types/opportunity.ts`
- [ ] Testar `GET /opportunities` no browser ou Postman antes de integrar na UI
- [ ] Implementar listagem com paginação e filtros (`search`, `organization`, `location`)
- [ ] Implementar tela de detalhe com tratamento de 404
- [ ] Usar `link` para abrir o edital na fonte original
- [ ] **Não** conectar o React diretamente ao Postgres/Supabase para ler oportunidades

---

## Contatos / arquivos de referência no repositório

| Arquivo | Conteúdo |
|---|---|
| `backend/api/views.py` | Contrato e lógica dos endpoints |
| `backend/urls.py` | Rotas HTTP da API |
| `backend/settings.py` | Configuração do Django (CORS, DRF) |
| `backend/tests/test_list_opportunities.py` | Exemplos de resposta da listagem |
| `backend/tests/test_top_opportunities.py` | Exemplos do endpoint `/top` |
| `backend/tests/test_opportunity_detail.py` | Exemplos de detalhe e 404 |
| `backend/models/opportunity.py` | Schema da entidade principal |
| `backend/run_pipeline.py` | Como os dados chegam ao banco |

Dúvidas sobre novos campos ou endpoints → falar com quem mantém o backend Python.
