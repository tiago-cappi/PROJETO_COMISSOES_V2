"""
Testes unitários para ProcessMapper (módulo recebimento).

Testa o mapeamento de documentos da Análise Financeira para processos comerciais:

    REGRA 1 — COT (Adiantamento):
        Documento começa com "COT" → tipo = ADIANTAMENTO
        processo = sufixo numérico após "COT"
        Se processo tem Status="FATURADO" → InconsistenciaAdiantamentoError

    REGRA 2 — NF (Pagamento Regular):
        Extrai primeiros 6 dígitos do documento
        Busca na coluna "Numero NF" da Análise Comercial
        Mínimo 5 dígitos exigidos
        Zeros à esquerda removidos para comparação

Cenários cobertos:
    ── COT (Adiantamento) ──
    - COT seguido de número → mapeado como ADIANTAMENTO
    - COT sem sufixo numérico → não mapeado
    - COT com processo FATURADO → InconsistenciaAdiantamentoError
    - COT com status não-FATURADO → mapeado normalmente
    - Cache de resultado para COT

    ── NF (Pagamento Regular) ──
    - Documento com 6+ dígitos encontrados na NF → PAGAMENTO_REGULAR
    - Documento com 5 dígitos → aceito (mínimo)
    - Documento com menos de 5 dígitos → rejeitado
    - NF não encontrada na Análise Comercial → não mapeado
    - Zeros à esquerda ignorados na comparação
    - Cache de resultado para NF

    ── Casos especiais ──
    - Documento vazio/None → não mapeado
    - BOM nos nomes das colunas → removido automaticamente
    - Documentos não mapeados rastreados
"""

import pytest
import pandas as pd

from src.recebimento.core.process_mapper import ProcessMapper
from src.recebimento.exceptions import InconsistenciaAdiantamentoError


# =========================================================================
# HELPERS
# =========================================================================

def _criar_df_comercial(itens: list) -> pd.DataFrame:
    """Cria DataFrame simulando a Análise Comercial Completa."""
    if not itens:
        return pd.DataFrame(columns=["Processo", "Numero NF", "Status Processo"])
    return pd.DataFrame(itens)


def _criar_item_comercial(
    processo: str = "12345",
    numero_nf: str = "123456",
    status_processo: str = "ORCAMENTO",
    **extras,
) -> dict:
    """Cria um item da Análise Comercial."""
    item = {
        "Processo": processo,
        "Numero NF": numero_nf,
        "Status Processo": status_processo,
    }
    item.update(extras)
    return item


