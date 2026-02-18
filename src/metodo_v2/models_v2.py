"""
src.metodo_v2.models_v2 - Modelos de dados para a Metodologia V2

Nova arquitetura baseada em:
- Colaboradores com cargo
- Regras de comissão por combinação hierárquica
- Faixas de comissão baseadas em valores absolutos de faturamento
- Sistema de prioridade por especificidade
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


# =============================================================================
# MODELOS DE CONFIGURAÇÃO
# =============================================================================

@dataclass
class FaixaComissao:
    """Representa uma faixa de comissão dentro de uma regra.
    
    Permite definir condições compostas:
    - Condição 1: limite_inferior operador_inferior FATURAMENTO
    - Condição 2 (opcional): FATURAMENTO operador_superior limite_superior
    
    Attributes:
        limite_inferior: Valor do primeiro limite (R$).
        taxa_comissao_pct: Taxa de comissão em percentual (ex: 0.5 = 0.5%).
        operador_inferior: Operador de comparação ('>=', '>', '<=', '<'). Default: '>='.
        limite_superior: Valor do segundo limite (R$), opcional.
        operador_superior: Operador da segunda condição ('>=', '>', '<=', '<'), opcional.
    
    Example:
        FaixaComissao(limite_inferior=10000, operador_inferior='>=', 
                     limite_superior=20000, operador_superior='<', taxa_comissao_pct=0.5)
        → Para 10000 <= FATURAMENTO < 20000, aplica 0.5% de comissão
    """
    limite_inferior: float
    taxa_comissao_pct: float
    operador_inferior: str = '>='
    limite_superior: Optional[float] = None
    operador_superior: Optional[str] = None

    def __post_init__(self):
        """Validações pós-inicialização."""
        if self.limite_inferior < 0:
            raise ValueError(f"limite_inferior não pode ser negativo: {self.limite_inferior}")
        if self.taxa_comissao_pct < 0:
            raise ValueError(f"taxa_comissao_pct não pode ser negativa: {self.taxa_comissao_pct}")
        
        # Validar operadores
        ops_validos = ['>=', '>', '<=', '<']
        if self.operador_inferior not in ops_validos:
            raise ValueError(f"operador_inferior inválido: {self.operador_inferior}. Use: {ops_validos}")
        if self.operador_superior and self.operador_superior not in ops_validos:
            raise ValueError(f"operador_superior inválido: {self.operador_superior}. Use: {ops_validos}")
        
        # Se tem limite superior, deve ter operador superior
        if self.limite_superior is not None and self.operador_superior is None:
            raise ValueError("Se limite_superior está definido, operador_superior também deve estar")
        if self.operador_superior is not None and self.limite_superior is None:
            raise ValueError("Se operador_superior está definido, limite_superior também deve estar")
    
    def aplica_ao_faturamento(self, faturamento: float) -> bool:
        """Verifica se esta faixa se aplica ao faturamento dado.
        
        Args:
            faturamento: Valor de faturamento a verificar (R$).
            
        Returns:
            True se o faturamento atende às condições desta faixa.
        """
        # Mapa de operadores
        ops_map = {
            '>=': lambda a, b: a >= b,
            '>': lambda a, b: a > b,
            '<=': lambda a, b: a <= b,
            '<': lambda a, b: a < b,
        }
        
        # Avaliar condição 1: faturamento operador_inferior limite_inferior
        # Ex: faturamento >= 50000
        op1_func = ops_map[self.operador_inferior]
        condicao1 = op1_func(faturamento, self.limite_inferior)
        
        # Se não tem segunda condição (limite_superior = None = infinito), retorna condição 1
        if self.limite_superior is None:
            return condicao1
        
        # Avaliar condição 2: faturamento operador_superior limite_superior
        # Ex: faturamento < 100000
        op2_func = ops_map[self.operador_superior]
        condicao2 = op2_func(faturamento, self.limite_superior)
        
        # Ambas devem ser verdadeiras (AND)
        return condicao1 and condicao2

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        result = {
            "limite_inferior": self.limite_inferior,
            "taxa_comissao_pct": self.taxa_comissao_pct,
            "operador_inferior": self.operador_inferior,
        }
        if self.limite_superior is not None:
            result["limite_superior"] = self.limite_superior
            result["operador_superior"] = self.operador_superior
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "FaixaComissao":
        """Cria instância a partir de dicionário."""
        return cls(
            limite_inferior=float(data.get("limite_inferior", 0)),
            taxa_comissao_pct=float(data.get("taxa_comissao_pct", 0)),
            operador_inferior=data.get("operador_inferior", ">="),
            limite_superior=float(data["limite_superior"]) if data.get("limite_superior") is not None else None,
            operador_superior=data.get("operador_superior"),
        )


@dataclass
class RegraComissao:
    """Representa uma regra de comissão para um colaborador.
    
    Uma regra define as faixas de comissão para uma combinação hierárquica
    específica. Campos com valor None são wildcards (match com qualquer valor).
    
    Attributes:
        colaborador: Nome do colaborador (FK).
        regra_id: ID único da regra dentro do colaborador.
        linha: Filtro de linha (None = qualquer).
        grupo: Filtro de grupo (None = qualquer).
        subgrupo: Filtro de subgrupo (None = qualquer).
        tipo_mercadoria: Filtro de tipo (None = qualquer).
        fabricante: Filtro de fabricante (None = qualquer).
        faixas: Lista de faixas de comissão ordenadas por limite_inferior.
    
    Example:
        RegraComissao(
            colaborador="André Caramello",
            regra_id=1,
            linha="Hidrologia",
            fabricante="QED",
            faixas=[
                FaixaComissao(0, 0.25),
                FaixaComissao(100000, 0.5),
                FaixaComissao(300000, 1.0),
            ]
        )
        → Regra para Hidrologia + QED (qualquer grupo/subgrupo/tipo)
        → Especificidade = 2
    """
    colaborador: str
    regra_id: int
    linha: Optional[str] = None
    grupo: Optional[str] = None
    subgrupo: Optional[str] = None
    tipo_mercadoria: Optional[str] = None
    fabricante: Optional[str] = None
    faixas: List[FaixaComissao] = field(default_factory=list)

    def __post_init__(self):
        """Validações e ordenação pós-inicialização."""
        if self.regra_id < 1:
            raise ValueError(f"regra_id deve ser >= 1, recebido: {self.regra_id}")
        # Ordenar faixas por limite_inferior
        self.faixas = sorted(self.faixas, key=lambda f: f.limite_inferior)

    @property
    def especificidade(self) -> int:
        """Calcula a especificidade da regra (0-5).
        
        Quanto mais campos definidos (não-None), maior a especificidade.
        Regras mais específicas têm prioridade sobre genéricas.
        """
        count = 0
        if self.linha is not None:
            count += 1
        if self.grupo is not None:
            count += 1
        if self.subgrupo is not None:
            count += 1
        if self.tipo_mercadoria is not None:
            count += 1
        if self.fabricante is not None:
            count += 1
        return count

    @property
    def filtros_definidos(self) -> Dict[str, str]:
        """Retorna apenas os filtros que estão definidos (não-None)."""
        filtros = {}
        if self.linha is not None:
            filtros["linha"] = self.linha
        if self.grupo is not None:
            filtros["grupo"] = self.grupo
        if self.subgrupo is not None:
            filtros["subgrupo"] = self.subgrupo
        if self.tipo_mercadoria is not None:
            filtros["tipo_mercadoria"] = self.tipo_mercadoria
        if self.fabricante is not None:
            filtros["fabricante"] = self.fabricante
        return filtros

    def match(self, linha: str, grupo: str, subgrupo: str, 
              tipo_mercadoria: str, fabricante: str) -> bool:
        """Verifica se esta regra dá match com uma combinação hierárquica.
        
        Args:
            linha, grupo, subgrupo, tipo_mercadoria, fabricante: Valores da hierarquia.
            
        Returns:
            True se todos os filtros definidos coincidem com os valores fornecidos.
        """
        if self.linha is not None and self.linha != linha:
            return False
        if self.grupo is not None and self.grupo != grupo:
            return False
        if self.subgrupo is not None and self.subgrupo != subgrupo:
            return False
        if self.tipo_mercadoria is not None and self.tipo_mercadoria != tipo_mercadoria:
            return False
        if self.fabricante is not None and self.fabricante != fabricante:
            return False
        return True

    def get_taxa_para_faturamento(self, faturamento: float) -> float:
        """Determina a taxa de comissão para um dado faturamento.
        
        Usa o método aplica_ao_faturamento() de cada faixa para verificar
        se o faturamento se encaixa nas condições definidas.
        
        Args:
            faturamento: Valor do faturamento em R$.
            
        Returns:
            Taxa de comissão em percentual.
        """
        if not self.faixas:
            return 0.0
        
        # Encontrar a primeira faixa cujas condições se aplicam
        for faixa in self.faixas:
            if faixa.aplica_ao_faturamento(faturamento):
                return faixa.taxa_comissao_pct
        
        # Se nenhuma faixa se aplicar, retorna 0
        return 0.0

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "colaborador": self.colaborador,
            "regra_id": self.regra_id,
            "linha": self.linha,
            "grupo": self.grupo,
            "subgrupo": self.subgrupo,
            "tipo_mercadoria": self.tipo_mercadoria,
            "fabricante": self.fabricante,
            "especificidade": self.especificidade,
            "faixas": [f.to_dict() for f in self.faixas],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RegraComissao":
        """Cria instância a partir de dicionário."""
        faixas = [FaixaComissao.from_dict(f) for f in data.get("faixas", [])]
        return cls(
            colaborador=data.get("colaborador", ""),
            regra_id=int(data.get("regra_id", 1)),
            linha=data.get("linha"),
            grupo=data.get("grupo"),
            subgrupo=data.get("subgrupo"),
            tipo_mercadoria=data.get("tipo_mercadoria"),
            fabricante=data.get("fabricante"),
            faixas=faixas,
        )


@dataclass
class RegraCentroCusto:
    """Representa uma regra de comissão por Centro de Custo (+ Fabricante opcional).
    
    No modo Centro de Custo, a comissão é calculada com base no faturamento
    total mensal do colaborador em cada combinação CC (+Fabricante).
    
    Attributes:
        colaborador: Nome do colaborador (FK).
        centro_custo: Código do centro de custo (ex: "2.5.031").
        fabricante: Fabricante específico (opcional). None = todos fabricantes do CC.
        faixas: Lista de faixas de comissão ordenadas por limite_inferior.
    
    Especificidade:
        - Regra com fabricante definido: especificidade = 2 (mais específica)
        - Regra sem fabricante (None): especificidade = 1 (genérica)
        
    Example:
        # Regra genérica para todo o CC
        RegraCentroCusto(
            colaborador="SAMANTA",
            centro_custo="2.5.031",
            fabricante=None,  # Todos fabricantes
            faixas=[FaixaComissao(0, 1.0), FaixaComissao(50000, 1.5)]
        )
        
        # Regra específica para um fabricante
        RegraCentroCusto(
            colaborador="SAMANTA",
            centro_custo="2.5.031",
            fabricante="BOSCH",  # Apenas BOSCH
            faixas=[FaixaComissao(0, 2.0), FaixaComissao(30000, 2.5)]
        )
        
        # Regra com split definido (quando há múltiplos Gerente Linha/Coordenador)
        RegraCentroCusto(
            colaborador="SAMANTA",
            centro_custo="2.5.031",
            fabricante=None,
            split=60.0,  # 60% para SAMANTA (JOÃO tem 40%)
            faixas=[FaixaComissao(0, 1.0)]
        )
    
    Split (Divisão de Comissão):
        - Aplicável apenas a cargos "Gerente Linha" e "Coordenador"
        - Se split=None e é único do cargo na regra (CC, Fab) → efetivo = 100%
        - Se split definido → usar valor (deve somar 100% com outros do mesmo cargo)
    """
    colaborador: str
    centro_custo: str
    fabricante: Optional[str] = None  # None = todos fabricantes do CC
    split: Optional[float] = None  # % de split (None = 100% se único do cargo)
    faixas: List[FaixaComissao] = field(default_factory=list)

    def __post_init__(self):
        """Validações e ordenação pós-inicialização."""
        if not self.centro_custo or not self.centro_custo.strip():
            raise ValueError("centro_custo não pode ser vazio")
        # Normalizar fabricante vazio para None
        if self.fabricante is not None and not self.fabricante.strip():
            self.fabricante = None
        # Ordenar faixas por limite_inferior
        self.faixas = sorted(self.faixas, key=lambda f: f.limite_inferior)

    @property
    def especificidade(self) -> int:
        """Calcula a especificidade da regra (1 ou 2).
        
        Regras mais específicas têm prioridade sobre genéricas.
        - 2: Regra com fabricante definido (mais específica)
        - 1: Regra sem fabricante (genérica, aplica a todos)
        """
        return 2 if self.fabricante else 1

    @property
    def chave_agrupamento(self) -> tuple:
        """Retorna a chave para agrupamento de faturamento.
        
        Returns:
            Tupla (centro_custo, fabricante) onde fabricante pode ser None.
        """
        return (self.centro_custo, self.fabricante)

    def match(self, centro_custo: str, fabricante: str) -> bool:
        """Verifica se esta regra se aplica a uma combinação CC + Fabricante.
        
        Args:
            centro_custo: Código do CC do item.
            fabricante: Fabricante do item.
            
        Returns:
            True se a regra se aplica (match exato ou regra genérica).
        """
        # CC deve coincidir sempre
        if self.centro_custo != centro_custo:
            return False
        
        # Se regra tem fabricante específico, deve coincidir
        if self.fabricante is not None:
            return self.fabricante == fabricante
        
        # Regra genérica (fabricante=None) aplica a qualquer fabricante
        return True

    def get_taxa_para_faturamento(self, faturamento: float) -> float:
        """Determina a taxa de comissão para um dado faturamento total.
        
        Args:
            faturamento: Valor do faturamento total no CC em R$.
            
        Returns:
            Taxa de comissão em percentual.
        """
        if not self.faixas:
            return 0.0
        
        # Iterar em ordem reversa (maior limite primeiro) para encontrar
        # a faixa mais alta que se aplica ao faturamento
        for faixa in reversed(self.faixas):
            if faixa.aplica_ao_faturamento(faturamento):
                return faixa.taxa_comissao_pct
        
        return 0.0

    def get_faixa_para_faturamento(self, faturamento: float) -> Optional[FaixaComissao]:
        """Retorna a faixa aplicável ao faturamento.
        
        Args:
            faturamento: Valor do faturamento total no CC em R$.
            
        Returns:
            FaixaComissao aplicável ou None.
        """
        # Iterar em ordem reversa para pegar a faixa mais alta
        for faixa in reversed(self.faixas):
            if faixa.aplica_ao_faturamento(faturamento):
                return faixa
        return None

    def get_split_decimal(self) -> float:
        """Retorna o split como decimal (0.0 a 1.0).
        
        Se split não definido (None), retorna 1.0 (100%).
        Cabe ao chamador verificar se há múltiplos do mesmo cargo.
        """
        if self.split is None:
            return 1.0
        return self.split / 100.0

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "colaborador": self.colaborador,
            "centro_custo": self.centro_custo,
            "fabricante": self.fabricante,
            "split": self.split,
            "faixas": [f.to_dict() for f in self.faixas],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RegraCentroCusto":
        """Cria instância a partir de dicionário."""
        faixas = [FaixaComissao.from_dict(f) for f in data.get("faixas", [])]
        split_val = data.get("split")
        return cls(
            colaborador=data.get("colaborador", ""),
            centro_custo=data.get("centro_custo", ""),
            fabricante=data.get("fabricante"),
            split=float(split_val) if split_val is not None else None,
            faixas=faixas,
        )


@dataclass
class ColaboradorV2:
    """Representa um colaborador na Metodologia V2.
    
    Attributes:
        nome: Nome completo do colaborador (PK única).
        cargo: Cargo do colaborador (FK para CARGOS_V2).
        regras: Lista de regras de comissão do colaborador (modo hierarquia).
        regras_cc: Lista de regras de comissão por Centro de Custo (modo CC).
        tipo_comissao: Tipo de comissão do colaborador: "faturamento" ou "recebimento".
                       Default: "faturamento" (compatibilidade retroativa).
        taxa_adiantamento_pct: Taxa fixa (%) para comissões de adiantamentos.
                               Obrigatória se tipo_comissao = "recebimento".
    """
    nome: str
    cargo: str
    regras: List[RegraComissao] = field(default_factory=list)
    regras_cc: List[RegraCentroCusto] = field(default_factory=list)
    tipo_comissao: str = "faturamento"  # "faturamento" ou "recebimento"
    taxa_adiantamento_pct: Optional[float] = None  # Taxa fixa para adiantamentos

    def __post_init__(self):
        """Validações pós-inicialização."""
        if not self.nome or not self.nome.strip():
            raise ValueError("nome do colaborador não pode ser vazio")
        
        # Normalizar tipo_comissao
        self.tipo_comissao = (self.tipo_comissao or "faturamento").strip().lower()
        if self.tipo_comissao not in ("faturamento", "recebimento"):
            raise ValueError(
                f"tipo_comissao inválido: '{self.tipo_comissao}'. "
                "Valores aceitos: 'faturamento' ou 'recebimento'"
            )
        
        # Validar taxa_adiantamento_pct para colaboradores de recebimento
        if self.tipo_comissao == "recebimento":
            if self.taxa_adiantamento_pct is None:
                raise ValueError(
                    f"Colaborador '{self.nome}' com tipo_comissao='recebimento' "
                    "deve ter taxa_adiantamento_pct definida"
                )
            if self.taxa_adiantamento_pct <= 0 or self.taxa_adiantamento_pct > 100:
                raise ValueError(
                    f"taxa_adiantamento_pct deve ser > 0 e <= 100, "
                    f"recebido: {self.taxa_adiantamento_pct}"
                )
        
        # Ordenar regras por especificidade (maior primeiro) para match eficiente
        self.regras = sorted(self.regras, key=lambda r: r.especificidade, reverse=True)

    def adicionar_regra(self, regra: RegraComissao) -> None:
        """Adiciona uma regra de hierarquia e reordena por especificidade."""
        self.regras.append(regra)
        self.regras = sorted(self.regras, key=lambda r: r.especificidade, reverse=True)

    def adicionar_regra_cc(self, regra: RegraCentroCusto) -> None:
        """Adiciona uma regra de Centro de Custo e reordena por especificidade."""
        self.regras_cc.append(regra)
        # Ordenar por especificidade (maior primeiro) para match eficiente
        self.regras_cc = sorted(self.regras_cc, key=lambda r: r.especificidade, reverse=True)

    def get_regra_cc(self, centro_custo: str, fabricante: str = None) -> Optional[RegraCentroCusto]:
        """Busca a regra mais específica para uma combinação CC + Fabricante.
        
        Ordem de prioridade:
        1. Regra com CC + Fabricante exato (especificidade=2)
        2. Regra com CC genérica (fabricante=None, especificidade=1)
        
        Args:
            centro_custo: Código do CC (ex: "2.5.031").
            fabricante: Nome do fabricante (opcional).
            
        Returns:
            RegraCentroCusto mais específica se encontrada, None caso contrário.
        """
        # Primeiro, buscar regra específica (CC + Fabricante)
        if fabricante:
            for regra in self.regras_cc:
                if regra.centro_custo == centro_custo and regra.fabricante == fabricante:
                    return regra
        
        # Fallback: buscar regra genérica (só CC)
        for regra in self.regras_cc:
            if regra.centro_custo == centro_custo and regra.fabricante is None:
                return regra
        
        return None

    def get_todas_regras_cc_para_centro_custo(self, centro_custo: str) -> List[RegraCentroCusto]:
        """Retorna todas as regras (genéricas e específicas) para um CC.
        
        Args:
            centro_custo: Código do CC.
            
        Returns:
            Lista de regras ordenadas por especificidade (maior primeiro).
        """
        regras = [r for r in self.regras_cc if r.centro_custo == centro_custo]
        return sorted(regras, key=lambda r: r.especificidade, reverse=True)

    def tem_vinculo_cc(self, centro_custo: str) -> bool:
        """Verifica se o colaborador está vinculado a um Centro de Custo.
        
        Um colaborador está vinculado se possui uma regra para aquele CC.
        
        Args:
            centro_custo: Código do CC.
            
        Returns:
            True se tem vínculo (regra existe), False caso contrário.
        """
        return self.get_regra_cc(centro_custo) is not None

    def get_centros_custo_vinculados(self) -> List[str]:
        """Retorna lista de CCs aos quais o colaborador está vinculado."""
        return [regra.centro_custo for regra in self.regras_cc]

    def get_proxima_regra_id(self) -> int:
        """Retorna o próximo ID disponível para uma nova regra."""
        if not self.regras:
            return 1
        return max(r.regra_id for r in self.regras) + 1

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "nome": self.nome,
            "cargo": self.cargo,
            "regras": [r.to_dict() for r in self.regras],
            "regras_cc": [r.to_dict() for r in self.regras_cc],
            "tipo_comissao": self.tipo_comissao,
            "taxa_adiantamento_pct": self.taxa_adiantamento_pct,
            "centros_custo_vinculados": self.get_centros_custo_vinculados(),
        }
    
    @property
    def recebe_por_recebimento(self) -> bool:
        """Retorna True se o colaborador recebe comissão por recebimento."""
        return self.tipo_comissao == "recebimento"
    
    @property
    def recebe_por_faturamento(self) -> bool:
        """Retorna True se o colaborador recebe comissão por faturamento."""
        return self.tipo_comissao == "faturamento"

    @classmethod
    def from_dict(cls, data: dict) -> "ColaboradorV2":
        """Cria instância a partir de dicionário."""
        regras = [RegraComissao.from_dict(r) for r in data.get("regras", [])]
        regras_cc = [RegraCentroCusto.from_dict(r) for r in data.get("regras_cc", [])]
        taxa_adiant = data.get("taxa_adiantamento_pct")
        return cls(
            nome=data.get("nome", ""),
            cargo=data.get("cargo", ""),
            regras=regras,
            regras_cc=regras_cc,
            tipo_comissao=data.get("tipo_comissao", "faturamento"),
            taxa_adiantamento_pct=float(taxa_adiant) if taxa_adiant is not None else None,
        )


# =============================================================================
# MODELOS DE RESULTADO
# =============================================================================

@dataclass
class ResultadoHierarquia:
    """Resultado do cálculo de comissão para uma combinação hierárquica.
    
    Attributes:
        linha, grupo, subgrupo, tipo_mercadoria, fabricante: Identificadores da hierarquia.
        faturamento: Faturamento total nesta combinação.
        regra_aplicada: Regra que foi aplicada (a mais específica que deu match).
        taxa_aplicada: Taxa de comissão aplicada (%).
        comissao: Valor da comissão calculada (R$).
    """
    linha: str
    grupo: str
    subgrupo: str
    tipo_mercadoria: str
    fabricante: str
    faturamento: float
    regra_aplicada: Optional[RegraComissao]
    taxa_aplicada: float
    comissao: float

    @property
    def hierarquia_str(self) -> str:
        """Retorna a hierarquia como string formatada."""
        return f"{self.linha} > {self.grupo} > {self.subgrupo} > {self.tipo_mercadoria} > {self.fabricante}"

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "linha": self.linha,
            "grupo": self.grupo,
            "subgrupo": self.subgrupo,
            "tipo_mercadoria": self.tipo_mercadoria,
            "fabricante": self.fabricante,
            "faturamento": self.faturamento,
            "regra_id": self.regra_aplicada.regra_id if self.regra_aplicada else None,
            "especificidade_regra": self.regra_aplicada.especificidade if self.regra_aplicada else 0,
            "taxa_aplicada": self.taxa_aplicada,
            "comissao": self.comissao,
        }


@dataclass
class ResultadoColaboradorV2:
    """Resultado completo do cálculo de comissão para um colaborador.
    
    Attributes:
        nome_colaborador: Nome do colaborador.
        cargo: Cargo do colaborador.
        mes_ano: Período de referência (ex: "2026-01").
        faturamento_total: Soma de todos os faturamentos por hierarquia.
        comissao_total: Soma de todas as comissões por hierarquia.
        resultados_por_hierarquia: Detalhamento por combinação hierárquica.
        hierarquias_sem_regra: Combinações que não tiveram regra aplicável.
    """
    nome_colaborador: str
    cargo: str
    mes_ano: str
    faturamento_total: float
    comissao_total: float
    resultados_por_hierarquia: List[ResultadoHierarquia] = field(default_factory=list)
    hierarquias_sem_regra: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def quantidade_hierarquias(self) -> int:
        """Quantidade de combinações hierárquicas processadas."""
        return len(self.resultados_por_hierarquia)

    @property
    def taxa_media(self) -> float:
        """Taxa média ponderada de comissão."""
        if self.faturamento_total == 0:
            return 0.0
        return (self.comissao_total / self.faturamento_total) * 100

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "nome_colaborador": self.nome_colaborador,
            "cargo": self.cargo,
            "mes_ano": self.mes_ano,
            "faturamento_total": round(self.faturamento_total, 2),
            "comissao_total": round(self.comissao_total, 2),
            "taxa_media_pct": round(self.taxa_media, 4),
            "quantidade_hierarquias": self.quantidade_hierarquias,
            "resultados_por_hierarquia": [r.to_dict() for r in self.resultados_por_hierarquia],
            "hierarquias_sem_regra": self.hierarquias_sem_regra,
        }

    def to_summary_dict(self) -> dict:
        """Versão resumida para exibição."""
        return {
            "colaborador": self.nome_colaborador,
            "cargo": self.cargo,
            "faturamento": f"R$ {self.faturamento_total:,.2f}",
            "comissao": f"R$ {self.comissao_total:,.2f}",
            "taxa_media": f"{self.taxa_media:.2f}%",
            "hierarquias": self.quantidade_hierarquias,
        }
