"""
src.metodo_v2.recebimento_v2.state_manager_v2 - Gerenciador de Estado

Persiste o estado dos processos em Estado_Processos_Recebimento_V2.xlsx.

Estados possíveis:
- ADIANTAMENTO: Pagamento recebido mas ainda não faturado
- FATURADO: Processo foi faturado → dispara reconciliação
- RECONCILIADO: Ajuste de reconciliação já foi aplicado

Arquivo separado do método padrão para evitar conflitos.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set

import pandas as pd


logger = logging.getLogger(__name__)


class EstadoProcesso(Enum):
    """Estados possíveis de um processo."""
    ADIANTAMENTO = "ADIANTAMENTO"
    FATURADO = "FATURADO"
    RECONCILIADO = "RECONCILIADO"


@dataclass
class RegistroEstado:
    """Registro de estado de um processo.
    
    Attributes:
        documento_normalizado: Chave do processo (NF).
        estado: Estado atual.
        valor_adiantado: Valor do adiantamento original.
        comissao_adiantada: Comissão calculada no adiantamento.
        data_adiantamento: Data do pagamento do adiantamento.
        colaborador_id: ID do colaborador (para rastreio).
        data_faturamento: Data do faturamento (quando FATURADO).
        valor_faturado: Valor faturado (quando FATURADO).
        comissao_real: Comissão real calculada no faturamento.
        data_reconciliacao: Data da reconciliação (quando RECONCILIADO).
        ajuste_aplicado: Valor do ajuste aplicado.
    """
    documento_normalizado: str
    estado: EstadoProcesso
    valor_adiantado: float = 0.0
    comissao_adiantada: float = 0.0
    data_adiantamento: Optional[pd.Timestamp] = None
    colaborador_id: str = ""
    centro_custo: str = ""  # CC do documento (para reconciliação em modo CC)
    data_faturamento: Optional[pd.Timestamp] = None
    valor_faturado: float = 0.0
    comissao_real: float = 0.0
    data_reconciliacao: Optional[pd.Timestamp] = None
    ajuste_aplicado: float = 0.0
    mes_apuracao: int = 0
    ano_apuracao: int = 0
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "Documento Normalizado": self.documento_normalizado,
            "Estado": self.estado.value,
            "Valor Adiantado": self.valor_adiantado,
            "Comissão Adiantada": self.comissao_adiantada,
            "Data Adiantamento": self.data_adiantamento,
            "Colaborador ID": self.colaborador_id,
            "Centro Custo": self.centro_custo,
            "Data Faturamento": self.data_faturamento,
            "Valor Faturado": self.valor_faturado,
            "Comissão Real": self.comissao_real,
            "Data Reconciliação": self.data_reconciliacao,
            "Ajuste Aplicado": self.ajuste_aplicado,
            "Mês Apuração": self.mes_apuracao,
            "Ano Apuração": self.ano_apuracao
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "RegistroEstado":
        """Cria instância a partir de dicionário."""
        estado_str = data.get("Estado", "ADIANTAMENTO")
        try:
            estado = EstadoProcesso(estado_str)
        except ValueError:
            estado = EstadoProcesso.ADIANTAMENTO
        
        # Helper para converter datas com tratamento de None
        def parse_data(val):
            if val is None or (isinstance(val, str) and not val.strip()):
                return None
            try:
                return pd.to_datetime(val, errors='coerce')
            except Exception:
                return None
        
        return cls(
            documento_normalizado=str(data.get("Documento Normalizado", "")),
            estado=estado,
            valor_adiantado=float(data.get("Valor Adiantado", 0) or 0),
            comissao_adiantada=float(data.get("Comissão Adiantada", 0) or 0),
            data_adiantamento=parse_data(data.get("Data Adiantamento")),
            colaborador_id=str(data.get("Colaborador ID", "")),
            centro_custo=str(data.get("Centro Custo", "")),
            data_faturamento=parse_data(data.get("Data Faturamento")),
            valor_faturado=float(data.get("Valor Faturado", 0) or 0),
            comissao_real=float(data.get("Comissão Real", 0) or 0),
            data_reconciliacao=parse_data(data.get("Data Reconciliação")),
            ajuste_aplicado=float(data.get("Ajuste Aplicado", 0) or 0),
            mes_apuracao=int(data.get("Mês Apuração", 0) or 0),
            ano_apuracao=int(data.get("Ano Apuração", 0) or 0)
        )


class StateManagerV2:
    """Gerenciador de estado persistente para V2.
    
    Arquivo: Estado_Processos_Recebimento_V2.xlsx
    """
    
    NOME_ARQUIVO = "Estado_Processos_Recebimento_V2.xlsx"
    
    def __init__(self, base_path: str = "."):
        """Inicializa o gerenciador.
        
        Args:
            base_path: Caminho base (raiz do projeto).
        """
        self.base_path = Path(base_path)
        self.filepath = self.base_path / "dados_saida" / self.NOME_ARQUIVO
        self._cache: Dict[str, RegistroEstado] = {}
        self._carregado = False

    def _build_key(self, documento_normalizado: str, colaborador_id: str) -> str:
        """Monta chave única para documento + colaborador."""
        return f"{documento_normalizado}||{colaborador_id}"
    
    def carregar(self) -> None:
        """Carrega estado do arquivo Excel."""
        if self._carregado:
            return
        
        if not self.filepath.exists():
            logger.info(f"[V2-REC-STATE] Arquivo de estado não existe, iniciando vazio: {self.filepath}")
            self._cache = {}
            self._carregado = True
            return
        
        try:
            df = pd.read_excel(self.filepath, dtype={"Documento Normalizado": str})
            
            for _, row in df.iterrows():
                registro = RegistroEstado.from_dict(row.to_dict())
                key = self._build_key(registro.documento_normalizado, registro.colaborador_id)
                self._cache[key] = registro
            
            logger.info(f"[V2-REC-STATE] Carregados {len(self._cache)} registros de estado")
            self._carregado = True
            
        except Exception as e:
            logger.error(f"[V2-REC-STATE] Erro ao carregar estado: {e}")
            self._cache = {}
            self._carregado = True
    
    def salvar(self) -> None:
        """Salva estado para arquivo Excel."""
        # Garantir diretório existe
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        
        if not self._cache:
            logger.info("[V2-REC-STATE] Nenhum registro para salvar")
            return
        
        df = pd.DataFrame([r.to_dict() for r in self._cache.values()])
        
        # Ordenar por documento + colaborador
        df = df.sort_values(["Documento Normalizado", "Colaborador ID"]).reset_index(drop=True)
        
        df.to_excel(self.filepath, index=False)
        logger.info(f"[V2-REC-STATE] Salvos {len(df)} registros em {self.filepath}")
    
    def obter_estado(self, documento_normalizado: str, colaborador_id: Optional[str] = None) -> Optional[RegistroEstado]:
        """Obtém estado de um processo.
        
        Args:
            documento_normalizado: Chave do processo.
            
        Returns:
            RegistroEstado ou None se não existir.
        """
        self.carregar()
        if colaborador_id:
            return self._cache.get(self._build_key(documento_normalizado, colaborador_id))

        for registro in self._cache.values():
            if registro.documento_normalizado == documento_normalizado:
                return registro
        return None

    def registro_existe(self, documento_normalizado: str, colaborador_id: str) -> bool:
        """Verifica se já existe registro para documento + colaborador."""
        self.carregar()
        return self._build_key(documento_normalizado, colaborador_id) in self._cache
    
    def registrar_adiantamento(
        self,
        documento_normalizado: str,
        valor_adiantado: float,
        comissao_adiantada: float,
        data_adiantamento: pd.Timestamp,
        colaborador_id: str,
        mes: int,
        ano: int,
        centro_custo: str = ""
    ) -> RegistroEstado:
        """Registra um novo adiantamento.
        
        Args:
            documento_normalizado: Chave do processo.
            valor_adiantado: Valor do pagamento.
            comissao_adiantada: Comissão calculada.
            data_adiantamento: Data do pagamento.
            colaborador_id: ID do colaborador.
            mes: Mês de apuração.
            ano: Ano de apuração.
            centro_custo: Centro de custo do documento (para reconciliação CC).
            
        Returns:
            RegistroEstado criado/atualizado.
        """
        self.carregar()
        
        registro = RegistroEstado(
            documento_normalizado=documento_normalizado,
            estado=EstadoProcesso.ADIANTAMENTO,
            valor_adiantado=valor_adiantado,
            comissao_adiantada=comissao_adiantada,
            data_adiantamento=data_adiantamento,
            colaborador_id=colaborador_id,
            centro_custo=centro_custo,
            mes_apuracao=mes,
            ano_apuracao=ano
        )
        
        self._cache[self._build_key(documento_normalizado, colaborador_id)] = registro
        logger.debug(f"[V2-REC-STATE] Adiantamento registrado: {documento_normalizado}")
        
        return registro
    
    def marcar_faturado(
        self,
        documento_normalizado: str,
        valor_faturado: float,
        comissao_real: float,
        data_faturamento: pd.Timestamp,
        colaborador_id: Optional[str] = None
    ) -> Optional[RegistroEstado]:
        """Marca processo como faturado.
        
        Args:
            documento_normalizado: Chave do processo.
            valor_faturado: Valor do faturamento.
            comissao_real: Comissão real calculada.
            data_faturamento: Data do faturamento.
            
        Returns:
            RegistroEstado atualizado ou None se não existir.
        """
        self.carregar()
        
        registro = None
        if colaborador_id:
            registro = self._cache.get(self._build_key(documento_normalizado, colaborador_id))
        else:
            for item in self._cache.values():
                if item.documento_normalizado == documento_normalizado:
                    registro = item
                    break
        if not registro:
            logger.warning(f"[V2-REC-STATE] Processo não encontrado: {documento_normalizado}")
            return None
        
        if registro.estado != EstadoProcesso.ADIANTAMENTO:
            logger.warning(f"[V2-REC-STATE] Processo já foi processado: {documento_normalizado} ({registro.estado.value})")
            return registro
        
        registro.estado = EstadoProcesso.FATURADO
        registro.valor_faturado = valor_faturado
        registro.comissao_real = comissao_real
        registro.data_faturamento = data_faturamento
        
        logger.debug(f"[V2-REC-STATE] Marcado como FATURADO: {documento_normalizado}")
        
        return registro
    
    def marcar_reconciliado(
        self,
        documento_normalizado: str,
        ajuste_aplicado: float,
        colaborador_id: Optional[str] = None
    ) -> Optional[RegistroEstado]:
        """Marca processo como reconciliado.
        
        Args:
            documento_normalizado: Chave do processo.
            ajuste_aplicado: Valor do ajuste (pode ser negativo).
            
        Returns:
            RegistroEstado atualizado ou None se não existir.
        """
        self.carregar()
        
        registro = None
        if colaborador_id:
            registro = self._cache.get(self._build_key(documento_normalizado, colaborador_id))
        else:
            for item in self._cache.values():
                if item.documento_normalizado == documento_normalizado:
                    registro = item
                    break
        if not registro:
            logger.warning(f"[V2-REC-STATE] Processo não encontrado: {documento_normalizado}")
            return None
        
        if registro.estado != EstadoProcesso.FATURADO:
            logger.warning(f"[V2-REC-STATE] Processo não está FATURADO: {documento_normalizado}")
            return registro
        
        registro.estado = EstadoProcesso.RECONCILIADO
        registro.data_reconciliacao = pd.Timestamp.now()
        registro.ajuste_aplicado = ajuste_aplicado
        
        logger.debug(f"[V2-REC-STATE] Marcado como RECONCILIADO: {documento_normalizado} (ajuste={ajuste_aplicado:.2f})")
        
        return registro
    
    def listar_adiantamentos_pendentes(
        self, 
        colaborador_id: Optional[str] = None
    ) -> List[RegistroEstado]:
        """Lista adiantamentos pendentes de reconciliação.
        
        Args:
            colaborador_id: Filtrar por colaborador (opcional).
            
        Returns:
            Lista de registros com estado ADIANTAMENTO.
        """
        self.carregar()
        
        pendentes = [
            r for r in self._cache.values()
            if r.estado == EstadoProcesso.ADIANTAMENTO
        ]
        
        if colaborador_id:
            pendentes = [r for r in pendentes if r.colaborador_id == colaborador_id]
        
        return pendentes
    
    def listar_faturados_pendentes(self) -> List[RegistroEstado]:
        """Lista processos faturados aguardando reconciliação.
        
        Returns:
            Lista de registros com estado FATURADO.
        """
        self.carregar()
        
        return [
            r for r in self._cache.values()
            if r.estado == EstadoProcesso.FATURADO
        ]
    
    def documentos_ja_processados(self) -> Set[str]:
        """Retorna conjunto de documentos já processados.
        
        Returns:
            Set de documentos normalizados.
        """
        self.carregar()
        return {r.documento_normalizado for r in self._cache.values()}
    
    def limpar_cache(self) -> None:
        """Limpa cache para forçar recarga."""
        self._cache = {}
        self._carregado = False