# =========================================================================
# CLASSE: TestCOTAdiantamento
# =========================================================================
@pytest.mark.unit
@pytest.mark.recebimento
class TestCOTAdiantamento:
    """Testa mapeamento de documentos COT (adiantamento)."""

    def test_cot_basico_mapeado(self, audit):
        """COT12345 → processo=12345, tipo=ADIANTAMENTO."""
        audit.set_contexto(modulo="ProcessMapper", cenario="COT basico")

        df = _criar_df_comercial([_criar_item_comercial(processo="12345")])
        mapper = ProcessMapper(df)
        resultado = mapper.mapear_documento("COT12345")

        audit.verificar(
            descricao="COT mapeado como ADIANTAMENTO",
            formula="COT prefix -> ADIANTAMENTO",
            entradas={"documento": "COT12345"},
            esperado="True",
            real=str(resultado["mapeado"]),
        )
        audit.verificar(
            descricao="Processo extraido do sufixo",
            formula="COT12345 -> 12345",
            entradas={"documento": "COT12345"},
            esperado="12345",
            real=resultado["processo"],
        )
        audit.verificar(
            descricao="Tipo = ADIANTAMENTO",
            formula="COT -> ADIANTAMENTO",
            entradas={},
            esperado="ADIANTAMENTO",
            real=resultado["tipo"],
        )

    def test_cot_com_espacos(self, audit):
        """COT com espaços é trimado e tratado com upper."""
        audit.set_contexto(modulo="ProcessMapper", cenario="COT com espacos")

        df = _criar_df_comercial([_criar_item_comercial(processo="99001")])
        mapper = ProcessMapper(df)
        resultado = mapper.mapear_documento("  cot99001  ")

        audit.verificar(
            descricao="COT com espacos e lowercase mapeado",
            formula="strip().upper() -> COT99001",
            entradas={"documento_raw": "  cot99001  "},
            esperado="True",
            real=str(resultado["mapeado"]),
        )

    def test_cot_sem_sufixo_numerico(self, audit):
        """COT sem número → não mapeado."""
        audit.set_contexto(modulo="ProcessMapper", cenario="COT sem numero")

        df = _criar_df_comercial([_criar_item_comercial()])
        mapper = ProcessMapper(df)
        resultado = mapper.mapear_documento("COTABC")

        audit.verificar(
            descricao="COT sem sufixo numerico nao mapeado",
            formula="isdigit() == False -> nao mapeado",
            entradas={"documento": "COTABC"},
            esperado="False",
            real=str(resultado["mapeado"]),
        )

    def test_cot_vazio_apos_prefixo(self, audit):
        """COT sozinho sem sufixo → não mapeado (string vazia não é dígito)."""
        audit.set_contexto(modulo="ProcessMapper", cenario="COT vazio")

        df = _criar_df_comercial([_criar_item_comercial()])
        mapper = ProcessMapper(df)
        resultado = mapper.mapear_documento("COT")

        audit.verificar(
            descricao="COT sem sufixo nao mapeado",
            formula="''.isdigit() == False",
            entradas={"documento": "COT"},
            esperado="False",
            real=str(resultado["mapeado"]),
        )

    def test_cot_processo_faturado_raise_erro(self, audit):
        """COT para processo FATURADO → InconsistenciaAdiantamentoError."""
        audit.set_contexto(modulo="ProcessMapper", cenario="COT FATURADO erro")

        df = _criar_df_comercial([
            _criar_item_comercial(processo="55555", status_processo="FATURADO"),
        ])
        mapper = ProcessMapper(df)

        erro_lancado = False
        try:
            mapper.mapear_documento("COT55555")
        except InconsistenciaAdiantamentoError as e:
            erro_lancado = True
            assert e.processo == "55555"
            assert e.documento == "COT55555"

        audit.verificar(
            descricao="InconsistenciaAdiantamentoError para COT FATURADO",
            formula="COT + FATURADO -> Exception",
            entradas={"documento": "COT55555", "status": "FATURADO"},
            esperado="True",
            real=str(erro_lancado),
        )

    def test_cot_processo_orcamento_ok(self, audit):
        """COT para processo ORCAMENTO → mapeado normalmente."""
        audit.set_contexto(modulo="ProcessMapper", cenario="COT ORCAMENTO ok")

        df = _criar_df_comercial([
            _criar_item_comercial(processo="66666", status_processo="ORCAMENTO"),
        ])
        mapper = ProcessMapper(df)
        resultado = mapper.mapear_documento("COT66666")

        audit.verificar(
            descricao="COT com ORCAMENTO aceito",
            formula="status != FATURADO -> ok",
            entradas={"documento": "COT66666", "status": "ORCAMENTO"},
            esperado="True",
            real=str(resultado["mapeado"]),
        )

    def test_cache_cot(self, audit):
        """Chamadas repetidas usam cache."""
        audit.set_contexto(modulo="ProcessMapper", cenario="Cache COT")

        df = _criar_df_comercial([_criar_item_comercial(processo="77777")])
        mapper = ProcessMapper(df)

        r1 = mapper.mapear_documento("COT77777")
        r2 = mapper.mapear_documento("COT77777")

        audit.verificar(
            descricao="Cache retorna mesmo resultado",
            formula="cache_mapeamento[doc]",
            entradas={"documento": "COT77777"},
            esperado=r1["processo"],
            real=r2["processo"],
        )
        # Verificar que o cache foi populado
        assert "COT77777" in mapper.cache_mapeamento


