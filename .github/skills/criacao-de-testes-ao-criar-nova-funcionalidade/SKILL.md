---
name: criacao-de-testes-ao-criar-nova-funcionalidade
description: Cria e atualiza testes automatizados sempre que uma nova funcionalidade for implementada em Python. Use para TDD, regressao, pytest, mocks, monkeypatch, validacao de comportamento e cobertura de novos fluxos de negocio.
---

# Skill: criacao-de-testes-ao-criar-nova-funcionalidade

## Objetivo
Garantir que toda nova funcionalidade entregue no projeto venha acompanhada de testes automatizados relevantes, claros e executaveis com `pytest`, reduzindo regressao e aumentando confianca nas mudancas.

## Quando usar esta skill
Use esta skill sempre que houver:
- criacao de funcao, classe, modulo ou endpoint novo
- alteracao de regra de negocio existente
- correcao de bug que deve virar teste de regressao
- mudanca em parsing, limpeza, transformacao ou persistencia de dados

Palavras-chave de ativacao:
- teste
- testes
- pytest
- tdd
- regressao
- monkeypatch
- mock
- cobertura
- nova funcionalidade
- validacao

## Resultado esperado
Ao final da tarefa, o agente deve:
- criar ou atualizar arquivos de teste em `backend/tests/`
- cobrir fluxo feliz e pelo menos um fluxo de erro/borda
- manter nomes de testes descritivos e focados em comportamento
- executar os testes relevantes e reportar resultado
- informar riscos remanescentes quando algo nao puder ser validado

## Convencoes do projeto
- Framework de testes: `pytest`
- Local dos testes: `backend/tests/`
- Nome dos arquivos: `test_<modulo>.py`
- Nome dos testes: `test_<comportamento_esperado>()`
- Estilo observado no repositorio:
  - uso de `monkeypatch` para isolar IO/rede
  - fixtures HTML inline para scrapers
  - asserts diretos e objetivos, sem complexidade desnecessaria

## Fluxo obrigatorio (passo a passo)
1. Entender a mudanca funcional
- Identificar entradas, saidas, efeitos colaterais e falhas esperadas.
- Determinar se o comportamento e puro (facil de testar) ou depende de rede/DB/arquivo.

2. Mapear impacto e pontos de teste
- Cobrir no minimo:
  - caminho principal de sucesso
  - pelo menos 1 caso de borda ou erro previsivel
  - regressao para bug corrigido (quando aplicavel)

3. Criar/atualizar testes antes de finalizar a implementacao
- Se possivel, escrever primeiro o teste que falha (TDD leve).
- Evitar acoplamento a detalhes internos da implementacao.
- Testar comportamento observavel: retorno, estado persistido, excecao, campos transformados.

4. Isolar dependencias externas
- Rede: usar `monkeypatch` em chamadas HTTP.
- Banco: preferir isolamento por mock/fake quando o teste nao for de integracao.
- Tempo/datas: controlar entradas para evitar flakiness.

5. Executar e validar
- Rodar testes do arquivo alterado primeiro.
- Se viavel, rodar conjunto maior relacionado.
- Em caso de impossibilidade (ex.: dependencia externa), explicitar o que nao foi validado.

6. Reportar com transparencia
- Listar arquivos criados/alterados.
- Resumir cenarios cobertos.
- Informar comando(s) executado(s) e status.

## Checklist de qualidade dos testes
- Teste falha quando a regra quebra de verdade.
- Nao depende de internet real nem de estado global fragil.
- Nomes deixam claro o comportamento validado.
- Arrange/Act/Assert legivel.
- Um motivo de falha por teste (escopo pequeno).
- Sem duplicacao desnecessaria.

## Padroes recomendados

### 1) Teste de transformacao/processamento
Quando a funcionalidade limpa ou transforma dados, validar campo a campo com exemplos realistas.

Exemplo:
```python
from datetime import date

from processing.prosas import process_prosas_opportunities


def test_process_prosas_opportunities_normalizes_fields():
	raw = [{
		"title": "  Edital X  ",
		"description": "<p>Texto <strong>limpo</strong>.</p>",
		"deadline": "2026-05-20",
		"link": "https://exemplo.com/oportunidade/1",
		"source_name": "Prosas",
		"source_url": "https://prosas.com.br",
	}]

	result = process_prosas_opportunities(raw)

	assert result[0]["title"] == "Edital X"
	assert result[0]["description"] == "Texto limpo."
	assert result[0]["deadline"] == date(2026, 5, 20)
```

### 2) Teste de coleta com dependencia externa
Quando a funcionalidade acessa HTTP, simular resposta com `monkeypatch`.

Exemplo:
```python
import importlib
import sys


class FakeResponse:
	def __init__(self, text, status_code=200):
		self.text = text
		self.status_code = status_code

	def raise_for_status(self):
		if self.status_code >= 400:
			raise RuntimeError("HTTP error")


def test_scrape_collects_items(monkeypatch):
	if "collectors.prosas" in sys.modules:
		del sys.modules["collectors.prosas"]

	prosas = importlib.import_module("collectors.prosas")

	html = """
	<html><body>
	  <article class='opportunity'>
		<a class='opportunity-link' href='/oportunidade/1'>Edital A</a>
	  </article>
	</body></html>
	"""

	monkeypatch.setattr(
		prosas.requests,
		"get",
		lambda url, headers=None, timeout=20: FakeResponse(html),
	)

	opportunities = prosas.scrape_prosas()
	assert len(opportunities) == 1
```

### 3) Teste de regressao de bug
Sempre que corrigir bug, adicionar teste que reproduz o cenario antigo e garante que nao volte.

Exemplo:
```python
def test_process_prosas_opportunities_handles_invalid_deadline_without_crash():
	raw = [{
		"title": "Edital Y",
		"description": "texto",
		"deadline": "data-invalida",
		"link": "https://exemplo.com/2",
		"source_name": "Prosas",
		"source_url": "https://prosas.com.br",
	}]

	result = process_prosas_opportunities(raw)
	assert result[0]["deadline"] is None
```

## Comandos de execucao recomendados
Executar a partir de `backend/`:

```bash
pytest -q
```

Ou focado em um arquivo:

```bash
pytest -q tests/test_prosas_processing.py
```

## Prompt templates para acionar a skill
- "Implemente a funcionalidade X e crie testes pytest cobrindo sucesso e borda."
- "Adicione teste de regressao para o bug Y e rode os testes relacionados."
- "Crie testes para o novo coletor com monkeypatch de requests.get."
- "Faça teste da funcionalidade X que foi criada"
- "Crie os testes da funcionalidade"
- "Faça testes"
- "Faça teste"

## Criterios de conclusao (Definition of Done)
- Nova funcionalidade implementada.
- Testes correspondentes criados/atualizados.
- Testes relevantes executados com sucesso localmente.
- Resultado reportado com riscos pendentes, se houver.