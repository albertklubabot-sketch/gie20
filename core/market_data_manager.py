import os
import importlib
import pandas as pd
from datetime import datetime, timedelta

class MarketDataManager:
    """
    Centralny menedżer danych rynkowych – autonomiczne zarządzanie providerami,
    feedback loop, automatyczna integracja nowych źródeł oraz meta-refleksja.
    """

    def __init__(self, login=None, password=None, server=None, hive=None, meta_reflection=None):
        self.providers = []
        self.stats = {}  # Statystyki skuteczności providerów
        self.hive = hive
        self.meta_reflection = meta_reflection
        self.load_providers(login, password, server)

    def load_providers(self, login, password, server):
        """
        Dynamicznie ładuje wszystkie klasy providera z folderu data_providers.
        """
        provider_dir = "data_providers"
        for file in os.listdir(provider_dir):
            if file.endswith(".py") and not file.startswith("_"):
                module_name = f"{provider_dir}.{file[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    if hasattr(module, "DataProvider"):
                        provider = module.DataProvider(login, password, server)
                        self.providers.append(provider)
                        self.stats[provider.__class__.__name__] = {"success": 0, "fail": 0, "last_error": None}
                except Exception as e:
                    print(f"[MarketDataManager] Błąd ładowania providera {module_name}: {e}")

    def fetch(self, symbol, minutes=60):
        """
        Pobiera dane ze wszystkich providerów w zadanym oknie czasowym.
        """
        end = datetime.now()
        start = end - timedelta(minutes=minutes)
        all_data = []
        for provider in self.providers:
            try:
                data = provider.fetch(symbol, start, end)
                if data is not None:
                    all_data.append(data)
                    self.stats[provider.__class__.__name__]["success"] += 1
                else:
                    self.stats[provider.__class__.__name__]["fail"] += 1
            except Exception as e:
                pname = provider.__class__.__name__
                self.stats[pname]["fail"] += 1
                self.stats[pname]["last_error"] = str(e)
                self._notify_hive(f"Błąd provider: {pname} {e}")
        if not all_data:
            self._notify_hive(f"Brak danych dla symbolu {symbol}")
            return None
        df = pd.concat(all_data, axis=1)
        return df

    def get_merged_data(self, symbol, timeframe, limit=100):
        """
        Zwraca połączony DataFrame z wszystkich providerów dla danego symbolu.
        """
        df = self.fetch(symbol, minutes=limit)
        if df is not None:
            return df.tail(limit)
        return None

    def best_provider(self):
        """
        Zwraca najlepszego providera wg skuteczności.
        """
        return max(self.stats, key=lambda k: self.stats[k]["success"])

    def remove_bad_providers(self, threshold=5):
        """
        Usuwa providerów z dużą ilością błędów.
        """
        to_remove = [p for p, stat in self.stats.items() if stat["fail"] > threshold]
        self.providers = [p for p in self.providers if p.__class__.__name__ not in to_remove]
        for p in to_remove:
            self._notify_hive(f"Usunięto słabego providera: {p}")
            del self.stats[p]

    def provider_health_report(self):
        """
        Raport skuteczności providerów.
        """
        return self.stats

    def hunger_for_data(self, symbol):
        """
        Głód danych: jeśli dla symbolu brakuje danych, triggeruj poszukiwanie alternatyw.
        """
        self._notify_hive(f"Głód danych dla symbolu {symbol}. Uruchamiam hunter_tools!")
        # Możesz dodać logikę integracji z hunter_tools/meta_reflection

    def _notify_hive(self, msg):
        """
        Prywatny hook do powiadamiania Hive lub MetaReflection o problemach.
        """
        if self.hive is not None:
            self.hive.notify(msg)
        if self.meta_reflection is not None:
            self.meta_reflection.log_event(msg)
        print(f"[HIVE/META] {msg}")

    # --- Metody meta-rozwojowe ---
    def auto_reflect(self):
        """
        Meta-refleksja: analizuj skuteczność providerów, automatycznie klonuj/wykluczaj.
        """
        for name, stat in self.stats.items():
            if stat["fail"] > 10 and stat["success"] == 0:
                self._notify_hive(f"Wykluczanie martwego providera: {name}")
                self.remove_bad_providers(threshold=10)

    def auto_hunt(self, symbol):
        """
        Automatyczne wyszukiwanie nowych źródeł dla symbolu (hook do hunter_tools).
        """
        self._notify_hive(f"Auto-hunt nowych źródeł dla: {symbol}")
        # Tu możesz wywołać hunter_tools.scan_for_providers(symbol)

    # --- ADAPTERY DO META-GUARDIAN i GIE_MIND ---
    def get_total_capital(self):
        """
        Zwraca całkowity kapitał rachunku z najlepszego providera.
        """
        for provider in self.providers:
            if hasattr(provider, "get_total_capital"):
                try:
                    value = provider.get_total_capital()
                    if value is not None:
                        return value
                except Exception as e:
                    print(f"[MarketDataManager] Błąd pobrania total_capital: {e}")
        return 0.0

    def get_equity(self):
        """
        Zwraca aktualną wartość equity z najlepszego providera.
        """
        for provider in self.providers:
            if hasattr(provider, "get_equity"):
                try:
                    value = provider.get_equity()
                    if value is not None:
                        return value
                except Exception as e:
                    print(f"[MarketDataManager] Błąd pobrania equity: {e}")
        return 0.0

    def get_open_trades(self):
        """
        Zwraca listę aktywnych pozycji z najlepszego providera.
        """
        for provider in self.providers:
            if hasattr(provider, "get_open_trades"):
                try:
                    trades = provider.get_open_trades()
                    if trades is not None:
                        return trades
                except Exception as e:
                    print(f"[MarketDataManager] Błąd pobrania pozycji: {e}")
        return []

    def get_open_grids(self):
        """
        Zwraca listę aktywnych gridów (jeśli provider obsługuje grid trading).
        """
        for provider in self.providers:
            if hasattr(provider, "get_open_grids"):
                try:
                    grids = provider.get_open_grids()
                    if grids is not None:
                        return grids
                except Exception as e:
                    print(f"[MarketDataManager] Błąd pobrania gridów: {e}")
        return []

    def get_margin_level(self):
        """
        Zwraca poziom margin level (equity/margin), jeśli provider obsługuje.
        """
        for provider in self.providers:
            if hasattr(provider, "get_margin_level"):
                try:
                    value = provider.get_margin_level()
                    if value is not None:
                        return value
                except Exception as e:
                    print(f"[MarketDataManager] Błąd pobrania margin_level: {e}")
        return 1.0  # fallback

# --- Przykładowa klasa adaptacyjna (jeśli masz blokady API itp.) ---
class MarketAdaptation:
    def __init__(self, max_fails=3):
        self.blocked = False
        self.failed_requests = 0
        self.max_fails = max_fails

    def check_api(self, self_response):
        if self_response.get("error") in ["blocked", "throttled", "banned"]:
            self.failed_requests += 1
            if self.failed_requests >= self.max_fails:
                self.blocked = True
                self.take_action()
        else:
            self.failed_requests = 0

    def take_action(self):
        print("Market API blocked! Rotating endpoints, enabling proxy...")
        # Tu możesz podłączyć automatyczną zmianę endpointów, proxy, itp.
