import numpy as np
import time
import uuid
import copy
import threading
import json
import os
from datetime import datetime

# =======================
# SYSTEM HIVE: ROJ INTELIGENCJI
# =======================
class Hive:
    """Zarządzanie rojami sensorów i wymianą wiedzy."""
    def __init__(self):
        self.members = []
        self.knowledge_bank = set()

    def add(self, sensor):
        self.members.append(sensor)
        print(f"[HIVE] Dodano sensor: {sensor.name}")

    def share_knowledge(self):
        """Wspólna wymiana wiedzy między wszystkimi sensorami w roju."""
        for sensor in self.members:
            sensor.knowledge_bank.update(self.knowledge_bank)
            self.knowledge_bank.update(sensor.knowledge_bank)
        print("[HIVE] Knowledge sharing completed.")

    def broadcast(self, msg):
        """Rozsyłanie sygnału do wszystkich sensorów w roju."""
        for sensor in self.members:
            sensor.receive_broadcast(msg)

# =======================
# SYSTEM HUNTER: DYNAMICZNE PODPINANIE ŹRÓDEŁ/NARZĘDZI
# =======================
class HunterTools:
    """Wstęp do integracji dynamicznych narzędzi i źródeł danych."""
    def __init__(self):
        self.tools = {}
        self.data_providers = {}

    def add_tool(self, name, tool_fn):
        self.tools[name] = tool_fn
        print(f"[HUNTER] Dodano narzędzie: {name}")

    def add_data_provider(self, name, provider_fn):
        self.data_providers[name] = provider_fn
        print(f"[HUNTER] Dodano źródło danych: {name}")

    def use_tool(self, name, *args, **kwargs):
        if name in self.tools:
            return self.tools[name](*args, **kwargs)
        print(f"[HUNTER] Tool {name} not found!")
        return None

    def get_data(self, name, *args, **kwargs):
        if name in self.data_providers:
            return self.data_providers[name](*args, **kwargs)
        print(f"[HUNTER] Data provider {name} not found!")
        return None

