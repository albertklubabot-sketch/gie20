# ==== ETAP 1: Importy i konfiguracja ====
from core.base_engine import BaseEngine
import os
import json
import random
import numpy as np
from datetime import datetime
import glob
import importlib

from utils.logger import Logger
from utils.meta_logger import MetaLogger
from core.meta_reflection import MetaReflection
from core.gie_manifest import gie_manifest

from core.sensors.noise_sensor import NoiseSensor
from core.sensors.volume_sensor import VolumeSensor
from core.sensors.pressure_sensor import PressureSensor
from core.sensors.sensor_hunter import SensorHunter

from core.meta_guardian import MetaGuardian


# === GLOBALNE PARAMETRY ===
GIE_CONFIG = {
    "max_drawdown": 0.2,
    "max_open_trades": 10,
    "candl_size": "1H",
    "min_equity_margin": 0.25,
    "alert_email": "",
    "snapshot_dir": "./data/snapshots",
    "monitor_cycle_sec": 600,
}

RYZYKANT_PARAMS = {
    "name": "Ryzykant",
    "risk_level": 0.85,
    "curiosity": 0.8,
    "hunger": 1.0,
    "reward_bias": 1.3
}

# ==== ETAP 2: Klasa RyzykantEngine ====
class RyzykantEngine(BaseEngine):
    def __init__(
        self,
        name="Ryzykant",
        symbol="EURUSD",
        lot=0.01,
        sensors=None,
        hive=None,
        config=None,
        risk_level=0.85,
        curiosity=0.8,
        hunger=1.0,
        reward_bias=1.3,
        allowed_symbols=None,
        meta_guardian=None,
        **kwargs
    ):
        super().__init__(
            name=name,
            symbol=symbol,
            lot=lot,
            sensors=sensors or [],
            hive=hive,
            config=config,
            **kwargs
        )

        self.risk_level = risk_level
        self.curiosity = curiosity
        self.hunger = hunger
        self.reward_bias = reward_bias
        self.allowed_symbols = allowed_symbols or ["EURUSD", "XAUUSD", "BTCUSD", "USDJPY", "XAGUSD"]
        self.meta_guardian = meta_guardian

        self.memory = []
        self.last_action = None
        self.last_reward = 0.0
        self.clone_count = 0
        self.mts_connected = False
        self.status = "initialized"
        self.meta_state = {}
        self.meta_logger = MetaLogger()

        # Logowanie do MT5
        try:
            import data_providers.mt5_data as mt5_data
            mts_cfg_path = os.path.join(os.path.dirname(__file__), "..", "mt5_secrets.json")
            if os.path.exists(mts_cfg_path):
                with open(mts_cfg_path, "r", encoding="utf-8") as f:
                    mts_secrets = json.load(f)
                    MTS_LOGIN = mts_secrets.get("MTS_LOGIN")
                    MTS_PASSWORD = mts_secrets.get("MTS_PASSWORD")
                    MTS_SERVER = mts_secrets.get("MTS_SERVER")

                import MetaTrader5 as mt5
                if not mt5.initialize():
                    self.meta_logger.error(f"[MTS] Błąd inicjalizacji: {mt5.last_error()}")
                elif not mt5.login(login=MTS_LOGIN, password=MTS_PASSWORD, server=MTS_SERVER):
                    self.meta_logger.error(f"[MTS] Błąd logowania: {mt5.last_error()}")
                else:
                    self.meta_logger.info(f"[MTS] Zalogowano do MTS (user: {MTS_LOGIN})")
                    self.mts_connected = True
        except Exception as ex:
            self.meta_logger.error(f"[MTS][ERROR] Import/Login MTS: {ex}")

    def decide(self, sensors, market_data=None, feedback=None, meta_context=None):
        noise = sensors.get("noise", 0)
        pressure = sensors.get("pressure", 0)
        volume = sensors.get("volume", 0)
        alt_signals = sensors.get("alt_data", {})

        base_chance = self.analyze_market(sensors, noise, pressure, volume, alt_signals)
        risk_appetite = self.risk_level * 0.1 + self.hunger * 0.2 + self.curiosity * 0.05
        expected_value = base_chance * self.reward_bias * risk_appetite

        threshold = 0.5 + 0.25 * self.risk_level
        action = "WAIT"

        if expected_value > threshold:
            action = "OPEN_NORMAL_POSITION"
        elif expected_value > 0.3:
            action = "OPEN_LARGE_POSITION"
        elif random.random() < self.curiosity * 0.12:
            action = random.choice(["OPEN_LARGE_POSITION", "OPEN_NORMAL_POSITION", "WAIT"])

        self.meta_state["last_decision"] = {
            "risk_appetite": risk_appetite,
            "expected_value": expected_value,
            "base_chance": base_chance,
            "noise": noise,
            "pressure": pressure,
            "volume": volume,
            "alt_signals": alt_signals,
            "action": action
        }

        self.meta_logger.debug(f"[DECIDE] {action} | EV: {expected_value:.3f} | base: {base_chance:.3f}")
        return action

    def analyze_market(self, sensors, noise, pressure, volume, alt_signals):
        try:
            opportunity = 0.2 * (pressure + 0.3 * volume + 0.2) + (noise * 0.05)
            if isinstance(alt_signals, dict):
                for k, v in alt_signals.items():
                    opportunity += float(v) * 0.05
            opportunity *= self.reward_bias
            return np.clip(opportunity, 0, 1.2)
        except Exception as e:
            self.meta_state["analyze_market_error"] = str(e)
            self.meta_logger.error(f"[ANALYZE_MARKET][ERROR]: {e}")
            return 0.1

    def open_trade(self, direction="buy", lot=None):
        self.meta_logger.info(f"[TRADE] Otwarto pozycję: {direction}, lot={lot or self.lot}")
        return True  # symulacja

    def run(self):
        sensors = {
            "noise": random.uniform(0, 1),
            "pressure": random.uniform(0, 1),
            "volume": random.uniform(0, 1),
            "alt_data": {}
        }
        action = self.decide(sensors)
        result = None
        profit = 0

        if action == "OPEN_NORMAL_POSITION":
            result = self.open_trade("buy")
            profit = random.uniform(-10, 10) if result else -5
        elif action == "OPEN_LARGE_POSITION":
            result = self.open_trade("buy", lot=self.lot * 2)
            profit = random.uniform(-20, 20) if result else -10
        else:
            self.meta_logger.debug("[RyzykantEngine] Czekam...")
            return

        if result:
            self.meta_logger.info(f"[RyzykantEngine] Wynik: {profit:.2f}")
            self.feedback(result, profit)

        self.explore_params()
        if self.clone_count < 2 and random.random() < 0.25:
            self.clone_self()

    def feedback(self, result, profit, meta_feedback=None):
        reward = profit if profit else 0
        self.last_reward = reward
        self.hunger = max(self.hunger - 0.1, 0.5)
        self.curiosity = np.clip(self.curiosity + reward * 0.01, 0.1, 1.0)
        self.risk_level = min(1.0, self.risk_level + reward * 0.01)
        self.reward_bias = max(self.reward_bias + random.uniform(-0.03, 0.1), 0.3)
        self.meta_logger.debug(f"[FEEDBACK] Reward={reward:.2f}, hunger={self.hunger:.2f}, risk={self.risk_level:.2f}")

    def explore_params(self):
        self.risk_level = min(1.0, max(0.2, self.risk_level + random.uniform(-0.1, 0.1)))
        self.curiosity = min(1.0, max(0.2, self.curiosity + random.uniform(-0.05, 0.05)))
        self.hunger = min(1.0, max(0.2, self.hunger + random.uniform(-0.1, 0.1)))
        self.reward_bias = min(1.2, max(0.5, self.reward_bias + random.uniform(-0.1, 0.1)))
        self.meta_logger.debug(f"[EXPLORE] r={self.risk_level:.2f}, c={self.curiosity:.2f}, h={self.hunger:.2f}, rb={self.reward_bias:.2f}")

    def clone_self(self, new_symbol=None):
        self.clone_count += 1
        new_symbol = new_symbol or self.choose_new_symbol()
        clone = RyzykantEngine(
            name=f"{self.__class__.__name__}_clone_{self.clone_count}",
            risk_level=self.risk_level,
            curiosity=self.curiosity,
            hunger=self.hunger,
            reward_bias=self.reward_bias,
            lot=self.lot,
            symbol=new_symbol,
            allowed_symbols=self.allowed_symbols,
            meta_guardian=self.meta_guardian
        )
        self.meta_logger.info(f"[CLONE] Utworzono klona: {new_symbol}")
        return clone

    def choose_new_symbol(self):
        unexplored = [s for s in self.allowed_symbols if s != self.symbol]
        return random.choice(unexplored) if unexplored else self.symbol

    def evaluate(self, test_data):
        return max(test_data) * 1.5


