from processing.text_processor import (
    remove_html,
    normalize_whitespace,
    remove_special_characters,
    truncate,
    build_processed_text,
)


class TestRemoveHtml:
    def test_remove_tags_basicas(self):
        assert remove_html("<p>Texto simples</p>") == "Texto simples"

    def test_remove_tags_aninhadas(self):
        assert remove_html("<div><strong>Negrito</strong> normal</div>") == "Negrito normal"

    def test_texto_sem_html_inalterado(self):
        assert remove_html("Texto limpo") == "Texto limpo"

    def test_none_retorna_vazio(self):
        assert remove_html(None) == ""

    def test_vazio_retorna_vazio(self):
        assert remove_html("") == ""


class TestNormalizeWhitespace:
    def test_espacos_duplos_viram_simples(self):
        assert normalize_whitespace("texto  com   espacos") == "texto com espacos"

    def test_quebras_excessivas_reduzidas(self):
        result = normalize_whitespace("linha1\n\n\n\nlinha2")
        assert result == "linha1\n\nlinha2"

    def test_strip_nas_bordas(self):
        assert normalize_whitespace("  texto  ") == "texto"


class TestRemoveSpecialCharacters:
    def test_remove_caracteres_estranhos(self):
        result = remove_special_characters("Texto @ com # símbolos!")
        assert "@" not in result
        assert "#" not in result

    def test_preserva_pontuacao_comum(self):
        result = remove_special_characters("Título: descrição, prazo.")
        assert ":" in result
        assert "," in result
        assert "." in result

    def test_preserva_letras_acentuadas(self):
        result = remove_special_characters("inscrição, educação, inovação")
        assert "inscrição" in result


class TestTruncate:
    def test_texto_curto_nao_truncado(self):
        texto = "Texto curto"
        assert truncate(texto, max_chars=100) == texto

    def test_texto_longo_truncado(self):
        texto = "palavra " * 200
        result = truncate(texto, max_chars=100)
        assert len(result) <= 104
        assert result.endswith("...")

    def test_trunca_na_palavra(self):
        texto = "uma frase bem longa que deve ser cortada corretamente"
        result = truncate(texto, max_chars=20)
        assert not result.endswith(" ...")
        assert result.endswith("...")


class TestBuildProcessedText:
    def test_contem_titulo(self):
        result = build_processed_text(title="Edital CNPq", description="")
        assert "Título: Edital CNPq" in result

    def test_contem_organizacao(self):
        result = build_processed_text(title="Edital", description="", organization="CNPq")
        assert "Organização: CNPq" in result

    def test_contem_prazo(self):
        result = build_processed_text(title="Edital", description="", deadline="2026-12-31")
        assert "Prazo: 2026-12-31" in result

    def test_contem_descricao_limpa(self):
        result = build_processed_text(title="Edital", description="<p>Descrição do edital</p>")
        assert "Descrição: Descrição do edital" in result

    def test_html_removido_da_descricao(self):
        result = build_processed_text(title="Edital", description="<b>Negrito</b> texto")
        assert "<b>" not in result
        assert "Negrito texto" in result

    def test_sem_organizacao_e_prazo(self):
        result = build_processed_text(title="Edital", description="Texto")
        assert "Organização" not in result
        assert "Prazo" not in result