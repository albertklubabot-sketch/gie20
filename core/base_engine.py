import os
import sys
import importlib
import uuid
import random
import datetime
from typing import Dict, Any, Callable

# Dynamiczne, odporne na błędy ścieżki (nie używaj .., wszystko lokalnie!)
PLUGIN_FOLDER = os.path.join(os.path.dirname(__file__), "plugins")
if not os.path.isdir(PLUGIN_FOLDER):
    print(f"[ERROR] Folder pluginów nie istnieje: {PLUGIN_FOLDER}")

STRATEGY_FOLDER = os.path.join(os.path.dirname(__file__), "engines")
if not os.path.isdir(STRATEGY_FOLDER):
    print(f"[ERROR] Folder strategii nie istnieje: {STRATEGY_FOLDER}")

class Plugin:
    def __init__(self, engine, config=None):
        self.engine = engine
        self.config = config or {}

    def on_decision(self, environment, decision):
        pass

    def on_reward(self, reward, info):
        pass

    def on_reflect(self):
        pass

class BaseEngine:
    def __init__(self, name=None, symbol=None, lot=None, sensors=None, hive=None, config=None, **kwargs):
        self.id = str(uuid.uuid4())
        self.name = name or self.__class__.__name__
        self.symbol = symbol
        self.lot = lot
        self.sensors = sensors if sensors is not None else []
        self.hive = hive
        self.config = config or {}

        self.memory = []
        self.state = {}
        self.last_action = None
        self.reward = 0.0
        self.hunger = 0.5
        self.curiosity = 0.5
        self.history = []
        self.clone_count = 0

        self.plugins: Dict[str, Plugin] = {}
        self.loaded_strategies: Dict[str, Callable] = {}
        self.active_strategy: str = None

        self._autoload_plugins()
        self._autoload_strategies()

    # --- Dynamiczne ładowanie pluginów ---
    def _autoload_plugins(self):
        if not os.path.exists(PLUGIN_FOLDER):
            os.makedirs(PLUGIN_FOLDER)
        sys.path.insert(0, PLUGIN_FOLDER)

        for fname in os.listdir(PLUGIN_FOLDER):
            if fname.endswith(".py") and not fname.startswith("_"):
                mname = fname[:-3]
                try:
                    mod = importlib.import_module(mname)
                    if hasattr(mod, "Plugin"):
                        plugin = mod.Plugin(self)
                        self.plugins[mname] = plugin
                        print(f"[BaseEngine] Załadowano plugin: {mname}")
                except Exception as e:
                    print(f"[BaseEngine] Błąd ładowania pluginu {mname}: {e}")

    def use_plugin(self, name, *args, **kwargs):
        plugin = self.plugins.get(name)
        if plugin and hasattr(plugin, "run"):
            return plugin.run(*args, **kwargs)
        raise Exception(f"Plugin '{name}' nie posiada metody run lub nie istnieje.")

    # --- Dynamiczne ładowanie strategii silników ---
    def _autoload_strategies(self):
        sys.path.insert(0, STRATEGY_FOLDER)

        for fname in os.listdir(STRATEGY_FOLDER):
            if fname.endswith(".py") and not fname.startswith("_"):
                mname = fname[:-3]
                try:
                    mod = importlib.import_module(mname)
                    if hasattr(mod, "strategy") and callable(mod.strategy):
                        self.loaded_strategies[mname] = mod.strategy
                        print(f"[BaseEngine] Załadowano strategię: {mname}")
                except Exception as e:
                    print(f"[BaseEngine] Błąd ładowania strategii {mname}: {e}")

    def set_strategy(self, name):
        if name in self.loaded_strategies:
            self.active_strategy = name
            print(f"[BaseEngine] Aktywowano strategię: {name}")
        else:
            raise Exception(f"Strategia {name} nie została załadowana.")

    def decide(self, environment):
        """
        Dynamiczne wywołanie aktywnej strategii albo fallback do NotImplemented.
        """
        if self.active_strategy and self.active_strategy in self.loaded_strategies:
            decision = self.loaded_strategies[self.active_strategy](self, environment)
            for plugin in self.plugins.values():
                plugin.on_decision(environment, decision)
            self.log_decision(decision, environment)
            return decision
        raise NotImplementedError("Brak aktywnej strategii – użyj set_strategy().")

    def receive_feedback(self, reward, info=None):
        self._adjust_motivation(reward)
        for plugin in self.plugins.values():
            plugin.on_reward(reward, info)
        if self.hive:
            self.hive.share_knowledge(self, reward, info)
        self.reward += reward
        self.memory.append({'timestamp': datetime.datetime.now(), 'reward': reward, 'info': info})

    def sense(self, sensors, environment):
        sensor_data = {}
        for sensor in sensors:
            sensor_data[sensor.name] = sensor.read(environment)
        return sensor_data

    def meta_reflect(self):
        if len(self.memory) < 3:
            return
        avg_reward = sum(x['reward'] for x in self.memory[-10:]) / min(10, len(self.memory))
        for plugin in self.plugins.values():
            plugin.on_reflect()
        if avg_reward < 0:
            self.self_improve()

    def self_improve(self):
        self.curiosity = min(1, self.curiosity + random.uniform(-0.1, 0.1))
        self.hunger = min(1, self.hunger + random.uniform(-0.1, 0.1))
        self.clone_count += 1
        print(f"[{self.name}] samodoskonalenie! Klony: {self.clone_count}")

    def _adjust_motivation(self, reward):
        if reward > 0:
            self.hunger = max(0, self.hunger - 0.1)
            self.curiosity = min(1, self.curiosity + 0.05)
        else:
            self.hunger = min(1, self.hunger + 0.05)
            self.curiosity = max(0, self.curiosity - 0.05)

    def clone(self):
        clone = self.__class__(name=self.name + "_clone", hive=self.hive, config=self.config.copy())
        clone.state = self.state.copy()
        clone.history = list(self.history)
        clone.curiosity = self.curiosity
        clone.hunger = self.hunger
        return clone

    def log_decision(self, decision, environment, reward=None):
        entry = {
            'timestamp': datetime.datetime.now(),
            'decision': decision,
            'env': environment,
            'reward': reward
        }
        self.history.append(entry)

    def communicate(self, message, recipient=None):
        if self.hive:
            self.hive.broadcast(message, sender=self, recipient=recipient)

    def run(self):
        print("[BaseEngine] Bazowy silnik aktywowany")

    def evolve(self):
        print("[BaseEngine] Ewolucja bazowej strategii")

    def evaluate(self, test_data):
        return sum(test_data)  # Przykład: bazowe podejście
