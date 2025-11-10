"""
Módulo para gerenciamento de taxas de câmbio.

Este módulo é responsável por buscar e cachear taxas de câmbio médias mensais
para cálculo de metas de fornecedores. As taxas são necessárias para converter
valores de faturamento de BRL para a moeda nativa do fornecedor.

Otimizações implementadas:
- Pré-carregamento de todas as taxas necessárias antes do processamento
- Cache persistente em arquivo JSON para evitar buscas repetidas
- Timeout reduzido e fallback rápido para evitar travamentos
- Busca otimizada com menos tentativas
"""

import os
import json
import time
import calendar
from datetime import datetime
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class CurrencyRateManager:
    """
    Gerencia taxas de câmbio com cache persistente e busca otimizada.
    
    Estratégia de otimização:
    1. Cache persistente em arquivo JSON (evita buscas repetidas entre execuções)
    2. Cache em memória durante a execução (evita buscas duplicadas)
    3. Pré-carregamento de todas as taxas necessárias de uma vez
    4. Timeout reduzido (5s) e menos tentativas (2) para evitar travamentos
    5. Fallback rápido entre APIs (não espera timeout completo)
    """
    
    def __init__(self, cache_file: str = "cache_taxas_cambio.json", logger=None):
        """
        Inicializa o gerenciador de taxas de câmbio.
        
        Args:
            cache_file: Caminho para arquivo de cache persistente
            logger: Logger opcional para mensagens de debug
        """
        self.cache_file = cache_file
        self.logger = logger
        self.cache_memoria: Dict[Tuple[int, int, tuple], Dict[str, Dict[int, float]]] = {}
        self.cache_persistente: Dict[str, Dict[str, Dict[int, float]]] = {}
        self._carregar_cache_persistente()
        
    def _log(self, nivel: str, mensagem: str):
        """Log interno usando logger ou print."""
        if self.logger:
            if nivel == "INFO":
                self.logger.info(mensagem)
            elif nivel == "DEBUG":
                self.logger.debug(mensagem)
            elif nivel == "WARNING":
                self.logger.warning(mensagem)
        else:
            if nivel != "DEBUG":  # Só mostrar INFO/WARNING, não DEBUG
                print(f"[{nivel}] {mensagem}")
    
    def _carregar_cache_persistente(self):
        """Carrega cache persistente do arquivo JSON."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache_persistente = json.load(f)
                self._log("DEBUG", f"Cache persistente carregado: {len(self.cache_persistente)} entradas")
        except Exception as e:
            self._log("WARNING", f"Falha ao carregar cache persistente: {e}")
            self.cache_persistente = {}
    
    def _salvar_cache_persistente(self):
        """Salva cache persistente no arquivo JSON."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_persistente, f, indent=2, ensure_ascii=False)
            self._log("DEBUG", f"Cache persistente salvo: {len(self.cache_persistente)} entradas")
        except Exception as e:
            self._log("WARNING", f"Falha ao salvar cache persistente: {e}")
    
    def _chave_cache_persistente(self, ano: int, mes_final: int, moedas: List[str]) -> str:
        """Gera chave de cache persistente."""
        moedas_sorted = sorted(set(moedas))
        return f"{ano}_{mes_final}_{'_'.join(moedas_sorted)}"
    
    def _buscar_taxa_api(
        self, 
        moeda: str, 
        ano: int, 
        mes: int, 
        timeout: float = 5.0,
        max_retries: int = 2
    ) -> Optional[float]:
        """
        Busca taxa de câmbio para uma moeda/mês específico.
        
        Estratégia otimizada:
        1. Tenta exchangerate.host/timeseries (média mensal)
        2. Se falhar, tenta frankfurter.app (dia 15 do mês)
        3. Se falhar, tenta exchangerate.host/convert (dia 15 do mês)
        4. Timeout reduzido (5s) e menos tentativas (2) para evitar travamentos
        
        Returns:
            Taxa de câmbio ou None se não conseguir obter
        """
        if not REQUESTS_AVAILABLE:
            return None
        
        primeiro_dia = datetime(ano, mes, 1).date()
        ultimo_dia = datetime(ano, mes, calendar.monthrange(ano, mes)[1]).date()
        dia_central = min(15, calendar.monthrange(ano, mes)[1])
        data_central = datetime(ano, mes, dia_central).date().isoformat()
        
        # Estratégia 1: exchangerate.host/timeseries (média mensal - mais preciso)
        try:
            url = "https://api.exchangerate.host/timeseries"
            params = {
                "start_date": primeiro_dia.isoformat(),
                "end_date": ultimo_dia.isoformat(),
                "base": "BRL",
                "symbols": moeda,
            }
            for attempt in range(1, max_retries + 1):
                try:
                    r = requests.get(url, params=params, timeout=timeout)
                    if r.status_code == 200:
                        data = r.json()
                        rates = []
                        for d, vals in data.get("rates", {}).items():
                            v = vals.get(moeda)
                            if v is not None:
                                rates.append(float(v))
                        if rates:
                            taxa_media = sum(rates) / len(rates)
                            self._log("DEBUG", f"Taxa obtida via timeseries: {moeda} {ano}-{mes:02d} = {taxa_media:.6f}")
                            return taxa_media
                except Exception as e:
                    if attempt < max_retries:
                        time.sleep(0.5 * attempt)  # Backoff curto
                        continue
                    self._log("DEBUG", f"Timeseries falhou para {moeda} {ano}-{mes:02d}: {e}")
        except Exception:
            pass
        
        # Estratégia 2: frankfurter.app (dia central - rápido)
        try:
            url = f"https://api.frankfurter.app/{data_central}"
            params = {"from": "BRL", "to": moeda}
            for attempt in range(1, max_retries + 1):
                try:
                    r = requests.get(url, params=params, timeout=timeout)
                    if r.status_code == 200:
                        data = r.json()
                        taxa = data.get("rates", {}).get(moeda)
                        if taxa is not None:
                            self._log("DEBUG", f"Taxa obtida via frankfurter: {moeda} {ano}-{mes:02d} = {taxa:.6f}")
                            return float(taxa)
                except Exception as e:
                    if attempt < max_retries:
                        time.sleep(0.3 * attempt)
                        continue
        except Exception:
            pass
        
        # Estratégia 3: exchangerate.host/convert (dia central - último recurso)
        try:
            url = "https://api.exchangerate.host/convert"
            params = {"from": "BRL", "to": moeda, "date": data_central}
            for attempt in range(1, max_retries + 1):
                try:
                    r = requests.get(url, params=params, timeout=timeout)
                    if r.status_code == 200:
                        data = r.json()
                        taxa = data.get("result") or data.get("info", {}).get("rate")
                        if taxa is not None:
                            self._log("DEBUG", f"Taxa obtida via convert: {moeda} {ano}-{mes:02d} = {taxa:.6f}")
                            return float(taxa)
                except Exception as e:
                    if attempt < max_retries:
                        time.sleep(0.3 * attempt)
                        continue
        except Exception:
            pass
        
        return None
    
    def get_rates(
        self, 
        ano: int, 
        mes_final: int, 
        moedas: List[str],
        force_refresh: bool = False
    ) -> Dict[str, Dict[int, float]]:
        """
        Obtém taxas de câmbio para moedas do mês 1 até mes_final.
        
        Args:
            ano: Ano de apuração
            mes_final: Último mês a buscar (1-12)
            moedas: Lista de códigos de moedas (ex: ['USD', 'EUR'])
            force_refresh: Se True, ignora cache e busca novamente
        
        Returns:
            Dicionário {moeda: {mes: taxa}} com taxas de câmbio
        """
        moedas = list(set(moedas))
        if not moedas:
            return {}
        
        # Remover BRL (não precisa conversão)
        moedas = [m for m in moedas if str(m).upper() != "BRL"]
        if not moedas:
            return {}
        
        # Normalizar moedas
        moedas = [str(m).upper() for m in moedas]
        
        # Verificar cache em memória
        cache_key = (ano, mes_final, tuple(sorted(moedas)))
        if not force_refresh and cache_key in self.cache_memoria:
            self._log("DEBUG", f"Cache memória hit: {moedas} ({ano}, mês {mes_final})")
            return self.cache_memoria[cache_key]
        
        # Verificar cache persistente
        chave_persistente = self._chave_cache_persistente(ano, mes_final, moedas)
        if not force_refresh and chave_persistente in self.cache_persistente:
            resultado = self.cache_persistente[chave_persistente]
            # Converter strings de chaves para int (meses)
            resultado_convertido = {
                moeda: {int(mes): taxa for mes, taxa in meses.items()}
                for moeda, meses in resultado.items()
            }
            self.cache_memoria[cache_key] = resultado_convertido
            self._log("DEBUG", f"Cache persistente hit: {moedas} ({ano}, mês {mes_final})")
            return resultado_convertido
        
        # Buscar taxas (não encontradas no cache)
        inicio = time.time()
        self._log("INFO", f"Buscando taxas para {len(moedas)} moeda(s): {moedas} ({ano}, mês 1-{mes_final})")
        
        resultado = {moeda: {} for moeda in moedas}
        total_requisicoes = len(moedas) * mes_final
        requisicoes_completas = 0
        
        for moeda in moedas:
            for mes in range(1, mes_final + 1):
                taxa = self._buscar_taxa_api(moeda, ano, mes, timeout=5.0, max_retries=2)
                if taxa is not None:
                    resultado[moeda][mes] = taxa
                requisicoes_completas += 1
                
                # Log de progresso a cada 25% ou a cada 5 segundos
                if requisicoes_completas % max(1, total_requisicoes // 4) == 0:
                    tempo_decorrido = time.time() - inicio
                    pct = (requisicoes_completas / total_requisicoes) * 100
                    self._log("INFO", 
                        f"Progresso busca taxas: {requisicoes_completas}/{total_requisicoes} "
                        f"({pct:.0f}%) em {tempo_decorrido:.1f}s")
        
        tempo_total = time.time() - inicio
        
        # Estatísticas
        taxas_obtidas = sum(len(meses) for meses in resultado.values())
        taxas_faltando = total_requisicoes - taxas_obtidas
        
        self._log("INFO", 
            f"Busca concluída: {taxas_obtidas}/{total_requisicoes} taxas obtidas "
            f"({taxas_faltando} faltando) em {tempo_total:.2f}s")
        
        if tempo_total > 30.0:
            self._log("WARNING", 
                f"Busca de taxas demorou {tempo_total:.2f}s (pode estar travando)")
        
        # Salvar no cache
        self.cache_memoria[cache_key] = resultado
        # Converter int para string para JSON
        resultado_json = {
            moeda: {str(mes): taxa for mes, taxa in meses.items()}
            for moeda, meses in resultado.items()
        }
        self.cache_persistente[chave_persistente] = resultado_json
        self._salvar_cache_persistente()
        
        return resultado
    
    def preload_all_rates(
        self,
        ano: int,
        mes_final: int,
        todas_moedas: Set[str],
        logger=None
    ) -> Dict[str, Dict[int, float]]:
        """
        Pré-carrega todas as taxas necessárias de uma vez.
        
        Esta função deve ser chamada ANTES do loop de processamento de itens
        para evitar buscas durante o cálculo de FC.
        
        Args:
            ano: Ano de apuração
            mes_final: Último mês a buscar
            todas_moedas: Set com todas as moedas que serão necessárias
            logger: Logger opcional
        
        Returns:
            Dicionário com todas as taxas pré-carregadas
        """
        if logger:
            self.logger = logger
        
        moedas_lista = list(todas_moedas)
        if not moedas_lista:
            return {}
        
        self._log("INFO", 
            f"Pré-carregando taxas para {len(moedas_lista)} moeda(s): {moedas_lista} "
            f"({ano}, mês 1-{mes_final})")
        
        inicio_preload = time.time()
        resultado = self.get_rates(ano, mes_final, moedas_lista)
        tempo_preload = time.time() - inicio_preload
        
        self._log("INFO", 
            f"Pré-carregamento concluído em {tempo_preload:.2f}s")
        
        return resultado

