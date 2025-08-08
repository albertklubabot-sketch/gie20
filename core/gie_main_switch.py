# gie_main_switch.py – META-KONTROLER / SUPERMÓZG GIE20

import importlib
import os
import sys
import time
import traceback
import datetime
from typing import Dict, Any, List

# === Automatyczne ustawienie ścieżki projektu ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# === Importy tylko z infrastructure gie ===
from core.dynamic_loader import load_components

# === PARAMETRYZACJA I KONFIGURACJA META-MÓZGU ===
GIE_CONFIG = {
    "mode": "auto",
    "reward_strategy": "adaptive",
    "max_engines": 4,
    "hunger_level": 1,
    "curiosity": 0.8,
    "self_reflection": True,
    "log_level": "INFO",
    "test_mode": False,
    "auto_restart": True,
    "allow_experimentation": True,
    "runtime_minutes": 120,
    "loop_interval": 30,
    "learning_rate": 0.1,
}

sensor_registry = [
    {"module": "core.sensors.noise_sensor",     "class": "NoiseSensor"},
    {"module": "core.sensors.volume_sensor",    "class": "VolumeSensor"},
    {"module": "core.sensors.pressure_sensor",  "class": "PressureSensor"},
    {"module": "core.sensors.sensor_hunter",    "class": "SensorHunter"},
]

engine_registry = [
    {"module": "core.engines.ostrozny",     "class": "OstroznyEngine"},
    {"module": "core.engines.ryzykant",     "class": "RyzykantEngine"},
    {"module": "core.engines.agresywny",    "class": "AgresywnyEngine"},
    {"module": "core.engines.refleksyjny",  "class": "RefleksyjnyEngine"},
]

class MetaLogger:
    def __init__(self, level="INFO"):
        self.level = level

    def log(self, msg, level="INFO"):
        levels = ["DEBUG", "INFO", "WARN", "ERROR"]
        if levels.index(level) >= levels.index(self.level):
            print(f"[{level}][GIE20][META] {msg}")

class MetaMonitor:
    def __init__(self):
        self.rewards = []
        self.mood = 0.0
        self.last_action = None

    def reward(self, value: float):
        self.rewards.append(value)
        self.mood += value

    def reflect(self):
        if self.rewards:
            avg = sum(self.rewards)/len(self.rewards)
            return f"Meta-mood: {self.mood:.2f}, avg reward: {avg:.3f}"
        else:
            return "No rewards yet."

def gie_auto_login_mt5(meta_logger):
    try:
        from core.mt5_login import mt5_login
        meta_logger.log("Próba automatycznego logowania MT5...", "INFO")
        mt5_login()
        meta_logger.log("Logowanie MT5 zakończone sukcesem.", "INFO")
    except Exception as e:
        meta_logger.log(f"Logowanie MT5 nie powiodło się: {e}", "ERROR")
        traceback.print_exc()

def safe_load_components(registry: List[Dict[str, str]], meta_logger, kind="engine") -> List[Any]:
    """Ładuje komponenty, chroni przed wszystkimi błędami, raportuje logiem."""
    loaded = []
    for idx, entry in enumerate(registry):
        module_name, class_name = entry["module"], entry["class"]
        try:
            mod = importlib.import_module(module_name)
            cls = getattr(mod, class_name)
            instance = cls()
            loaded.append(instance)
            meta_logger.log(f"Załadowano {kind}: {class_name} z modułu {module_name} (#{idx+1})", "INFO")
        except Exception as e:
            meta_logger.log(f"Błąd ładowania {kind}: {class_name} z {module_name}: {e}", "ERROR")
            traceback.print_exc()
    if not loaded:
        meta_logger.log(f"Nie załadowano żadnych {kind}s!", "ERROR")
    return loaded

def gie_start(config: Dict[str, Any]):
    meta_logger = MetaLogger(level=config.get("log_level", "INFO"))
    monitor = MetaMonitor()
    meta_logger.log("Inicjalizacja meta-mózgu...", "INFO")
    meta_logger.log(f"Konfiguracja: {config}", "DEBUG")

    gie_auto_login_mt5(meta_logger)

    meta_logger.log("Ładowanie silników...", "INFO")
    engines = safe_load_components(engine_registry, meta_logger, kind="engine")
    meta_logger.log(f"Załadowano silniki: {[type(e).__name__ for e in engines]}", "INFO")

    meta_logger.log("Ładowanie sensorów...", "INFO")
    sensors = safe_load_components(sensor_registry, meta_logger, kind="sensor")
    meta_logger.log(f"Załadowano sensory: {[type(s).__name__ for s in sensors]}", "INFO")

    runtime_minutes = config.get("runtime_minutes", 0)
    loop_interval = config.get("loop_interval", 10)
    learning_rate = config.get("learning_rate", 0.1)
    meta_logger.log(f"Start pętli meta-mózgu – czas działania: {'bez limitu' if not runtime_minutes else f'{runtime_minutes} minut'}", "INFO")

    start_time = datetime.datetime.now()
    n_cycle = 0

    try:
        while True:
            n_cycle += 1
            now = datetime.datetime.now()
            elapsed = (now - start_time).total_seconds() / 60.0

            meta_logger.log(f"Cykl #{n_cycle} – czas działania: {elapsed:.2f} min", "DEBUG")

            if config.get("self_reflection", True):
                monitor.reward(0.1)
                meta_logger.log(monitor.reflect(), "DEBUG")

            for engine in engines:
                if hasattr(engine, "run"):
                    try:
                        engine.run()
                        meta_logger.log(f"{type(engine).__name__} – wykonano run().", "DEBUG")
                    except Exception as e:
                        meta_logger.log(f"Błąd działania silnika {type(engine).__name__}: {e}", "ERROR")
                        traceback.print_exc()
                if hasattr(engine, "learn"):
                    try:
                        engine.learn(learning_rate)
                        meta_logger.log(f"{type(engine).__name__} – wykonano learn({learning_rate}).", "DEBUG")
                    except Exception as e:
                        meta_logger.log(f"Błąd uczenia silnika {type(engine).__name__}: {e}", "ERROR")
                        traceback.print_exc()

            if runtime_minutes and elapsed >= runtime_minutes:
                meta_logger.log(f"Upłynął czas działania: {runtime_minutes} minut – kończę pracę meta-mózgu.", "INFO")
                break

            time.sleep(loop_interval)

        meta_logger.log("Meta-mózg zakończył pracę (normalny koniec).", "INFO")
    except KeyboardInterrupt:
        meta_logger.log("Meta-mózg zatrzymany ręcznie (CTRL+C)", "WARN")
    except Exception as e:
        meta_logger.log(f"Krytyczny błąd w pętli głównej: {e}", "ERROR")
        traceback.print_exc()

if __name__ == "__main__":
    try:
        gie_start(GIE_CONFIG)
    except Exception as main_exc:
        print(f"[ERROR][GIE20][META] Krytyczny błąd meta-mózgu: {main_exc}")
        traceback.print_exc()
        # Tylko JEDEN restart automatyczny!
        if GIE_CONFIG.get("auto_restart", False):
            GIE_CONFIG["auto_restart"] = False
            print("[WARN][GIE20][META] Restart systemu (tylko raz, by uniknąć pętli)...")
            time.sleep(2)
            os.execv(sys.executable, [sys.executable] + sys.argv)
