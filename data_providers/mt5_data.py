import MetaTrader5 as mt5
import time
import threading
import traceback
import pandas as pd
import json
import os

from utils.logger import Logger
from core.meta_reflection import MetaReflection
from core.gie_hive import GieHive

# --- Wczytywanie danych dostępowych z pliku JSON ---
secrets_path = os.path.join(os.path.dirname(__file__), "mt5_secrets.json")
with open(secrets_path, "r") as f:
    secrets = json.load(f)

MT5_LOGIN = secrets["MT5_LOGIN"]
MT5_PASSWORD = secrets["MT5_PASSWORD"]
MT5_SERVER = secrets["MT5_SERVER"]
MT5_PATH = secrets.get("MT5_PATH", None)
MT5_SYMBOL = secrets.get("MT5_SYMBOL", None)

class MT5DataProvider:
    def __init__(self, config, sensors=None, hive=None, logger=None):
        self.config = config
        self.symbols = config.get("symbols", ["EURUSD"])
        self.timeframes = config.get("timeframes", ["M1"])
        self.mode = config.get("mode", "demo")
        self.auto_restart = config.get("auto_restart", True)
        self.max_retries = config.get("max_retries", 5)
        self.logger = logger or Logger("MT5DataProvider")
        self.meta_reflection = MetaReflection("MT5DataProvider")
        self.hive = hive or GieHive()
        self.sensors = sensors or []
        self.plugins = []
        self.mt5_initialized = False
        self.initialized = False
        self.running = False

    def add_sensor(self, sensor):
        self.sensors.append(sensor)
        self.logger.info(f"Sensor {sensor.__class__.__name__} added.")

    def add_plugin(self, plugin):
        self.plugins.append(plugin)
        self.logger.info(f"Plugin {plugin.__class__.__name__} loaded.")

    def initialize_mt5(self):
        if not mt5.initialize(login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER, path=MT5_PATH):
            self.logger.error(f"MT5 initialize failed: {mt5.last_error()}")
            return False
        self.mt5_initialized = True
        self.logger.info("MT5 initialized successfully.")
        return True

    def shutdown_mt5(self):
        mt5.shutdown()
        self.mt5_initialized = False
        self.logger.info("MT5 shutdown.")

    def get_ticks(self, symbol, from_time, to_time):
        try:
            ticks = mt5.copy_ticks_range(symbol, from_time, to_time, mt5.COPY_TICKS_ALL)
            df = pd.DataFrame(ticks)
            self.logger.debug(f"Ticks for {symbol}: {len(df)} rows.")
            return df
        except Exception as e:
            self.logger.error(f"Error fetching ticks: {e}")
            return pd.DataFrame()

    def get_rates(self, symbol, timeframe, bars=1000):
        try:
            tf = getattr(mt5, f"TIMEFRAME_{timeframe}", mt5.TIMEFRAME_M1)
            rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)
            df = pd.DataFrame(rates)
            self.logger.debug(f"Rates for {symbol}/{timeframe}: {len(df)} bars.")
            return df
        except Exception as e:
            self.logger.error(f"Error fetching rates: {e}")
            return pd.DataFrame()

    def get_depth(self, symbol):
        try:
            book = mt5.market_book_get(symbol)
            self.logger.debug(f"Market book for {symbol}: {book}")
            return book
        except Exception as e:
            self.logger.error(f"Error fetching market book: {e}")
            return None

    def get_news(self):
        try:
            news = mt5.news_get()
            self.logger.debug(f"Fetched {len(news)} news.")
            return news
        except Exception as e:
            self.logger.error(f"Error fetching news: {e}")
            return []

    def run_data_loop(self, interval=1):
        self.running = True
        retries = 0
        while self.running:
            try:
                if not self.mt5_initialized:
                    self.logger.info("Trying to initialize MT5...")
                    if not self.initialize_mt5():
                        time.sleep(5)
                        continue

                for symbol in self.symbols:
                    for tf in self.timeframes:
                        rates = self.get_rates(symbol, tf)
                        self.process_data(symbol, "TICK", rates)
                        ticks = self.get_ticks(symbol, int(time.time()) - 60, int(time.time()))
                        self.process_data(symbol, "TICKS", ticks)
                        depth = self.get_depth(symbol)
                        self.process_data(symbol, "DEPTH", depth)

                news = self.get_news()
                self.process_data("GLOBAL", "NEWS", news)

                self.hive.update()
                self.meta_reflection.record("MT5 loop success")

                time.sleep(interval)
            except Exception as e:
                self.logger.error(f"MT5 data loop error: {e}\n{traceback.format_exc()}")
                retries += 1
                if self.auto_restart and retries < self.max_retries:
                    self.logger.info("Restarting MT5 loop...")
                    self.shutdown_mt5()
                    time.sleep(2)
                    continue
                else:
                    self.running = False

    def process_data(self, symbol, dtype, data):
        for sensor in self.sensors:
            try:
                sensor.on_data(symbol, dtype, data)
            except Exception as e:
                self.logger.error(f"Sensor {sensor.__class__.__name__} error: {e}")

        # Hive integration
        self.hive.broadcast_data(symbol, dtype, data)

        # Plugins/hooks
        for plugin in self.plugins:
            try:
                plugin.on_data(symbol, dtype, data)
            except Exception as e:
                self.logger.error(f"Plugin {plugin.__class__.__name__} error: {e}")

    def start(self, interval=1):
        self.logger.info("Starting MT5 data provider loop...")
        self.running = True
        t = threading.Thread(target=self.run_data_loop, args=(interval,))
        t.daemon = True
        t.start()

    def stop(self):
        self.logger.info("Stopping MT5 data provider loop...")
        self.running = False
        self.shutdown_mt5()

# # Przykład użycia w gie_main.py lub innej głównej pętli GIE:
# from data_providers.mt5_data import MT5DataProvider
# from sensors.volume_sensor import VolumeSensor
# from core.base_engine import BaseEngine

# mt5_config = {...} # Załaduj z pliku lub dict
# mt5_provider = MT5DataProvider(mt5_config)
# mt5_provider.add_sensor(VolumeSensor())
# mt5_provider.add_plugin(BaseEngine())
# mt5_provider.start(interval=5)
