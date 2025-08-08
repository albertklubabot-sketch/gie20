import os
import sys
import time
import json
import importlib
import logging
import requests

from typing import List, Dict, Any, Optional, Callable

# === Importy core/systemowych narzędzi GIE ===
try:
    from core.meta_reflection import MetaReflection
    from core.gie_hive import HiveCommunicator
    from utils.logger import get_logger
except ImportError:
    # Fallback do testów standalone (bez całego core)
    class MetaReflection:
        def __init__(self, *a, **kw): pass
        def reflect(self, *a, **kw): pass
        def analyze_discoveries(self, log): return {"new_searches": 0, "stale_sources": 0}
    class HiveCommunicator:
        def __init__(self, *a, **kw): pass
        def broadcast(self, *a, **kw): return []
    def get_logger(name): 
        logger = logging.getLogger(name)
        if not logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

logger = get_logger("HunterTools")

# === DataSource: podstawowa klasa źródła danych ===
class DataSource:
    """Podstawowa klasa źródła danych."""
    def __init__(self, name: str, fetch_func: Callable, config: dict):
        self.name = name
        self.fetch_func = fetch_func
        self.config = config
        self.status = "ready"
        self.last_update = None
        self.error = None

    def fetch(self, *args, **kwargs):
        try:
            data = self.fetch_func(*args, **kwargs)
            self.last_update = time.time()
            self.status = "ok"
            logger.info(f"[{self.name}] Data fetched.")
            return data
        except Exception as e:
            self.error = str(e)
            self.status = "error"
            logger.error(f"[{self.name}] Data fetch error: {e}")
            return None

