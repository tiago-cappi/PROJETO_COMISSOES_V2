"""
Gerenciamento de armazenamento persistente das taxas de câmbio em JSON.

Formato do arquivo `data/currency_rates/monthly_avg_rates.json`:

{
  "metadata": {
    "ultima_atualizacao": "2025-11-14T10:30:00",
    "ano_atual": 2025,
    "mes_atual": 11,
    "moedas_disponiveis": ["USD", "GBP"],
    "schema_version": 1
  },
  "taxas": {
    "2025": {
      "USD": {
        "1": {
          "taxa_media": 0.201234,
          "fonte": "exchangerate.host/timeseries",
          "dias_utilizados": 31,
          "data_atualizacao": "...",
          "fallback": false,
          "observacao": null
        },
        "2": { ... }
      },
      "GBP": { ... }
    },
    "2024": { ... }
  }
}
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class RateRecord:
    moeda: str
    ano: int
    mes: int
    taxa_media: float
    fonte: str
    dias_utilizados: int
    fallback: bool = False
    observacao: Optional[str] = None


class RateStorage:
    """
    Encapsula leitura/escrita do JSON de taxas de câmbio.

    Obs.: Esta classe é intencionalmente genérica e NÃO conhece regras de negócio
    de comissões – apenas armazena e recupera taxas.
    """

    def __init__(
        self, json_path: str = "data/currency_rates/monthly_avg_rates.json"
    ) -> None:
        self.json_path = Path(json_path)
        self._data: Dict = {}
        self._ensure_structure()

    # ------------------------------------------------------------------
    # Estrutura básica do arquivo
    # ------------------------------------------------------------------
    def _ensure_structure(self) -> None:
        """Garante que a pasta e o arquivo JSON existam com estrutura mínima."""
        try:
            self.json_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.json_path.exists():
                base = {
                    "metadata": {
                        "ultima_atualizacao": None,
                        "ano_atual": None,
                        "mes_atual": None,
                        "moedas_disponiveis": [],
                        "schema_version": 1,
                    },
                    "taxas": {},
                }
                self.json_path.write_text(
                    json.dumps(base, indent=2, ensure_ascii=False), encoding="utf-8"
                )
                self._data = base
        except Exception:
            # Em caso de erro de IO, mantemos _data vazio e deixamos o chamador lidar
            if not self._data:
                self._data = {"metadata": {}, "taxas": {}}

    def _load(self) -> Dict:
        """Carrega dados do JSON (lazy)."""
        if self._data:
            return self._data
        try:
            raw = self.json_path.read_text(encoding="utf-8")
            self._data = json.loads(raw)
        except Exception:
            self._data = {"metadata": {}, "taxas": {}}
        if "taxas" not in self._data:
            self._data["taxas"] = {}
        if "metadata" not in self._data:
            self._data["metadata"] = {}
        return self._data

    def _save(self) -> None:
        """Persiste o conteúdo atual em disco."""
        try:
            self.json_path.write_text(
                json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except Exception:
            # Não propagamos erro aqui para não quebrar o fluxo principal;
            # a chamada que usa a taxa deve continuar mesmo sem persistência.
            pass

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def carregar_taxas(self) -> Dict:
        """Retorna o dicionário completo de dados (metadata + taxas)."""
        return self._load()

    def obter_taxa(self, moeda: str, ano: int, mes: int) -> Optional[float]:
        """Recupera apenas o valor da taxa média, se existir."""
        data = self._load()
        ano_key = str(ano)
        mes_key = str(mes)
        moeda_key = str(moeda).upper()
        try:
            return float(
                data["taxas"][ano_key][moeda_key][mes_key].get("taxa_media")  # type: ignore[call-arg]
            )
        except Exception:
            return None

    def salvar_taxa(
        self,
        moeda: str,
        ano: int,
        mes: int,
        taxa_media: float,
        fonte: str,
        dias_utilizados: int,
        fallback: bool = False,
        observacao: Optional[str] = None,
    ) -> None:
        """
        Salva/atualiza uma taxa no JSON (opera de forma incremental).
        Nunca apaga meses antigos – apenas acrescenta ou sobrescreve o mesmo mês.
        """
        data = self._load()
        ano_key = str(ano)
        mes_key = str(mes)
        moeda_key = str(moeda).upper()

        if "taxas" not in data:
            data["taxas"] = {}
        if ano_key not in data["taxas"]:
            data["taxas"][ano_key] = {}
        if moeda_key not in data["taxas"][ano_key]:
            data["taxas"][ano_key][moeda_key] = {}

        data["taxas"][ano_key][moeda_key][mes_key] = {
            "taxa_media": float(taxa_media),
            "fonte": str(fonte),
            "dias_utilizados": int(dias_utilizados),
            "data_atualizacao": datetime.now().isoformat(),
            "fallback": bool(fallback),
            "observacao": observacao,
        }
        self._data = data
        self._save()

    def atualizar_metadata(self, moedas: List[str]) -> None:
        """Atualiza metadados gerais do arquivo."""
        data = self._load()
        meta = data.setdefault("metadata", {})
        now = datetime.now()
        meta["ultima_atualizacao"] = now.isoformat()
        meta["ano_atual"] = now.year
        meta["mes_atual"] = now.month
        # Garante lista única e ordenada de moedas
        existentes = set(
            str(m).upper()
            for m in meta.get("moedas_disponiveis", [])
            if isinstance(m, str)
        )
        novas = {str(m).upper() for m in moedas if m}
        meta["moedas_disponiveis"] = sorted(existentes.union(novas))
        meta.setdefault("schema_version", 1)
        self._data = data
        self._save()

    def calcular_media_ano_ate_mes(
        self, moeda: str, ano: int, mes_limite: int
    ) -> Optional[float]:
        """
        Calcula a média simples das taxas do ano até `mes_limite` (inclusive).
        Usado como fallback quando não é possível buscar uma taxa específica.
        """
        if mes_limite <= 0:
            return None

        valores: List[float] = []
        for mes in range(1, mes_limite + 1):
            taxa = self.obter_taxa(moeda, ano, mes)
            if taxa is not None:
                valores.append(taxa)

        if not valores:
            return None
        return sum(valores) / len(valores)