# =========================================================================
# CLASSE: TestNFPagamentoRegular
# =========================================================================
@pytest.mark.unit
@pytest.mark.recebimento
class TestNFPagamentoRegular:
    """Testa mapeamento de documentos NF (pagamento regular)."""

    def test_nf_6_digitos_encontrada(self, audit):
        """Documento com 6 dígitos → busca NF com sucesso."""
        audit.set_contexto(modulo="ProcessMapper", cenario="NF 6 digitos")

        df = _criar_df_comercial([
            _criar_item_comercial(processo="10001", numero_nf="123456"),
        ])
        mapper = ProcessMapper(df)
        resultado = mapper.mapear_documento("123456")

        audit.verificar(
            descricao="NF 6 digitos mapeada",
            formula="Busca NF na Analise Comercial",
            entradas={"documento": "123456", "nf_comercial": "123456"},
            esperado="True",
            real=str(resultado["mapeado"]),
        )
        audit.verificar(
            descricao="Tipo = PAGAMENTO_REGULAR",
            formula="NF -> PAGAMENTO_REGULAR",
            entradas={},
            esperado="PAGAMENTO_REGULAR",
            real=resultado["tipo"],
        )
        audit.verificar(
            descricao="Processo correto",
            formula="Busca retorna processo da linha",
            entradas={},
            esperado="10001",
            real=resultado["processo"],
        )

    def test_nf_com_prefixo_alfa(self, audit):
        """Documento 'NF123456' → extrai dígitos e busca."""
        audit.set_contexto(modulo="ProcessMapper", cenario="NF com prefixo alfa")

        df = _criar_df_comercial([
            _criar_item_comercial(processo="20002", numero_nf="123456"),
        ])
        mapper = ProcessMapper(df)
        resultado = mapper.mapear_documento("NF123456")

        audit.verificar(
            descricao="NF com prefixo alfa mapeada",
            formula="Extrai digitos: NF123456 -> 123456",
            entradas={"documento": "NF123456"},
            esperado="True",
            real=str(resultado["mapeado"]),
        )

    def test_nf_5_digitos_aceita(self, audit):
        """Documento com exatamente 5 dígitos → aceito (mínimo)."""
        audit.set_contexto(modulo="ProcessMapper", cenario="NF 5 digitos")

        df = _criar_df_comercial([
            _criar_item_comercial(processo="30003", numero_nf="12345"),
        ])
        mapper = ProcessMapper(df)
        resultado = mapper.mapear_documento("12345")

        audit.verificar(
            descricao="NF 5 digitos aceita (minimo)",
            formula="len(digits) >= 5 -> aceito",
            entradas={"documento": "12345", "num_digitos": 5},
            esperado="True",
            real=str(resultado["mapeado"]),
        )

    def test_nf_4_digitos_rejeitada(self, audit):
        """Documento com apenas 4 dígitos → rejeitado."""
        audit.set_contexto(modulo="ProcessMapper", cenario="NF 4 digitos")

        df = _criar_df_comercial([_criar_item_comercial()])
        mapper = ProcessMapper(df)
        resultado = mapper.mapear_documento("1234")

        audit.verificar(
            descricao="NF 4 digitos rejeitada",
            formula="len(digits) < 5 -> rejeitado",
            entradas={"documento": "1234", "num_digitos": 4},
            esperado="False",
            real=str(resultado["mapeado"]),
        )

    def test_nf_nao_encontrada(self, audit):
        """NF existente no documento mas não na Análise Comercial → não mapeado."""
        audit.set_contexto(modulo="ProcessMapper", cenario="NF nao encontrada")

        df = _criar_df_comercial([
            _criar_item_comercial(processo="40004", numero_nf="999999"),
        ])
        mapper = ProcessMapper(df)
        resultado = mapper.mapear_documento("111111")

        audit.verificar(
            descricao="NF nao encontrada na Analise Comercial",
            formula="mask == False para todos",
            entradas={"documento": "111111", "nf_existente": "999999"},
            esperado="False",
            real=str(resultado["mapeado"]),
        )

    def test_zeros_a_esquerda_ignorados(self, audit):
        """Zeros à esquerda são removidos para comparação."""
        audit.set_contexto(modulo="ProcessMapper", cenario="Zeros a esquerda")

        df = _criar_df_comercial([
            _criar_item_comercial(processo="50005", numero_nf="048341"),
        ])
        mapper = ProcessMapper(df)
        resultado = mapper.mapear_documento("048341")

        audit.verificar(
            descricao="Zeros a esquerda removidos na comparacao",
            formula="lstrip('0'): 048341 -> 48341",
            entradas={"documento": "048341", "nf_comercial": "048341"},
            esperado="True",
            real=str(resultado["mapeado"]),
        )

    def test_cache_nf(self, audit):
        """Chamadas repetidas para NF usam cache."""
        audit.set_contexto(modulo="ProcessMapper", cenario="Cache NF")

        df = _criar_df_comercial([
            _criar_item_comercial(processo="60006", numero_nf="654321"),
        ])
        mapper = ProcessMapper(df)

        r1 = mapper.mapear_documento("654321")
        r2 = mapper.mapear_documento("654321")

        audit.verificar(
            descricao="Cache NF retorna mesmo resultado",
            formula="cache_mapeamento[doc]",
            entradas={"documento": "654321"},
            esperado=r1["processo"],
            real=r2["processo"],
        )

    def test_nf_numeros_no_float(self, audit):
        """NF armazenada como float (ex: 48341.0) é normalizada."""
        audit.set_contexto(modulo="ProcessMapper", cenario="NF como float")

        df = _criar_df_comercial([
            _criar_item_comercial(processo="70007", numero_nf="48341.0"),
        ])
        mapper = ProcessMapper(df)
        resultado = mapper.mapear_documento("48341")

        audit.verificar(
            descricao="NF float normalizada (48341.0 -> 48341)",
            formula="regex extract digits, lstrip('0')",
            entradas={"documento": "48341", "nf_no_df": "48341.0"},
            esperado="True",
            real=str(resultado["mapeado"]),
        )


