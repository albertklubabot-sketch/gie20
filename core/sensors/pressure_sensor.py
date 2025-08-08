import numpy as np
import time
import copy
import threading
import json
import os
from datetime import datetime
from core.base_sensor import BaseSensor

class SuperPressureSensor:
    def __init__(
        self, 
        window=100, 
        base_pressure=1.0, 
        learning_rate=0.1,
        sensor_id=None,
        auto_log_path="data/pressure_super_history.log",
        cloud_sync=False
    ):
        self.window = window
        self.base_pressure = base_pressure
        self.adaptive_pressure = base_pressure
        self.learning_rate = learning_rate
        self.buffer = []
        self.history = []
        self.cloud_sync = cloud_sync
        self.id = sensor_id or f"SuperPressure_{int(time.time() * 1000)}"
        self.clone_count = 0
        self.last_alert_time = 0
        self.auto_log_path = auto_log_path
        self.hunger = 0
        self.growth_signal = False
        self.knowledge_bank = set()
        
    def read(self, tick_data):
        # Walidacja wejścia
        if not tick_data or "pressure" not in tick_data:
            return self._result(0, False, 0, 0, "Brak tick_data", level="low")
        
        pressure = tick_data['pressure']
        volume = tick_data.get('volume', 1.0)
        bid = tick_data.get('bid', 0.0)
        ask = tick_data.get('ask', 0.0)
        spread = tick_data.get('spread', ask - bid if ask and bid else 0.0)
        timestamp = tick_data.get('time', time.time())
        meta = tick_data.get('meta', None)

        # Buforowanie
        self.buffer.append({'pressure': pressure, 'volume': volume, 'spread': spread, 'time': timestamp})
        if len(self.buffer) > self.window:
            self.buffer.pop(0)

        # Statystyki
        pressures = np.array([b['pressure'] for b in self.buffer])
        mean_pressure = np.mean(pressures)
        std_pressure = np.std(pressures)
        max_pressure = np.max(pressures)
        min_pressure = np.min(pressures)
        range_pressure = max_pressure - min_pressure

        # Adaptacyjny próg, samouczenie
        recent_vol = np.std(pressures[-min(10, len(pressures)):]) if len(pressures) > 10 else std_pressure
        self.adaptive_pressure = self.base_pressure + self.learning_rate * (recent_vol + self.hunger)

        # Detekcja anomalii
        anomaly = pressure > (self.adaptive_pressure * 2) or pressure < (self.adaptive_pressure * 0.5)
        micro_spikes = np.sum(np.abs(pressures - mean_pressure) > self.adaptive_pressure)
        pressure_trend = np.polyfit(np.arange(len(pressures)), pressures, 1)[0] if len(pressures) > 5 else 0.0

        # Samouczenie, "głód"
        if anomaly:
            self.hunger = max(0, self.hunger - 1)
        else:
            self.hunger += 0.1
        self.growth_signal = self.hunger > 5

        # Baza wiedzy o anomaliach
        unique_pattern = f"{mean_pressure:.4f}:{std_pressure:.4f}:{max_pressure:.4f}:{min_pressure:.4f}:{micro_spikes}"
        if unique_pattern not in self.knowledge_bank and anomaly:
            self.knowledge_bank.add(unique_pattern)

        # Diagnostyka
        level = "high" if anomaly else ("hungry" if self.hunger > 3 else "ok")
        info = f"{level.upper()} | pres={pressure:.5f} µ={mean_pressure:.5f} σ={std_pressure:.5f} spikes={micro_spikes} hunger={self.hunger:.2f}"

        if anomaly and (time.time() - self.last_alert_time > 1):
            print(f"[{self.id}] ⚠️ ANOMALIA! {info}")
            self.last_alert_time = time.time()
        elif self.growth_signal:
            print(f"[{self.id}] 🟡 SYGNAŁ ROZWOJU! Hunger={self.hunger:.2f}")

        # Logowanie
        result = self._result(mean_pressure, anomaly, std_pressure, pressure_trend, info, level)
        self.history.append(result)
        if len(self.history) > 1000:
            self.history.pop(0)
        self._auto_log(result)

        if self.cloud_sync:
            self._sync_cloud(result)

        return result

    def _result(self, mean_pressure, anomaly, std_pressure, pressure_trend, info, level):
        return {
            "id": self.id,
            "mean_pressure": mean_pressure,
            "anomaly": anomaly,
            "std_pressure": std_pressure,
            "pressure_trend": pressure_trend,
            "info": info,
            "hunger": self.hunger,
            "growth_signal": self.growth_signal,
            "timestamp": datetime.now().isoformat(),
            "level": level
        }

    def _auto_log(self, result):
        os.makedirs(os.path.dirname(self.auto_log_path), exist_ok=True)
        with open(self.auto_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")

    def clone(self):
        self.clone_count += 1
        new_sensor = copy.deepcopy(self)
        new_sensor.id = f"{self.id}_clone{self.clone_count}"
        print(f"[{self.id}] Klonuję siebie! Nowy sensor: {new_sensor.id}")
        return new_sensor

    def self_tune(self):
        # Automatyczne dostrajanie
        if self.hunger > 6:
            self.base_pressure *= 0.95
        elif self.hunger < 1:
            self.base_pressure *= 1.03
        self.base_pressure = np.clip(self.base_pressure, 0.001, 1000)

    def __repr__(self):
        return f"<SuperPressureSensor id={self.id} hunger={self.hunger:.2f} buffer={len(self.buffer)}/{self.window} adaptive_pressure={self.adaptive_pressure:.4f}>"

    def _sync_cloud(self, result):
        # Przestrzeń do synchronizacji z chmurą/rojem
        pass

if __name__ == "__main__":
    sensor = SuperPressureSensor()
    # Symulacja działania
    for i in range(200):
        pressure = 1.0 + np.random.normal(0, 0.4)
        tick = {'pressure': pressure, 'volume': np.random.randint(1, 20), 'bid': 100, 'ask': 100.1}
        sensor.read(tick)
        if sensor.growth_signal:
            new_sensor = sensor.clone()
            break
import numpy as np

class PressureSensor:
    def activate(self):
        print("[PressureSensor] Sensor ciśnienia aktywowany")

    def mutate(self):
        print("[PressureSensor] Przetwarzanie mutacyjne ciśnienia")

    def evaluate(self, test_data):
        """
        Ocena skuteczności sensora ciśnienia na podstawie danych testowych.
        Zwraca zakres zmian ciśnienia (różnica max - min).
        """
        if test_data is None or len(test_data) == 0:
            return 0.0
        import numpy as np
        return float(np.max(test_data) - np.min(test_data))  # Zakres zmian ciśnienia
