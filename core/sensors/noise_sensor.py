import numpy as np
import time
import copy
import threading
import json
import os
from datetime import datetime
from core.base_sensor import BaseSensor

class SuperNoiseSensor:
    def __init__(
        self, 
        window=100, 
        base_threshold=2.0, 
        sensor_id=None, 
        auto_log_path="data/noise_super_history.log",
        learning_rate=0.1,
        cloud_sync=False
    ):
        self.window = window
        self.base_threshold = base_threshold
        self.adaptive_threshold = base_threshold
        self.learning_rate = learning_rate
        self.cloud_sync = cloud_sync  # (future) możliwość synchronizacji z chmurą
        self.buffer = []
        self.history = []
        self.id = sensor_id or f"SuperNoise_{int(time.time() * 1000)}"
        self.clone_count = 0
        self.last_alert_time = 0
        self.auto_log_path = auto_log_path
        self.hunger = 0
        self.growth_signal = False
        self.knowledge_bank = set()

    def read(self, tick_data):
        # Sprawdzenie poprawności wejścia
        if not tick_data or 'price' not in tick_data:
            return self._result(0, False, 0, 0, 0, 0, "Brak tick_data", level="low")

        price = tick_data['price']
        volume = tick_data.get('volume', 1.0)
        spread = tick_data.get('spread', 0.0)
        timestamp = tick_data.get('time', time.time())
        meta = tick_data.get('meta', None)

        # Buforowanie danych
        self.buffer.append({'price': price, 'volume': volume, 'spread': spread, 'time': timestamp})
        if len(self.buffer) > self.window:
            self.buffer.pop(0)

        # Analiza zmian i meta-adaptacja progu
        prices = np.array([b['price'] for b in self.buffer])
        returns = np.diff(prices) if len(prices) > 1 else np.zeros(1)
        volatility = np.std(returns) if len(returns) > 1 else 0.0
        max_jump = np.max(np.abs(returns)) if len(returns) > 1 else 0.0

        # Meta-tuning – uczy się, jak bardzo rynek jest "szumiący"
        volatility_history = [np.std(np.diff(prices[max(0, i-10):i])) for i in range(10, len(prices))]
        recent_vol = np.mean(volatility_history) if volatility_history else 0.0
        self.adaptive_threshold = (self.base_threshold + recent_vol * 2) * (1 + self.learning_rate * self.hunger)

        # Detekcja anomalii i wzorców
        anomaly = volatility > self.adaptive_threshold or max_jump > self.adaptive_threshold * 1.5
        micro_spikes = np.sum(np.abs(returns) > self.adaptive_threshold)
        micro_lulls = np.sum(np.abs(returns) < self.adaptive_threshold * 0.12)
        pressure = volume * spread * (1 + volatility)
        
        # Samouczenie przez "głód" (hunger)
        if anomaly:
            self.hunger = max(0, self.hunger - 1)
        else:
            self.hunger += 0.1
        self.growth_signal = self.hunger > 5  # Sygnalizacja potrzeby klonowania/rozwoju

        # Sieciowa "baza wiedzy" – rozpoznaje i zapamiętuje nietypowe wzorce
        unique_pattern = (f"{volatility:.4f}:{max_jump:.4f}:{micro_spikes}:{micro_lulls}:{pressure:.2f}")
        if unique_pattern not in self.knowledge_bank and anomaly:
            self.knowledge_bank.add(unique_pattern)

        # Info diagnostyczne
        level = "high" if anomaly else ("hungry" if self.hunger > 3 else "ok")
        info = f"{level.upper()} | vol={volatility:.5f} jump={max_jump:.5f} pres={pressure:.2f} hunger={self.hunger:.2f}"

        if anomaly and (time.time() - self.last_alert_time > 1):
            print(f"[{self.id}] ⚠️ ANOMALIA! {info}")
            self.last_alert_time = time.time()
        elif self.growth_signal:
            print(f"[{self.id}] 🟡 SYGNAŁ ROZWOJU! Hunger={self.hunger:.2f}")

        # Zapis analizy
        result = self._result(volatility, anomaly, max_jump, pressure, micro_spikes, micro_lulls, info, level)
        self.history.append(result)
        if len(self.history) > 1000:
            self.history.pop(0)
        self._auto_log(result)

        # (Opcjonalnie) Synchronizacja do chmury, sieci
        if self.cloud_sync:
            self._sync_cloud(result)

        return result

    def _result(self, volatility, anomaly, max_jump, pressure, micro_spikes, micro_lulls, info, level):
        return {
            "id": self.id,
            "volatility": volatility,
            "anomaly": anomaly,
            "max_jump": max_jump,
            "pressure": pressure,
            "micro_spikes": micro_spikes,
            "micro_lulls": micro_lulls,
            "info": info,
            "hunger": self.hunger,
            "growth_signal": self.growth_signal,
            "timestamp": datetime.now().isoformat(),
            "level": level
        }

    def _auto_log(self, result):
        """Zapisuje bieżący wynik do pliku log."""
        os.makedirs(os.path.dirname(self.auto_log_path), exist_ok=True)
        with open(self.auto_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")

    def clone(self):
        """Klonuje sensor w nowym kontekście."""
        self.clone_count += 1
        new_sensor = copy.deepcopy(self)
        new_sensor.id = f"{self.id}_clone{self.clone_count}"
        print(f"[{self.id}] Klonuję siebie! Nowy sensor: {new_sensor.id}")
        return new_sensor

    def self_tune(self):
        """Samodzielne dostrajanie parametrów (AI-ready)."""
        # Tu możesz podłączyć AI/uczenie ze wzmocnieniem!
        if self.hunger > 6:
            self.base_threshold *= 0.9  # Zwiększ czułość, bo "nudno"
        elif self.hunger < 1:
            self.base_threshold *= 1.05  # Zmniejsz, gdy "przejedzony"
        self.base_threshold = np.clip(self.base_threshold, 0.01, 100)

    def __repr__(self):
        return f"<SuperNoiseSensor id={self.id} hunger={self.hunger:.2f} buffer={len(self.buffer)}/{self.window} adaptive_threshold={self.adaptive_threshold:.4f}>"

    def _sync_cloud(self, result):
        """Miejsce na wysyłanie do chmury/rozproszonej bazy."""
        # Tu możesz dodać kod np. do Firebase, AWS, GDrive itp.
        pass

# Przykład użycia
if __name__ == "__main__":
    sensor = SuperNoiseSensor()
    # Symulowany test
    for i in range(300):
        price = 100 + np.random.normal(0, 0.3)
        tick = {'price': price, 'volume': np.random.randint(1,10), 'spread': 0.1 * np.random.rand()}
        sensor.read(tick)
        if sensor.growth_signal:
            new_sensor = sensor.clone()
            break
import numpy as np

class NoiseSensor:
    def activate(self):
        print("[NoiseSensor] Sensor szumu aktywowany")
    def mutate(self):
        print("[NoiseSensor] Przetwarzanie mutacyjne szumu")
    def evaluate(self, test_data):
        import numpy as np
        return np.mean(test_data)  # Przykład: średni poziom szumu