# =========================================================================
# CLASSE: TestCasosEspeciais
# =========================================================================
@pytest.mark.unit
@pytest.mark.recebimento
class TestCasosEspeciais:
    """Testa casos especiais e edge cases."""

    def test_documento_vazio(self, audit):
        """Documento vazio → não mapeado."""
        audit.set_contexto(modulo="ProcessMapper", cenario="Documento vazio")

        df = _criar_df_comercial([_criar_item_comercial()])
        mapper = ProcessMapper(df)
        resultado = mapper.mapear_documento("")

        audit.verificar(
            descricao="Documento vazio nao mapeado",
            formula="not documento -> False",
            entradas={"documento": ""},
            esperado="False",
            real=str(resultado["mapeado"]),
        )

    def test_documento_none(self, audit):
        """Documento None → não mapeado."""
        audit.set_contexto(modulo="ProcessMapper", cenario="Documento None")

        df = _criar_df_comercial([_criar_item_comercial()])
        mapper = ProcessMapper(df)
        resultado = mapper.mapear_documento(None)

        audit.verificar(
            descricao="Documento None nao mapeado",
            formula="pd.isna(None) -> True -> nao mapeado",
            entradas={"documento": "None"},
            esperado="False",
            real=str(resultado["mapeado"]),
        )

    def test_bom_nas_colunas_removido(self, audit):
        """BOM (Byte Order Mark) nos nomes das colunas é removido."""
        audit.set_contexto(modulo="ProcessMapper", cenario="BOM cleanup")

        df = pd.DataFrame([{
            "\ufeffProcesso": "88888",
            "Numero NF": "888888",
            "Status Processo": "ORCAMENTO",
        }])
        mapper = ProcessMapper(df)

        # Se BOM foi removido, col_processo deve ser encontrada
        audit.verificar(
            descricao="BOM removido dos nomes das colunas",
            formula="col.replace(BOM, '')",
            entradas={"coluna_com_bom": "\\ufeffProcesso"},
            esperado="True",
            real=str(mapper.col_processo is not None),
        )

    def test_documentos_nao_mapeados_rastreados(self, audit):
        """Documentos sem match ficam na lista documentos_nao_mapeados."""
        audit.set_contexto(modulo="ProcessMapper", cenario="Rastreamento nao mapeados")

        df = _criar_df_comercial([_criar_item_comercial(numero_nf="999999")])
        mapper = ProcessMapper(df)

        mapper.mapear_documento("111111")
        mapper.mapear_documento("COTABC")

        nao_mapeados = mapper.obter_documentos_nao_mapeados()

        audit.verificar(
            descricao="Documentos nao mapeados rastreados",
            formula="len(documentos_nao_mapeados) >= 2",
            entradas={"doc1": "111111", "doc2": "COTABC"},
            esperado=2,
            real=len(nao_mapeados),
        )

    def test_df_comercial_vazio(self, audit):
        """DataFrame vazio → nenhuma NF encontrada."""
        audit.set_contexto(modulo="ProcessMapper", cenario="DF vazio")

        df = pd.DataFrame(columns=["Processo", "Numero NF", "Status Processo"])
        mapper = ProcessMapper(df)
        resultado = mapper.mapear_documento("123456")

        audit.verificar(
            descricao="DF vazio -> NF nao encontrada",
            formula="df_comercial.empty -> None",
            entradas={"documento": "123456"},
            esperado="False",
            real=str(resultado["mapeado"]),
        )

    def test_obter_documentos_nao_mapeados_vazio(self, audit):
        """Sem documentos não mapeados → DataFrame vazio."""
        audit.set_contexto(modulo="ProcessMapper", cenario="Nao mapeados vazio")

        df = _criar_df_comercial([_criar_item_comercial(processo="11111")])
        mapper = ProcessMapper(df)

        nao_mapeados = mapper.obter_documentos_nao_mapeados()

        audit.verificar(
            descricao="Sem nao mapeados -> DF vazio",
            formula="len(documentos_nao_mapeados) == 0",
            entradas={},
            esperado=0,
            real=len(nao_mapeados),
        )

    def test_inconsistencia_to_dict(self, audit):
        """InconsistenciaAdiantamentoError.to_dict() retorna dict correto."""
        audit.set_contexto(modulo="ProcessMapper", cenario="Exception to_dict")

        erro = InconsistenciaAdiantamentoError(
            documento="COT99999",
            processo="99999",
            status_processo="FATURADO",
        )
        d = erro.to_dict()

        audit.verificar(
            descricao="to_dict error_type correto",
            formula="Classe do erro",
            entradas={},
            esperado="InconsistenciaAdiantamentoError",
            real=d["error_type"],
        )
        audit.verificar(
            descricao="to_dict documento correto",
            formula="erro.documento",
            entradas={},
            esperado="COT99999",
            real=d["documento"],
        )