# =======================
# KLASA BAZOWA SENSORA
# =======================
class BaseSensor:
    def __init__(
            self,
            name="BaseSensor",
            sensitivity=1.0,
            memory_size=1000,
            learning_rate=0.1,
            auto_log_path="data/base_sensor_history.log",
            cloud_sync=False,
            window=120,
            base_level=1.0,
            sensor_id=None,
            hive=None,
            hunter=None
    ):
        self.id = sensor_id or str(uuid.uuid4())
        self.name = name
        self.sensitivity = sensitivity
        self.memory_size = memory_size
        self.memory = []
        self.status = "OK"
        self.last_value = None
        self.last_detection_time = None
        self.learning_rate = learning_rate
        self.autoconclone_count = 0

        # Zaawansowane bufory dla bardziej złożonych sensorów
        self.window = window
        self.base_level = base_level
        self.adaptive_level = base_level
        self.buffer = []
        self.history = []
        self.hunger = 0
        self.growth_signal = False
        self.knowledge_bank = set()
        self.last_alert_time = 0

        # Integracje z systemami hive/hunter
        self.hive = hive
        self.hunter = hunter

        # Logowanie / chmura
        self.auto_log_path = auto_log_path
        self.cloud_sync = cloud_sync

    # --- PODSTAWOWA DETEKCJA ---
    def detect(self, data):
        detection = self.sensitivity * np.mean(data)
        self.last_value = detection
        self.memory.append((time.time(), detection))
        if len(self.memory) > self.memory_size:
            self.memory.pop(0)
        self.last_detection_time = time.time()
        return detection

    def receive_broadcast(self, msg):
        """Obsługa komunikatów z roju/hive."""
        print(f"[{self.name}] Received broadcast: {msg}")

    # --- ADAPTACJA I UCZENIE ---
    def adjust_sensitivity(self, feedback):
        old = self.sensitivity
        if feedback == "false_positive":
            self.sensitivity = max(0.01, self.sensitivity - self.learning_rate)
        elif feedback == "missed_event":
            self.sensitivity = min(10.0, self.sensitivity + self.learning_rate)
        print(f"[{self.name}] Sensitivity changed: {old:.3f} -> {self.sensitivity:.3f}")

    def reflect(self):
        if not self.memory:
            return None
        values = np.array([val for (_, val) in self.memory])
        mean = np.mean(values)
        std = np.std(values)
        reflection = {
            "mean": mean,
            "std": std,
            "memory_size": len(self.memory),
            "last_value": self.last_value
        }
        print(f"[{self.name}] Reflection: {reflection}")
        return reflection

    # --- SAMOREPLIKACJA / KLONOWANIE ---
    def autoclone(self):
        self.autoconclone_count += 1
        clone = self.__class__(
            name=f"{self.name}_clone{self.autoconclone_count}",
            sensitivity=self.sensitivity * np.random.uniform(0.8, 1.2),
            memory_size=self.memory_size,
            learning_rate=self.learning_rate,
            auto_log_path=self.auto_log_path,
            window=self.window,
            base_level=self.base_level,
            hive=self.hive,
            hunter=self.hunter
        )
        print(f"[{self.name}] Autoclone created: {clone.name}")
        if self.hive:
            self.hive.add(clone)
        return clone

    def clone(self):
        self.autoconclone_count += 1
        new_sensor = copy.deepcopy(self)
        new_sensor.id = f"{self.id}_clone{self.autoconclone_count}"
        print(f"[{self.id}] Klonuję siebie! Nowy sensor: {new_sensor.id}")
        if self.hive:
            self.hive.add(new_sensor)
        return new_sensor

    # --- LOGOWANIE I CLOUD ---
    def _auto_log(self, result):
        try:
            os.makedirs(os.path.dirname(self.auto_log_path), exist_ok=True)
            with open(self.auto_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Log error: {e}")

    def _sync_cloud(self, result):
        # Wersja demo – podłącz pod GIE-hive/cloud
        pass

    # --- DEBUG / PRINT ---
    def __repr__(self):
        return f"<{self.name} id={self.id} hunger={self.hunger:.2f} adaptive_level={self.adaptive_level:.2f}>"

# ============================
# SPECJALISTYCZNE SENSORY
# ============================

class NoiseSensor(BaseSensor):
    """Zaawansowany sensor do analizy szumu rynkowego."""
    def read(self, tick_data):
        # Szum: np. niestabilność lub ilość mikrofluktuacji
        if not tick_data or "noise" not in tick_data:
            return None
        noise = tick_data['noise']
        self.buffer.append(noise)
        if len(self.buffer) > self.window:
            self.buffer.pop(0)
        std_noise = np.std(self.buffer)
        mean_noise = np.mean(self.buffer)
        self.adaptive_level = self.base_level + self.learning_rate * (std_noise + self.hunger)
        anomaly = abs(noise - mean_noise) > self.adaptive_level * 2
        if anomaly:
            self.hunger = max(0, self.hunger - 1)
        else:
            self.hunger += 0.1
        self.growth_signal = self.hunger > 4.0
        info = f"noise={noise:.3f} μ={mean_noise:.3f} σ={std_noise:.3f} hunger={self.hunger:.2f}"
        result = {
            "id": self.id,
            "name": self.name,
            "noise": noise,
            "anomaly": anomaly,
            "mean_noise": mean_noise,
            "std_noise": std_noise,
            "info": info,
            "hunger": self.hunger,
            "growth_signal": self.growth_signal,
            "timestamp": datetime.now().isoformat(),
        }
        self.history.append(result)
        self._auto_log(result)
        if self.cloud_sync:
            self._sync_cloud(result)
        return result

class PressureSensor(BaseSensor):
    """Sensor do detekcji presji/ciśnienia na rynku."""
    def read(self, tick_data):
        if not tick_data or "pressure" not in tick_data:
            return None
        pressure = tick_data['pressure']
        self.buffer.append(pressure)
        if len(self.buffer) > self.window:
            self.buffer.pop(0)
        mean_p = np.mean(self.buffer)
        std_p = np.std(self.buffer)
        self.adaptive_level = self.base_level + self.learning_rate * (std_p + self.hunger)
        anomaly = abs(pressure - mean_p) > self.adaptive_level * 2
        if anomaly:
            self.hunger = max(0, self.hunger - 1)
        else:
            self.hunger += 0.14
        self.growth_signal = self.hunger > 4.2
        info = f"pressure={pressure:.2f} μ={mean_p:.2f} σ={std_p:.2f} hunger={self.hunger:.2f}"
        result = {
            "id": self.id,
            "name": self.name,
            "pressure": pressure,
            "anomaly": anomaly,
            "mean_pressure": mean_p,
            "std_pressure": std_p,
            "info": info,
            "hunger": self.hunger,
            "growth_signal": self.growth_signal,
            "timestamp": datetime.now().isoformat(),
        }
        self.history.append(result)
        self._auto_log(result)
        if self.cloud_sync:
            self._sync_cloud(result)
        return result

class SuperVolumeSensor(BaseSensor):
    """Zaawansowany sensor do analizy wolumenu."""
    def read(self, tick_data):
        if not tick_data or "volume" not in tick_data:
            return None
        volume = tick_data['volume']
        self.buffer.append(volume)
        if len(self.buffer) > self.window:
            self.buffer.pop(0)
        mean_volume = np.mean(self.buffer)
        std_volume = np.std(self.buffer)
        self.adaptive_level = self.base_level + self.learning_rate * (std_volume + self.hunger)
        anomaly = volume > (self.adaptive_level * 2) or volume < (self.adaptive_level * 0.5)
        if anomaly:
            self.hunger = max(0, self.hunger - 1)
        else:
            self.hunger += 0.11
        self.growth_signal = self.hunger > 5.5
        info = f"vol={volume:.2f} μ={mean_volume:.2f} σ={std_volume:.2f} hunger={self.hunger:.2f}"
        result = {
            "id": self.id,
            "name": self.name,
            "volume": volume,
            "anomaly": anomaly,
            "mean_volume": mean_volume,
            "std_volume": std_volume,
            "info": info,
            "hunger": self.hunger,
            "growth_signal": self.growth_signal,
            "timestamp": datetime.now().isoformat(),
        }
        self.history.append(result)
        self._auto_log(result)
        if self.cloud_sync:
            self._sync_cloud(result)
        return result

# ============================
# DEMO: JAK TO DZIAŁA
# ============================
if __name__ == "__main__":
    # Tworzymy systemy hive i hunter
    hive = Hive()
    hunter = HunterTools()
    # Dodaj narzędzia do hunter
    hunter.add_tool("normalize", lambda x: (x - np.mean(x)) / (np.std(x) + 1e-6))
    hunter.add_data_provider("example_data", lambda: np.random.normal(0, 1, 100).tolist())

    # Tworzymy sensory i dołączamy do hive
    vol_sensor = SuperVolumeSensor(name="SuperVolume", hive=hive, hunter=hunter)
    noise_sensor = NoiseSensor(name="NoiseX", hive=hive, hunter=hunter)
    pressure_sensor = PressureSensor(name="PressureX", hive=hive, hunter=hunter)
    hive.add(vol_sensor)
    hive.add(noise_sensor)
    hive.add(pressure_sensor)

    # Przykładowa symulacja ticków
    for i in range(50):
        tick_vol = {'volume': abs(np.random.normal(1.2, 0.25))}
        tick_noise = {'noise': np.random.normal(0, 1)}
        tick_pressure = {'pressure': np.random.normal(100, 4)}
        vol_sensor.read(tick_vol)
        noise_sensor.read(tick_noise)
        pressure_sensor.read(tick_pressure)

    # Wymiana wiedzy w roju
    hive.share_knowledge()

    # Test działania hunter
    data = hunter.get_data("example_data")
    normed = hunter.use_tool("normalize", np.array(data))
    print("[HUNTER TOOL] Normalized data sample:", normed[:5])

    # Autoklonowanie i refleksja
    if vol_sensor.growth_signal:
        vol_sensor.autoclone()

    vol_sensor.reflect()
    print("Hive members:", [s.name for s in hive.members])
