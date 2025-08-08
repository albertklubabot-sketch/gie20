# data_providers/alt_data.py
import importlib
import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Any

class AltDataProvider:
    """
    Superinteligentny, samodoskonalący się moduł do obsługi alternatywnych źródeł danych dla GIE 2.0
    Obsługuje: automatyczne wykrywanie, podłączanie i integrację nowych źródeł alt-data (np. news, social, sentiment, pogodowe, blockchain)
    """

    def __init__(self, config_path: str = 'data_providers/alt_data_config.json'):
        self.config_path = config_path
        self.sources = {}  # Klucz: nazwa źródła, wartość: obiekt źródła
        self.history = []  # Log wszystkich zapytań i wyników
        self.load_config()
        self.auto_import_plugins()
        self.super_intelligence_log(f"AltDataProvider initialized. Sources: {list(self.sources.keys())}")

    def super_intelligence_log(self, msg: str):
        # Superlogowanie z timestampem
        ts = datetime.now().isoformat()
        print(f"[ALT_DATA][{ts}] {msg}")

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                for src in config.get("sources", []):
                    self.register_source(src)
            self.super_intelligence_log("Config loaded.")
        else:
            self.super_intelligence_log("No config file found. Starting with empty config.")

    def save_config(self):
        config = {"sources": [src for src in self.sources.keys()]}
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=4)
        self.super_intelligence_log("Config saved.")

    def register_source(self, source_info: Dict[str, Any]):
        """
        Rejestruje nowe źródło danych
        source_info: dict z polami: name, type, endpoint/module, params
        """
        name = source_info["name"]
        if name in self.sources:
            self.super_intelligence_log(f"Source '{name}' already registered.")
            return
        # Typ źródła: REST, local_plugin, external_api
        if source_info["type"] == "REST":
            self.sources[name] = RestAltDataSource(source_info["endpoint"], source_info.get("params", {}))
        elif source_info["type"] == "local_plugin":
            try:
                module = importlib.import_module(source_info["endpoint"])
                self.sources[name] = module.AltDataSource()
            except Exception as e:
                self.super_intelligence_log(f"Failed to load local plugin: {e}")
                return
        elif source_info["type"] == "external_api":
            self.sources[name] = ExternalAPIAltDataSource(source_info["endpoint"], source_info.get("params", {}))
        else:
            self.super_intelligence_log(f"Unknown source type: {source_info['type']}")
            return
        self.super_intelligence_log(f"Source '{name}' registered [{source_info['type']}].")

    def auto_import_plugins(self):
        # Automatyczne ładowanie wszystkich pluginów z folderu data_providers/alt_plugins/
        plugins_dir = os.path.join(os.path.dirname(__file__), "alt_plugins")
        if not os.path.isdir(plugins_dir):
            os.makedirs(plugins_dir, exist_ok=True)
        for fname in os.listdir(plugins_dir):
            if fname.endswith(".py") and not fname.startswith("_"):
                module_name = f"data_providers.alt_plugins.{fname[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    if hasattr(module, "AltDataSource"):
                        src = module.AltDataSource()
                        name = getattr(src, "name", fname[:-3])
                        self.sources[name] = src
                        self.super_intelligence_log(f"Auto-loaded plugin: {name}")
                except Exception as e:
                    self.super_intelligence_log(f"Failed to auto-load plugin {fname}: {e}")

    def fetch_all(self, query: str = None) -> Dict[str, Any]:
        """
        Pobiera dane ze wszystkich dostępnych źródeł
        """
        results = {}
        for name, src in self.sources.items():
            try:
                data = src.fetch(query=query)
                results[name] = data
                self.super_intelligence_log(f"Fetched data from {name}.")
            except Exception as e:
                self.super_intelligence_log(f"Error fetching from {name}: {e}")
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "results": results
        })
        return results

    def discover_new_sources(self):
        """
        Superinteligentna metoda szukania i auto-integracji nowych źródeł danych z internetu / API directory / pluginów.
        (Przykład: tylko symulacja, ale możesz to rozszerzyć o prawdziwe skanowanie repozytoriów/pluginów)
        """
        # TODO: Dodać AI crawling repozytoriów/pluginów
        discovered = [
            {"name": "AltNewsAI", "type": "REST", "endpoint": "https://altnewsapi.com/api", "params": {}},
            {"name": "SentimentOcean", "type": "external_api", "endpoint": "https://sentimentocean.com/api", "params": {"key": "YOUR_API_KEY"}}
        ]
        for src in discovered:
            self.register_source(src)
        self.save_config()
        self.super_intelligence_log(f"Discovered and registered new sources: {[x['name'] for x in discovered]}")

    def get_history(self) -> List[Dict[str, Any]]:
        return self.history

    def meta_evolve(self):
        """
        Samodoskonalenie: analiza skuteczności źródeł, automatyczne odrzucanie nieefektywnych,
        wnioskowanie o potrzebie nowych pluginów, samoregulacja
        """
        # Przykładowa analiza historii
        performance = {}
        for entry in self.history[-20:]:
            for src, data in entry["results"].items():
                if src not in performance:
                    performance[src] = 0
                if data:
                    performance[src] += 1
        for src, score in performance.items():
            if score < 2:
                self.super_intelligence_log(f"Source '{src}' is underperforming. Considering removal or retraining.")
        # Samodzielnie szukaj nowych pluginów jeśli poniżej określonej skuteczności
        if len(performance) < 3:
            self.super_intelligence_log("Low diversity of sources. Triggering auto-discovery.")
            self.discover_new_sources()

class RestAltDataSource:
    """
    Przykładowe źródło typu REST API
    """
    def __init__(self, endpoint: str, params: Dict[str, Any]):
        self.endpoint = endpoint
        self.params = params
        self.name = "REST_" + endpoint.split("//")[-1].split("/")[0]

    def fetch(self, query: str = None) -> Any:
        url = self.endpoint
        payload = self.params.copy()
        if query:
            payload["q"] = query
        resp = requests.get(url, params=payload)
        if resp.status_code == 200:
            return resp.json()
        else:
            raise Exception(f"REST fetch error: {resp.status_code}")

class ExternalAPIAltDataSource:
    """
    Przykładowe źródło typu zewnętrzne API (np. sentiment)
    """
    def __init__(self, endpoint: str, params: Dict[str, Any]):
        self.endpoint = endpoint
        self.params = params
        self.name = "API_" + endpoint.split("//")[-1].split("/")[0]

    def fetch(self, query: str = None) -> Any:
        url = self.endpoint
        payload = self.params.copy()
        if query:
            payload["query"] = query
        resp = requests.post(url, json=payload)
        if resp.status_code == 200:
            return resp.json()
        else:
            raise Exception(f"API fetch error: {resp.status_code}")

# PRZYKŁADOWE UŻYCIE:
if __name__ == "__main__":
    alt_data = AltDataProvider()
    alt_data.discover_new_sources()
    wyniki = alt_data.fetch_all("tesla stock news")
    print("Wyniki:", wyniki)
    alt_data.meta_evolve()
