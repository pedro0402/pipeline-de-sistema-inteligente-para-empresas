---
name: documentacao-automatica-a-cada-mudanca
description: Documenta automaticamente cada mudanca de codigo no momento da implementacao. Use para atualizar README, adicionar docstrings, registrar changelog tecnico, explicar impacto da alteracao e manter historico de decisoes. Palavras-chave: documentacao, changelog, README, docstring, rastreabilidade, impacto, alteracao de codigo.
---

# Skill: documentacao-automatica-a-cada-mudanca

## Objetivo
Garantir que toda alteracao de codigo seja acompanhada de documentacao objetiva e util no mesmo fluxo da implementacao, aumentando precisao tecnica, rastreabilidade e manutencao futura.

## Quando usar esta skill
Use esta skill sempre que houver:
- criacao de funcionalidade nova
- alteracao de regra de negocio existente
- correcao de bug
- refatoracao com impacto comportamental
- mudanca de contrato (entrada/saida de funcoes, API, modelo)

Palavras-chave de ativacao:
- documentar
- documentacao
- changelog
- README
- docstring
- registrar alteracao
- resumo da mudanca
- impacto da mudanca

## Resultado esperado
Ao final da tarefa, o agente deve:
- atualizar a documentacao tecnica correspondente a mudanca
- registrar o que mudou, por que mudou e impacto esperado
- explicitar comportamento anterior vs comportamento atual
- incluir passos de validacao (testes/comandos) quando aplicavel
- manter texto curto, verificavel e sem ambiguidade

## Fontes de verdade para documentar
Priorizar nesta ordem:
1. Codigo alterado (implementacao final)
2. Testes adicionados/atualizados
3. Comandos executados e resultados
4. Contexto funcional informado pelo usuario

Nunca inventar comportamento nao presente no codigo.

## Onde documentar (regras praticas)
1. Mudanca de uso do sistema
- Atualizar `README.md` quando alterar configuracao, execucao, fluxo principal ou contrato visivel ao usuario.

2. Mudanca de comportamento interno relevante
- Adicionar/atualizar docstring em funcoes, classes e metodos alterados.
- Focar em entradas, saidas, efeitos colaterais e excecoes esperadas.

3. Mudanca com impacto de historico
- Criar/atualizar `CHANGELOG.md` (ou `docs/changelog.md`, se existir) com:
  - data
  - tipo da mudanca (feat, fix, refactor, docs, test)
  - descricao objetiva
  - impacto

4. Mudanca de API/contrato
- Documentar campos obrigatorios, defaults, validacoes e erros possiveis.

## Fluxo obrigatorio (passo a passo)
1. Mapear o diff da alteracao
- Identificar arquivos alterados e o tipo de mudanca em cada um.

2. Classificar o impacto
- `alto`: muda contrato, persistencia ou regra central.
- `medio`: altera comportamento interno observado por testes.
- `baixo`: ajuste interno sem mudanca funcional.

3. Aplicar documentacao minima por impacto
- Alto: README + docstrings + changelog.
- Medio: docstrings + changelog curto.
- Baixo: docstring pontual (se necessario) ou comentario tecnico breve.

4. Registrar validacao
- Informar testes/comandos executados e status.
- Se algo nao foi validado, declarar explicitamente.

5. Fechar com resumo verificavel
- "O que mudou", "Por que mudou", "Impacto", "Como validar".

## Template de changelog tecnico
Use este formato quando houver arquivo de changelog:

```md
## YYYY-MM-DD

### feat|fix|refactor|docs|test: titulo curto
- O que mudou: ...
- Por que mudou: ...
- Impacto: ...
- Validacao: ...
```

## Template de docstring (Python)
```python
def exemplo(param1: str, param2: int) -> dict:
    """Resume o comportamento da funcao.

    Args:
        param1: Significado funcional do parametro.
        param2: Restricoes ou formato esperado.

    Returns:
        Estrutura retornada e semantica dos campos principais.

    Raises:
        ValueError: Quando entradas invalidas forem recebidas.
    """
```

## Regras de qualidade da documentacao
- Texto curto e tecnico, sem marketing.
- Frases verificaveis no codigo/testes.
- Sem repetir obviedades da sintaxe.
- Explicar intencao e impacto, nao apenas "o que o codigo faz".
- Manter consistencia de termos no projeto.

## Antipadroes proibidos
- Documentar funcionalidade que nao foi implementada.
- Escrever changelog generico (ex.: "ajustes diversos").
- Omitir quebra de compatibilidade.
- Atualizar apenas codigo e deixar docs desatualizadas em mudancas de contrato.

## Prompt templates para acionar a skill
- "Implemente a mudanca X e documente automaticamente tudo o que for alterado."
- "A cada arquivo alterado, atualize docstrings e registre changelog tecnico."
- "Faca a feature Y e ja deixe README/changelog coerentes com a mudanca."
- "Corrija o bug Z e documente impacto e validacao."

## Criterios de conclusao (Definition of Done)
- Codigo alterado conforme solicitado.
- Documentacao correspondente atualizada no mesmo fluxo.
- Mudancas descritas com impacto e validacao.
- Nenhuma divergencia entre comportamento implementado e documentado.
