import sys
import os
import importlib
import pkgutil

# --- Dodawanie głównych folderów do sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for subfolder in ['engines', 'sensors', 'data_providers', 'utils']:
    folder_path = os.path.join(BASE_DIR, subfolder)
    if not os.path.isdir(folder_path):
        print(f"[WARN] Folder nie istnieje: {folder_path}")
    sys.path.append(folder_path)

# === Importy rdzenia (core) ===
from core.gie_mind import GieMind
from core.meta_reflection import MetaReflection
from core.gie_hive import GieHive

# === Import loggerów ===
from utils.logger import Logger
from utils.meta_logger import MetaLogger

# === Dynamiczne ładowanie silników ===
def load_engines():
    engines = []
    engine_path = os.path.join(os.path.dirname(__file__), "engines")
    if not os.path.isdir(engine_path):
        print(f"[ERROR] Folder engines nie istnieje: {engine_path}")
        return engines
    for importer, modname, ispkg in pkgutil.iter_modules([engine_path]):
        if not modname.startswith('_'):
            module = importlib.import_module(f"engines.{modname}")
            for attr in dir(module):
                if attr.endswith("Engine"):
                    engine_class = getattr(module, attr)
                    if callable(engine_class):
                        try:
                            engines.append(engine_class())
                        except Exception as e:
                            print(f"Nie udało się załadować silnika {attr}: {e}")
    return engines

# === Dynamiczne ładowanie sensorów ===
def load_sensors():
    sensors = {}
    sensor_path = os.path.join(os.path.dirname(__file__), "sensors")
    if not os.path.isdir(sensor_path):
        print(f"[ERROR] Folder sensors nie istnieje: {sensor_path}")
        return sensors
    for importer, modname, ispkg in pkgutil.iter_modules([sensor_path]):
        if not modname.startswith('_'):
            module = importlib.import_module(f"sensors.{modname}")
            for attr in dir(module):
                if attr.endswith("Sensor"):
                    sensor_class = getattr(module, attr)
                    if callable(sensor_class):
                        try:
                            instance = sensor_class()
                            name = attr.replace("Sensor", "").lower()
                            sensors[name] = instance
                        except Exception as e:
                            print(f"Nie udało się załadować sensora {attr}: {e}")
    return sensors

def run_gie(steps=100):
    logger = Logger()
    meta_logger = MetaLogger()

    # Przykład działania loggera (możesz rozbudować lub wykomentować)
    logger.log("System started")
    logger.log_event("boot", {"status": "OK"})
    logger.log_metric("profit", 123.45)
    logger.log_error("Testowy błąd")

    actions = meta_logger.auto_action()
    for act in actions:
        logger.log(f"META_ACTION::{act}")

    # === Dynamiczne ładowanie silników i sensorów ===
    engines = load_engines()
    sensors = load_sensors()

    # === Inicjalizacja GieMind z meta-refleksją ===
    gie = GieMind(engines=engines, sensors=sensors)
    gie.meta_reflection = MetaReflection()

    # === Podpięcie loggera do silników i sensorów ===
    for engine in engines:
        engine.logger = gie.log_event
    for sensor in sensors.values():
        sensor.logger = gie.log_event

    print(f"[GIE] Uruchamiam GieMind z {len(engines)} silnikami i {len(sensors)} sensorami na {steps} kroków.")
    gie.run(steps=steps)

def run_hive(agent_count=3, steps=100):
    hive = GieHive(agent_count=agent_count)
    print(f"[GIE] Uruchamiam GieHive: {agent_count} agentów x {steps} kroków.")
    hive.run_all(steps=steps)
    hive.synchronize_knowledge()
    hive.clone_best()
    hive.remove_worst()
    hive.run_all(steps=steps)

if __name__ == "__main__":
    # Domyślnie uruchamiamy tryb "jednego Gie z meta-refleksją i logowaniem"
    run_gie(steps=100)

    # Jeśli chcesz uruchomić multiagenta (Hive), odkomentuj poniżej:
    # run_hive(agent_count=3, steps=100)
