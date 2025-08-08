import numpy as np
from scipy.stats import entropy
from core.base_sensor import BaseSensor
from utils.logger import get_logger
import time

class SuperAggressiveSensor(BaseSensor):
    """
    Superinteligentny sensor gie do zastosowań agresywnych i refleksyjnych.
    Analizuje mikroimpulsy, presję, rytm rynkowy, sygnatury energetyczne.
    Nowość: logowanie triggerów, numeracja anomaly_id, burst/vol clustering.
    Kompatybilny z wszystkimi silnikami gie.
    """

    def __init__(self, window: int = 100, hunger: float = 1.0, cooldown_period: float = 4.0):
        super().__init__()
        self.window = window
        self.hunger = hunger
        self.cooldown_period = cooldown_period
        self.logger = get_logger("SuperSensor")
        self.buffer = []
        self.anomaly_count = 0
        self.high_pressure_events = 0
        self.last_trade_time = 0
        self.anomaly_id = 0  # unikalna numeracja sygnałów
        self.logger.info("SuperAggressiveSensor initialized (window=%d, hunger=%.2f)", self.window, self.hunger)

    def read(self, tick_data: dict) -> dict:
        """
        Przyjmuje ticka, aktualizuje rolling window i przekazuje do analizy.
        tick_data: {
            'price': float,
            'spread': float,
            'timestamp': float
        }
        """
        price = tick_data.get('price')
        spread = tick_data.get('spread', 0.0)
        timestamp = tick_data.get('timestamp', time.time())

        if price is None or timestamp is None:
            self.logger.warning("❌ Nieprawidłowy tick (brak price/timestamp)")
            return {}

        self.buffer.append((timestamp, price, spread))
        if len(self.buffer) > self.window:
            self.buffer.pop(0)

        prices = np.array([p for t, p, s in self.buffer])
        spreads = np.array([s for t, p, s in self.buffer])
        times = np.array([t for t, p, s in self.buffer])

        if len(prices) >= 2:
            returns = np.diff(prices)
            volatility = np.std(returns)
        else:
            returns = np.array([])
            volatility = 0.0

        self.logger.debug("📥 Tick: %.5f | spread=%.5f | vol=%.4f | buffer=%d",
                          price, spread, volatility, len(self.buffer))

        return self._analyze_tick(timestamp, prices, spreads, times, returns, volatility)

    def _analyze_tick(self, timestamp, prices, spreads, times, returns, volatility) -> dict:
        # Podstawowe cechy rynku
        spread_diff = np.diff(spreads)
        spread_accel = np.mean(np.abs(np.diff(spread_diff[-5:]))) if len(spread_diff) > 5 else 0

        direction_entropy = 0
        if len(returns) > 1:
            direction_series = np.sign(returns)
            _, counts = np.unique(direction_series, return_counts=True)
            direction_entropy = entropy(counts) if len(counts) > 1 else 0

        momentum_flips = np.sum(np.diff(np.sign(returns)) != 0) if len(returns) > 2 else 0
        energy_signature = float(np.abs(np.fft.fft(returns[-32:])).sum()) if len(returns) >= 32 else 0.0

        spread_jump = spreads[-1] - spreads[-2] if len(spreads) > 2 else 0
        pressure_level = float(np.abs(spread_jump) > 0.05)

        anomaly = float(volatility > 0.01 and pressure_level > 0 and direction_entropy > 0.5)
        if anomaly:
            self.anomaly_count += 1
        if pressure_level:
            self.high_pressure_events += 1

        duration = times[-1] - times[0] if len(times) > 1 else 1.0
        anomaly_rate = self.anomaly_count / duration

        time_since_last = timestamp - self.last_trade_time
        actionable = time_since_last > self.cooldown_period
        if anomaly and actionable:
            self.last_trade_time = timestamp

        growth_signal = self.anomaly_count > 3 and energy_signature > 0.1

        # Micro burst trade cluster: >=3 ticki w <0.3 sek (ostatnie 5 ticków)
        burst_threshold = 0.3
        recent_times = times[-5:] if len(times) >= 5 else times
        burst_cluster = False
        if len(recent_times) >= 3:
            cluster_gaps = np.diff(recent_times)
            burst_cluster = np.sum(cluster_gaps < burst_threshold) >= 2
            
        # Volatility clustering: >=3 spike'i w oknie 5s
        cluster_window = 5.0
        recent_idx = np.where(times > (timestamp - cluster_window))[0]
        recent_returns = returns[recent_idx - 1] if len(recent_idx) > 1 else np.array([])
        spike_threshold = 2.0 * np.std(returns) if len(returns) > 0 else 0.0
        vol_cluster = False
        if len(recent_returns) > 0 and spike_threshold > 0:
            vol_cluster = np.sum(np.abs(recent_returns) > spike_threshold) >= 3

        # Advanced trigger logging z numeracją, timestampem, listą triggerów
        trigger = []
        if anomaly: trigger.append("anomaly")
        if burst_cluster: trigger.append("burst")
        if vol_cluster: trigger.append("vol_cluster")
        timestamp_readable = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        if trigger:
            self.anomaly_id += 1
            self.logger.info(
                "[%s] SIGNAL #%d: %s | vol=%.4f ent=%.3f pres=%.3f burst=%s volclust=%s energy=%.3f price=%.5f",
                timestamp_readable, self.anomaly_id, ",".join(trigger),
                volatility, direction_entropy, pressure_level, burst_cluster, vol_cluster, energy_signature, prices[-1]
            )

        return {
            "volatility": volatility,
            "pressure_level": pressure_level,
            "anomaly": anomaly,
            "growth_signal": growth_signal,
            "hunger": self.hunger,
            "momentum_flips": momentum_flips,
            "direction_entropy": direction_entropy,
            "spread_accel": spread_accel,
            "energy_signature": energy_signature,
            "anomaly_rate": anomaly_rate,
            "actionable": actionable,
            "burst_cluster": burst_cluster,
            "vol_cluster": vol_cluster
        }

    def reset(self):
        """Resetuje stan sensora (bufor, statystyki, timery, numerację sygnałów)"""
        self.buffer.clear()
        self.anomaly_count = 0
        self.high_pressure_events = 0
        self.last_trade_time = 0
        self.anomaly_id = 0
        self.logger.info("🔄 Sensor zresetowany")

    def __str__(self):
        return "SuperAggressiveSensor"
