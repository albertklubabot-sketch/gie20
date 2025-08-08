import numpy as np
import time
import copy
import threading
import json
import os
from datetime import datetime
from core.base_sensor import BaseSensor

class SuperVolumeSensor:
    def __init__(
        self,
        window=120,
        base_volume=1.0,
        learning_rate=0.12,
        sensor_id=None,
        auto_log_path="data/volume_super_history.log",
        cloud_sync=False
    ):
        self.window = window
        self.base_volume = base_volume
        self.adaptive_volume = base_volume
        self.learning_rate = learning_rate
        self.buffer = []
        self.history = []
        self.cloud_sync = cloud_sync
        self.id = sensor_id or f"SuperVolume_{int(time.time() * 1000)}"
        self.clone_count = 0
        self.last_alert_time = 0
        self.auto_log_path = auto_log_path
        self.hunger = 0
        self.growth_signal = False
        self.knowledge_bank = set()

    def read(self, tick_data):
        if not tick_data or "volume" not in tick_data:
            return self._result(0, False, 0, 0, "Brak tick_data", level="low")

        volume = tick_data['volume']
        price = tick_data.get('price', 0.0)
        spread = tick_data.get('spread', 0.0)
        timestamp = tick_data.get('time', time.time())
        meta = tick_data.get('meta', None)

        self.buffer.append({'volume': volume, 'price': price, 'spread': spread, 'time': timestamp})
        if len(self.buffer) > self.window:
            self.buffer.pop(0)

        volumes = np.array([b['volume'] for b in self.buffer])
        mean_volume = np.mean(volumes)
        std_volume = np.std(volumes)
        max_volume = np.max(volumes)
        min_volume = np.min(volumes)
        range_volume = max_volume - min_volume

        recent_vol = np.std(volumes[-min(10, len(volumes)):]) if len(volumes) > 10 else std_volume
        self.adaptive_volume = self.base_volume + self.learning_rate * (recent_vol + self.hunger)

        anomaly = volume > (self.adaptive_volume * 2) or volume < (self.adaptive_volume * 0.5)
        micro_spikes = np.sum(np.abs(volumes - mean_volume) > self.adaptive_volume)
        volume_trend = np.polyfit(np.arange(len(volumes)), volumes, 1)[0] if len(volumes) > 5 else 0.0

        if anomaly:
            self.hunger = max(0, self.hunger - 1)
        else:
            self.hunger += 0.11
        self.growth_signal = self.hunger > 5.5

        unique_pattern = f"{mean_volume:.4f}:{std_volume:.4f}:{max_volume:.4f}:{min_volume:.4f}:{micro_spikes}"
        if unique_pattern not in self.knowledge_bank and anomaly:
            self.knowledge_bank.add(unique_pattern)

        level = "high" if anomaly else ("hungry" if self.hunger > 3.5 else "ok")
        info = f"{level.upper()} | vol={volume:.2f} µ={mean_volume:.2f} σ={std_volume:.2f} spikes={micro_spikes} hunger={self.hunger:.2f}"

        if anomaly and (time.time() - self.last_alert_time > 1):
            print(f"[{self.id}] ⚡ ANOMALIA! {info}")
            self.last_alert_time = time.time()
        elif self.growth_signal:
            print(f"[{self.id}] 🔺 SYGNAŁ ROZWOJU! Hunger={self.hunger:.2f}")

        result = self._result(mean_volume, anomaly, std_volume, volume_trend, info, level)
        self.history.append(result)
        if len(self.history) > 1200:
            self.history.pop(0)
        self._auto_log(result)

        if self.cloud_sync:
            self._sync_cloud(result)

        return result

    def _result(self, mean_volume, anomaly, std_volume, volume_trend, info, level):
        return {
            "id": self.id,
            "mean_volume": mean_volume,
            "anomaly": anomaly,
            "std_volume": std_volume,
            "volume_trend": volume_trend,
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
        if self.hunger > 6:
            self.base_volume *= 0.93
        elif self.hunger < 1:
            self.base_volume *= 1.05
        self.base_volume = np.clip(self.base_volume, 0.01, 10_000)

    def __repr__(self):
        return f"<SuperVolumeSensor id={self.id} hunger={self.hunger:.2f} buffer={len(self.buffer)}/{self.window} adaptive_volume={self.adaptive_volume:.2f}>"

    def _sync_cloud(self, result):
        # (Tu można dodać wymianę przez chmurę, API, GIE-hive itp.)
        pass

if __name__ == "__main__":
    sensor = SuperVolumeSensor()
    # Test – symulacja działania
    for i in range(240):
        volume = abs(np.random.normal(1.2, 0.25)) * (1 + 0.15 * np.sin(i/10))
        tick = {'volume': volume, 'price': 101.5, 'spread': 0.03}
        sensor.read(tick)
        if sensor.growth_signal:
            new_sensor = sensor.clone()
            break
import numpy as np

class VolumeSensor:
    def activate(self):
        print("[VolumeSensor] Sensor wolumenu aktywowany")

    def mutate(self):
        print("[VolumeSensor] Przetwarzanie mutacyjne wolumenu")

    def evaluate(self, test_data):
        return np.std(test_data)  # Przykład: zmienność wolumenu