# ==== ETAP 3: AutoHunterMixin ====
class AutoHunterMixin:
    def auto_discover_and_add_sensors(self, sensors_folder=None):
        sensors_folder = sensors_folder or os.path.join(os.path.dirname(__file__), "sensors")
        if not os.path.isdir(sensors_folder):
            print(f"[ERROR] Brak katalogu sensors: {sensors_folder}")
            return
        sensor_files = glob.glob(os.path.join(sensors_folder, "*.py"))
        for sensor_file in sensor_files:
            module_name = os.path.splitext(os.path.basename(sensor_file))[0]
            if module_name.startswith("_"):
                continue
            try:
                mod = importlib.import_module(f"core.sensors.{module_name}")
                for attr in dir(mod):
                    if attr.endswith("Sensor") and attr != "BaseSensor":
                        sensor_cls = getattr(mod, attr)
                        if not any(isinstance(s, sensor_cls) for s in getattr(self, "sensors", [])):
                            if not hasattr(self, "sensors"):
                                self.sensors = []
                            self.sensors.append(sensor_cls())
                            print(f"[AutoHunter] Dodano sensor: {attr}")
            except Exception as e:
                print(f"[AutoHunter][ERROR] Sensor {module_name}: {e}")

    def auto_discover_and_add_strategies(self, strategies_folder=None):
        strategies_folder = strategies_folder or os.path.join(os.path.dirname(__file__), "engines")
        if not os.path.isdir(strategies_folder):
            print(f"[ERROR] Brak katalogu engines: {strategies_folder}")
            return
        strategy_files = glob.glob(os.path.join(strategies_folder, "*.py"))
        for strategy_file in strategy_files:
            module_name = os.path.splitext(os.path.basename(strategy_file))[0]
            if module_name.startswith("_"):
                continue
            try:
                mod = importlib.import_module(f"core.engines.{module_name}")
                for attr in dir(mod):
                    if attr.endswith("Engine") and attr != "BaseEngine":
                        print(f"[AutoHunter] Zarejestrowano silnik: {attr}")
            except Exception as e:
                print(f"[AutoHunter][ERROR] Strategia {module_name}: {e}")


# ==== ETAP 4: Klasa super-agenta ====
class FullyAutonomousRyzykant(RyzykantEngine, AutoHunterMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auto_discover_and_add_sensors()
        self.auto_discover_and_add_strategies()

    def run(self):
        self.auto_discover_and_add_sensors()
        self.auto_discover_and_add_strategies()
        super().run()