# === HunterTools: Super moduł hunter / automatyczny łowca danych, okazji, narzędzi i strategii ===
class HunterTools:
    """Super moduł Hunter | automatyczny łowca danych, okazji, narzędzi i strategii."""

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.data_sources: Dict[str, DataSource] = {}
        self.plugins: Dict[str, Any] = {}
        self.meta = MetaReflection(self)
        self.hive = HiveCommunicator(self)
        self.discovery_log: List[dict] = []
        self.self_modifying = False
        self.last_scan_time = 0
        self.hunger = 1.0   # <-- UPEWNIONE, że masz atrybut
        self.init_default_sources()
        logger.info("HunterTools initialized.")

    # --- Podstawowe funkcje -----------------
    def init_default_sources(self):
        """Podłącza domyślne źródła danych i narzędzia."""
        # Przykład z MT5, AlphaVantage, Yahoo, CoinGecko itp.
        self.add_data_source("YahooFinance", self.fetch_yahoo, {})
        self.add_data_source("CoinGecko", self.fetch_coingecko, {})
        # Można dodać więcej dynamicznie...

    def add_data_source(self, name: str, fetch_func: Callable, config: dict):
        """Rejestracja nowego źródła."""
        self.data_sources[name] = DataSource(name, fetch_func, config)
        logger.info(f"Added data source: {name}")

    def remove_data_source(self, name: str):
        if name in self.data_sources:
            del self.data_sources[name]
            logger.info(f"Removed data source: {name}")

    # --- Hunter: eksploracja, łowienie i uczenie ---------
    def explore_new_sources(self):
        """Skanuje sieć/API w poszukiwaniu nowych, wartościowych źródeł i strategii."""
        hunter_query_list = [
            {"name": "AlphaVantage", "url": "https://www.alphavantage.co/query", "test": True},
            {"name": "Finnhub", "url": "https://finnhub.io/api/v1/", "test": True},
            {"name": "CustomCSV", "url": "file:data/new_data.csv", "test": False}
        ]
        for source in hunter_query_list:
            if source['name'] not in self.data_sources:
                self.try_register_dynamic_source(source)

    def try_register_dynamic_source(self, source):
        # Prosty przykład automatycznej rejestracji
        def dummy_fetch(*args, **kwargs):
            return {"msg": f"Fetched from {source['name']}", "dummy_fetch": True, "url": source["url"]}
        self.add_data_source(source['name'], dummy_fetch, {"url": source["url"]})
        self.log_discovery(f"New source registered: {source['name']}")

    def hunt_opportunities(self, criteria: dict) -> List[dict]:
        """Automatyczne wyszukiwanie okazji rynkowych na podstawie kryteriów."""
        opportunities = []
        for ds_name, ds in self.data_sources.items():
            data = ds.fetch(criteria)
            if self.evaluate_data(data, criteria):
                opportunities.append({"source": ds_name, "data": data})
        if not opportunities:
            self.meta.reflect("No opportunities found. Should we broaden the search?")
        return opportunities

    def evaluate_data(self, data, criteria: dict) -> bool:
        """Inteligentna ocena czy dane spełniają oczekiwania."""
        if not data:
            return False
        # Prosta heurystyka (możesz tu dodać ML lub scoring!)
        return True if "msg" in str(data) or len(str(data)) > 10 else False

    def log_discovery(self, text: str):
        self.discovery_log.append({"ts": time.time(), "text": text})
        logger.info(text)

    # --- Integracja, API, klonowanie, hive -------------
    def integrate_with_hive(self, self_ref):
        """Wymiana okazji, źródeł i narzędzi i pluginów z innymi instancjami GIE."""
        try:
            hive_data = self.hive.broadcast("get_hunter_discoveries", self.discovery_log)
            for entry in hive_data or []:
                if entry not in self.discovery_log:
                    self.discovery_log.append(entry)
            logger.info("Hive integration complete.")
        except Exception as e:
            logger.error(f"Hive integration error: {e}")

    def clone_self(self):
        """Klonowanie hunter tools z własną pamięcią i strategiami."""
        new_hunter = HunterTools(self.config)
        new_hunter.discovery_log = list(self.discovery_log)
        new_hunter.hunger = self.hunger * 0.9  # lekkie zmniejszenie głodu po klonie
        logger.info("HunterTools instance cloned.")
        return new_hunter

    # --- Self-modification, auto-expansion -------------
    def self_improve(self):
        """Meta-refleksja: uczy się na swoich sukcesach, błędach i modyfikuje kod."""
        stats = self.meta.analyze_discoveries(self.discovery_log)
        if stats.get("new_searches", 0) > 3:
            self.hunger += 0.1
            self.explore_new_sources()
        if stats.get("stale_sources", 0) > 0:
            self.remove_data_source(stats["stale_source_name"])
            self.meta.reflect(f"Removed stale source: {stats['stale_source_name']}")

    # --- Przykładowe fetch_func ---------------
    def fetch_yahoo(self, params: dict = None):
        """Przykładowy fetcher Yahoo Finance."""
        try:
            url = "https://query1.finance.yahoo.com/v7/finance/quote"
            if params is None:
                params = {"symbols": "AAPL"}
            response = requests.get(url, params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Yahoo fetch error: {e}")
            return None

    def fetch_coingecko(self, params: dict = None):
        """Przykładowy fetcher CoinGecko."""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = params or {"ids": "bitcoin", "vs_currencies": "usd"}
            response = requests.get(url, params=params)
            return response.json()
        except Exception as e:
            logger.error(f"CoinGecko fetch error: {e}")
            return None

    # --- Plugin system --------------
    def load_plugin(self, plugin_path: str):
        """Ładowanie pluginów tools (nowe strategie, narzędzia)."""
        try:
            spec = importlib.util.spec_from_file_location("plugin", plugin_path)
            plugin = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(plugin)
            self.plugins[plugin_path] = plugin
            logger.info(f"Loaded plugin: {plugin_path}")
        except Exception as e:
            logger.error(f"Plugin load error: {e}")

    def run_plugins(self, *args, **kwargs):
        """Uruchamianie wszystkich załadowanych pluginów."""
        for name, plugin in self.plugins.items():
            if hasattr(plugin, "run"):
                try:
                    plugin.run(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Plugin {name} run error: {e}")

    # --- API wejście/wyjście (podłączenie z GIE) ---------
    def api_request(self, endpoint: str, data: dict = None):
        """API wewnętrzne dla GIE (możesz podłączyć tu Flask lub FastAPI)."""
        # To tylko interfejs, implementuj połączenie z core/systemem GIE
        return {"endpoint": endpoint, "status": "ok", "data": data}

    # --- Harmonogramy i automatyzacja ---------------
    def run_automated(self):
        """Automatyczny cykl hunter tools."""
        while self.hunger > 0.1:
            self.explore_new_sources()
            found = self.hunt_opportunities({})
            if not found:
                self.hunger += 0.05  # podbij głód, jeśli nic nie znalazł
            else:
                self.hunger *= 0.95
                self.self_improve()
                self.integrate_with_hive(self)
            time.sleep(10)

    # --- Meta refleksja manualna -----------
    def reflect(self, msg: str):
        self.meta.reflect(msg)
        logger.info(f"Meta reflection: {msg}")

# ===== KOD TESTOWY =====
if __name__ == "__main__":
    ht = HunterTools()
    ht.explore_new_sources()
    print("Discovery log:", ht.discovery_log)
    print("Opportunities:", ht.hunt_opportunities({"target": "profit"}))
    print("Manual reflection executed.")
    ht.reflect("Manual meta reflection test")
    # Możesz przetestować automatyzację uruchamiając ht.run_automated() (uwaga: nieskończona pętla!)
