# Pipeline de Sistema Inteligente para Empresas

Pipeline em Python para coletar oportunidades, processar dados e persistir resultados em banco relacional.

## O que este projeto faz
- Coleta oportunidades da fonte Prosas.
- Processa e normaliza campos (titulo, descricao, prazo, etc.).
- Persiste oportunidades no banco de dados sem duplicar links.
- Mantem suite de testes com pytest para garantir regressao controlada.

## Tecnologias
- Python 3.10+
- SQLAlchemy
- python-dotenv
- requests
- beautifulsoup4
- pytest

## Estrutura principal
- [backend/run_pipeline.py](backend/run_pipeline.py): orquestra coleta, processamento, persistencia e relatorio.
- [backend/collectors/prosas.py](backend/collectors/prosas.py): scraping de oportunidades.
- [backend/processing/prosas.py](backend/processing/prosas.py): limpeza e normalizacao dos dados.
- [backend/core/database.py](backend/core/database.py): engine e sessao do SQLAlchemy.
- [backend/models](backend/models): modelos de persistencia.
- [backend/tests](backend/tests): testes unitarios e de integracao.

## Setup rapido
1. Entrar na pasta do backend:

	cd backend

2. Criar e ativar ambiente virtual:

	# No Windows:
	python -m venv venv
	venv\Scripts\activatepip install -r requirements.txt

	# No Linux/Mac:
	python3 -m venv venv
	source venv/bin/activate

3. Instalar dependencias:

	pip install -r requirements.txt

4. Criar arquivo de ambiente:

	cp .env.example .env

	Se nao existir .env.example, crie manualmente:

	touch .env

5. Configurar variaveis no .env:

	DATABASE_URL=postgresql://USUARIO:SENHA@HOST:5432/NOME_DO_BANCO

6. Criar estrutura do banco de dados:
	Com o ambiente ativo, rode:

	python create_tables.py

7. Rodar as migrates:
	Com o ambiente ativo, rode:

	python seed_company.py
	
## Como rodar o projeto
	Com o ambiente ativo, rode:

	python manage.py runserver

## Variaveis de ambiente
- DATABASE_URL: obrigatoria para execucao do pipeline e testes de banco.
- SUPABASE_URL e SUPABASE_KEY: usadas apenas em teste de integracao especifico de API.

## Problemas comuns
1. Erro de conexao no banco
- Verifique formato e credenciais em DATABASE_URL.
- Confirme acesso de rede ao host do banco.

2. Erro de tabela inexistente
- Execute a etapa de inicializacao de tabelas antes do pipeline.

3. Testes de integracao sendo pulados
- Alguns testes usam skip automatico quando variaveis de ambiente nao estao configuradas.

## Boas praticas de contribuicao
- Sempre incluir testes ao adicionar funcionalidade.
- Atualizar documentacao no mesmo fluxo da alteracao de codigo.