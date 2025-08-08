import os
import json
import random
import time
import datetime
import MetaTrader5 as mt5

from utils.logger import Logger
from utils.meta_logger import MetaLogger
from core.base_engine import BaseEngine
from core.meta_reflection import MetaReflection
from core.gie_manifest import gie_manifest
from core.sensors.sag_sensor import SuperAggressiveSensor

class AgresywnyEngine(BaseEngine):
    def __init__(self, symbol="EURUSD", lot=0.04, memory_file="agresywny_memory.json", sensors=None):
        super().__init__(name="Agresywny", symbol=symbol, lot=lot, sensors=sensors)
        self.memory_file = memory_file
        self.own_memory = []
        self.happy_points = 0
        self.sad_points = 0
        self.hunger = 1.0
        self.curiosity = 0.7
        self.reward_bias = 1.0
        self.last_sensors = {}
        self.main_position = None
        self.meta_reflector = MetaReflection()
        self.meta_logger = MetaLogger()
        self.last_result = None
        self.profit_threshold = 1.5
        self.loss_threshold = -1.0
        self.log("Engine initialized.")
        self.load_memory()

    def log(self, msg):
        print(f"[AgresywnyEngine][{time.strftime('%H:%M:%S')}] {msg}")

    def add_happy_point(self, reason=""):
        self.happy_points += 1
        self.log(f"😃 Szczęśliwy tick! (happy_points: {self.happy_points}) Powód: {reason}")
        if self.happy_points % 10 == 0:
            self.log("🔥 Osiągnąłem kolejny poziom szczęścia!")
            self.hunger = min(self.hunger + 0.05, 1.5)

    def add_sad_point(self, reason=""):
        self.sad_points += 1
        self.log(f"☹️ Smutny tick! (sad_points: {self.sad_points}) Powód: {reason}")
        if self.sad_points > 5:
            self.curiosity = min(self.curiosity + 0.1, 1.5)
            self.hunger = max(self.hunger - 0.1, 0.5)
            self.log("🤔 Zmieniam strategię! Więcej ciekawości, mniej szaleństwa.")
            if self.sad_points % 10 == 0:
                self.reward_bias = max(self.reward_bias - 0.05, 0.7)

    def should_close_position(self, position, profit_threshold=None, loss_threshold=None):
        profit_thr = profit_threshold if profit_threshold is not None else self.profit_threshold
        loss_thr = loss_threshold if loss_threshold is not None else self.loss_threshold
        if hasattr(position, 'profit'):
            if position.profit >= profit_thr:
                self.log_emotion(f"Czas na zamknięcie ZYSKU: {position.profit}", positive=True)
                return True
            if position.profit <= loss_thr:
                self.log_emotion(f"Czas na zamknięcie STRATY: {position.profit}", positive=False)
                return True
        return False

    def tick(self):
        # 1. Zamykanie pozycji
        positions = mt5.positions_get(symbol=self.symbol)
        if positions:
            for position in positions:
                if self.should_close_position(position):
                    self.close_trade(position)
                    if hasattr(position, 'profit') and position.profit > 0:
                        self.add_happy_point("Zysk na zamknięciu pozycji!")
                    else:
                        self.add_sad_point("Strata na zamknięciu pozycji.")

        # 2. Decyzja o otwarciu pozycji
        open_decision = False
        if random.random() < self.hunger:
            open_decision = True
        elif random.random() < self.curiosity:
            open_decision = True

        if open_decision:
            direction = random.choice(["buy", "sell"])
            result = self.open_trade(direction)
            if result:
                self.add_happy_point(f"Otwarcie pozycji {direction}")
            else:
                self.add_sad_point(f"Błąd przy otwarciu {direction}")
        else:
            self.log("Dziś odpoczywam... 😎")

        # 3. Samonagradzanie i adaptacja po ticku
        if self.happy_points and self.happy_points % 15 == 0:
            self.log("🥇 MAX szczęścia! Podbijam apetyt!")
            self.hunger = min(self.hunger + 0.05, 2.0)
        if self.sad_points and self.sad_points % 7 == 0:
            self.log("😡 Frustracja! Reset głodu na bezpieczny poziom!")
            self.hunger = 1.0
            self.curiosity += 0.05

        # 4. Meta-refleksja (co 5 ticków)
        if len(self.own_memory) > 0 and len(self.own_memory) % 5 == 0:
            meta_summary = self.meta_reflector.analyze(self.own_memory)
            self.log(f"[META] Wnioski meta-refleksji: {meta_summary}")

        # 5. Zapis wszystkiego
        self.save_memory()
        self.save_happy_points()
        self.save_log()

    def load_memory(self):
        if os.path.isfile(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    self.own_memory = json.load(f)
                self.log("Pamięć wczytana.")
            except Exception as e:
                self.log(f"Nie udało się wczytać pamięci: {e}")
        else:
            self.own_memory = []
            self.log("Brak wcześniejszej pamięci, czysta karta.")

    def save_memory(self):
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.own_memory, f, ensure_ascii=False, indent=2)
            self.log("Pamięć zapisana.")
        except Exception as e:
            self.log(f"Nie udało się zapisać pamięci: {e}")

    def save_happy_points(self):
        try:
            with open("agresywny_happy.json", "w", encoding="utf-8") as f:
                json.dump({"happy_points": self.happy_points}, f, ensure_ascii=False, indent=2)
            self.log("Szczęście zapisane.")
        except Exception as e:
            self.log(f"[Happy][ERROR] Nie można zapisać szczęścia: {e}")

    def log_emotion(self, msg, positive=True):
        emotion = "😃 [ZADOWOLONY]" if positive else "😞 [SMUTNY]"
        self.log(f"{emotion} {msg}")

    def open_trade(self, direction, custom_lot=None):
        lot = custom_lot if custom_lot else self.lot
        if lot < 0.04:
            lot = 0.04  # Minimalny lot zgodny z RoboForex ECN demo

        tick = mt5.symbol_info_tick(self.symbol)
        price = tick.ask if direction == "buy" else tick.bid

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": lot,
            "type": mt5.ORDER_TYPE_BUY if direction == "buy" else mt5.ORDER_TYPE_SELL,
            "price": price,
            "deviation": 10,
            "magic": 123456,
            "comment": "AgresywnyEngine",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        self.log(f"Otwieram pozycję {direction.upper()} {lot} {self.symbol} | Result: {result}")

        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            self.own_memory.append({
                'action': direction,
                'result': 'open',
                'profit': 0,
                'ts': time.time(),
                'sensors': self.last_sensors
            })
            self.main_position = direction
            return True
        else:
            self.log(f"[ERROR] Kod błędu: {getattr(result, 'retcode', 'brak')}")
            self.own_memory.append({
                'action': direction,
                'result': 'fail',
                'profit': 0,
                'ts': time.time(),
                'sensors': self.last_sensors
            })
            return False

    def close_trade(self, position):
        tick = mt5.symbol_info_tick(self.symbol)
        price = tick.bid if position.type == mt5.ORDER_TYPE_BUY else tick.ask
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": position.volume,
            "type": mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
            "price": price,
            "deviation": 10,
            "magic": 123456,
            "comment": "AgresywnyEngine CLOSE",
            "position": position.ticket,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        self.log(f"Zamykam pozycję (ticket {position.ticket}) | Result: {result}")
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            self.own_memory.append({
                'action': 'close',
                'result': 'open',
                'profit': position.profit,
                'ts': time.time(),
                'sensors': self.last_sensors
            })
            return True
        else:
            self.own_memory.append({
                'action': 'close',
                'result': 'fail',
                'profit': position.profit,
                'ts': time.time(),
                'sensors': self.last_sensors
            })
            return False

    def get_fake_sensor_readings(self):
        return {
            "pressure": random.uniform(-1, 1),
            "volume": random.uniform(0, 1),
            "noise": random.uniform(0, 1)
        }

    def save_log(self, filename="agresywny_log.json"):
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.own_memory, f, ensure_ascii=False, indent=2)
            self.log(f"Log zapisany do pliku {filename}")
        except Exception as e:
            self.log(f"[Happy][ERROR] Nie udało się zapisać logu: {e}")

    def load_log(self, filename="agresywny_log.json"):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                self.own_memory = json.load(f)
            self.log(f"Log wczytany z pliku {filename}")
        except Exception as e:
            self.log(f"[Happy][ERROR] Nie udało się wczytać logu: {e}")

    def run_autonomous_cycle(self, cycles=10, delay=10, meta_interval=5):
        for i in range(cycles):
            print(f"\nCYCLE {i+1}:")
            self.tick()
            self.save_memory()
            self.save_happy_points()
            self.save_log()

            if (i+1) % meta_interval == 0:
                print(f"\n[META] Analiza meta-refleksyjna po {i+1} cyklach...")
                meta_summary = self.meta_reflector.analyze(self.own_memory)
                print(f"[META] Wynik analizy: {meta_summary}")
                self.log(f"[META] {meta_summary}")

            time.sleep(delay)
        print("[GIE] Zakończono autonomiczny cykl.")

if __name__ == "__main__":
    print("[INIT] Startuję GIE AgresywnyEngine")
    sag_sensor = SuperAggressiveSensor(window=120, hunger=1.2)
    engine = AgresywnyEngine(
        symbol="EURUSD",
        lot=0.04,
        sensors={"SuperAggressiveSensor": sag_sensor}
    )
    engine.load_memory()
    engine.run_autonomous_cycle(cycles=10, delay=10, meta_interval=5)
    engine.load_log()
    print("[GIE] Praca zakończona.")

