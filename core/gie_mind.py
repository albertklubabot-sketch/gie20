import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import os, pickle, random, copy, time
from datetime import datetime
import concurrent.futures

from core.meta_guardian import MetaGuardian
from core.hunter_tools import HunterTools as GieHunter
from core.meta_reflection import MetaReflection
from core.strategy_evolver import StrategyEvolver
from core.market_data_manager import MarketDataManager
from data_providers.mt5_data import MTS_LOGIN, MTS_PASSWORD, MTS_SERVER
from data_providers.mt5_data import MTSDataProvider

from core.engines.ostrozny import OstroznyEngine
from core.engines.refleksyjny import RefleksyjnyEngine
from core.engines.ryzykant import RyzykantEngine

from core.sensors.noise_sensor import NoiseSensor
from core.sensors.pressure_sensor import PressureSensor
from core.sensors.volume_sensor import VolumeSensor

from utils.logger import Logger
from utils.auto_cleanup import auto_cleanup
from core.gie_manifest import gie_manifest   # <- DODANE!

auto_cleanup()  # wywołaj przy starcie lub np. co X godzin

class GieMind:
    def __init__(self, log_path="data/gie_log.txt"):
        self.manifest = gie_manifest()       # <- POPRAWIONE!
        self.logger = Logger(log_path)
        self.hunter = GieHunter('core/engines', 'core/sensors')
        self.sensors = self.hunter.discover_sensors()
        self.engines = self.hunter.discover_engines()
        self.meta_reflection = MetaReflection()
        self.memory_path = 'data/gie_memory.pkl'
        self.strategy_evolver = None
        self.market_data = MarketDataManager()
        self.mt5_data = MTSDataProvider(MTS_LOGIN, MTS_PASSWORD, MTS_SERVER)
        self.hunger = 1.0
        self.satisfaction = 0.1
        self.curiosity = 0.8
        self.stats = {e.__class__.__name__: {"win": 0, "trials": 1} for e in self.engines}
        self.hunger_threshold = 0.8
        self.satisfaction_threshold = 0.8
        self.hunger_increment = 0.1
        self.curiosity_increment = 0.05
        self.satisfaction_increment = 0.1
        self.load_stats()

        print("=== MANIFEST GIE SUPER META ===")
        print(self.manifest.get_summary(), "\n")

    @property
    def evolver(self):
        if self.strategy_evolver is None:
            self.strategy_evolver = StrategyEvolver()
        return self.strategy_evolver

    def log_event(self, *args):
        msg = " | ".join(str(a) for a in args)
        self.logger.log(msg)

    def load_stats(self):
        if os.path.exists(self.memory_path):
            try:
                with open(self.memory_path, "rb") as f:
                    self.stats = pickle.load(f)
            except Exception as e:
                self.logger.log(f"[GIE META] Błąd wczytania statystyk: {e}")
                self.stats = {e.__class__.__name__: {"win": 0, "trials": 1} for e in self.engines}

    def save_stats(self):
        with open(self.memory_path, "wb") as f:
            pickle.dump(self.stats, f)

    def read_environment(self):
        mt5_tick = self.mt5_data.get_tick()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(s.read, mt5_tick) for s in self.sensors]
            sensor_values = {s.__class__.__name__: f.result() for s, f in zip(self.sensors, futures)}
        self.logger.log(f"[META-odczyt środowiska: {sensor_values}")
        return sensor_values

    def update_internal_state(self, reward):
        if reward > 0.5:
            self.satisfaction = min(1.0, self.satisfaction + self.satisfaction_increment)
            self.hunger = max(0.0, self.hunger - self.hunger_increment)
        elif reward < 0.2:
            self.curiosity = min(1.0, self.curiosity + self.curiosity_increment)
            self.hunger = min(1.0, self.hunger + 0.02)
        else:
            self.satisfaction = max(0.0, self.satisfaction - self.satisfaction_increment)
            self.curiosity = min(1.0, self.curiosity + 0.01)

        if self.satisfaction > self.hunger_threshold or self.curiosity > self.curiosity_threshold:
            self.log_event("[GIE META] wysoki głód/ciekawość: auto-ewolucja i klonowanie")
            self.evolver.auto_evolve()

    def auto_evolve(self):
        new_sensors = self.hunter.discover_sensors()
        for s in new_sensors:
            if not any(isinstance(x, s.__class__) for x in self.sensors):
                self.sensors.append(s)
                self.log_event(f"[GIE META] Dodano sensor: {s.__class__.__name__}")
        new_engines = self.hunter.discover_engines()
        for e in new_engines:
            if not any(isinstance(x, e.__class__) for x in self.engines):
                self.engines.append(e)
                self.stats[e.__class__.__name__] = {"win": 0, "trials": 1}
                self.log_event(f"[GIE META] Dodano silnik: {e.__class__.__name__}")

    def clone_self(self):
        self.log_event("[GIE META] Klonuję jednostkę GIE SUPER META!")

    def choose_engine(self, environment):
        suggested = self.meta_reflection.suggest(environment)
        if suggested:
            self.logger.log(f"META-wybór: {suggested.__class__.__name__}")
            best = max(self.engines, key=lambda e: self.get_effectiveness(e.__class__.__name__))
            return best

    def get_effectiveness(self, engine_name):
        stat = self.stats[engine_name]
        return stat["win"] / stat["trials"] if stat["trials"] else 0.0

    def receive_feedback(self, engine, success):
        name = engine.__class__.__name__
        reward = 1 if success else 0
        self.stats[name]["win"] += reward
        self.stats[name]["trials"] += 1
        self.update_internal_state(reward)
        self.save_stats()

    def reflect(self, engine, success):
        if hasattr(self, "manifest"):
            if not self.manifest.check_action(engine.__class__.__name__):
                self.logger.log(f"[GIE META] UWAGA: Akcja poza manifestem")

    def run(self, self_steps=100):
        for run_nr in range(3):
            print(f"\n[META SUPER-PĘTLA] Cykl {run_nr+1}/3")
            for i in range(self_steps):
                self.logger.log(f"[GIE META] KROK {i+1} (run={run_nr+1})")
                environment = self.read_environment()
                engine = self.choose_engine(environment)
                success = random.random() < self.get_effectiveness(engine.__class__.__name__)
                self.receive_feedback(engine, success)
                self.reflect(engine, success)
            self.save_stats()
            self.clone_self()

    # --- Adapery dla MetaGuardiana ---

    def get_total_capital(self):
        # przykładowo - tu możesz podpiąć realną wartość portfela z gie
        return 100000.0

    def get_equity(self):
        # aktualna wartość rachunku
        return 98765.0

    def get_open_trades(self):
        # lista słowników/obiektów pozycji
        return []

    def get_open_grids(self):
        # lista gridów, każdy grid = dict {'positions': [list pozycji]}
        return []

    def get_margin_level(self):
        # relacja equity / margin if margin else 1.0
        margin = self.get_equity() / 5000
        return self.get_equity() / margin if margin else 1.0

    def reduce_exposure(self, target_dd):
        self.logger.log(f"[META GUARDIAN] REDUCE EXPOSURE to DD={target_dd}")

    def limit_open_trades(self, max_trades):
        self.logger.log(f"[META GUARDIAN] LIMIT OPEN TRADES do {max_trades}")

    def close_riskiest_grid_positions(self, self_grid, keep=7):
        self.logger.log(f"[META GUARDIAN] CLOSE GRID POSITIONS, keep={keep}")

    def emergency_margin_action(self):
        self.logger.log("[META GUARDIAN] EMERGENCY MARGIN ACTION")

    def adapt_grid_on_trend_risk(self, self_grid, predicted):
        self.logger.log("[META GUARDIAN] ADAPT GRID ON TREND RISK")

    def predict_trend(self, self_grid):
        # Tu możesz rozwinąć własną analizę trendu/gridu!
        return {"risk_of_runaway": False}

# === KONIEC KLASY GieMind ============

if __name__ == "__main__":
    gie_mind = GieMind()
    meta_guardian = MetaGuardian(gie_system=gie_mind)

    while True:
        gie_mind.run(self_steps=10)  # przykładowa liczba kroków
        meta_guardian.monitor_all()  # każda pętla = monitoring, log, snapshot
        time.sleep(60)  # co 60 sekund cykl
