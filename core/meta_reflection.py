import pickle
import datetime
import random
import numpy as np
import os

class MetaReflection:
    def __init__(self, memory_path=None):
        # Ścieżka zawsze względem pliku, automatycznie twórz folder data!
        if memory_path is None:
            base_dir = os.path.dirname(__file__)
            data_dir = os.path.join(base_dir, "..", "data")
            data_dir = os.path.abspath(data_dir)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            memory_path = os.path.join(data_dir, "gie_memory.pkl")
        self.memory_path = memory_path
        self.memory = self.load_memory()
        self.knowledge = {}  # meta-wiedza (sukcesy silników w kontekście)
        self.adaptivity = 0.5  # plastyczność uczenia
        self.curiosity = 0.5   # motywacja do eksperymentów
        self.hunger = 0.5      # "głód" nowych rozwiązań
        self.meta_reward = 0.0 # meta-nagroda dla rozwoju
        self.last_expansion = None  # kiedy ostatnio rozbudowano

    def load_memory(self):
        try:
            with open(self.memory_path, "rb") as f:
                return pickle.load(f)
        except (FileNotFoundError, EOFError):
            return []

    def save_memory(self):
        # Upewnij się, że folder na pewno istnieje (gdyby był usunięty)
        dir_path = os.path.dirname(self.memory_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        with open(self.memory_path, "wb") as f:
            pickle.dump(self.memory, f)

    def log_event(self, state, action, result, engine, emotions):
        event = {
            "timestamp": datetime.datetime.now().isoformat(),
            "state": state,
            "action": action,
            "result": result,
            "engine": engine,
            "emotions": emotions
        }
        self.memory.append(event)
        self.save_memory()

    def update(self, history):
        """Zaawansowana analiza historyczna decyzji GIE (meta-korelacje)"""
        correlations = {}
        for record in history[-100:]:  # analizuj do 100 ostatnich kroków
            env = record.get("env", {})
            engine = record.get("engine", None)
            noise = round(env.get("noise", 0), 1)
            pressure = round(env.get("pressure", 0), 1)
            volume = round(env.get("volume", 0), 1)
            key = (engine, noise, pressure, volume)
            win = 1 if record.get("score", 0) else 0
            if key not in correlations:
                correlations[key] = {"win": 0, "trials": 0}
            correlations[key]["win"] += win
            correlations[key]["trials"] += 1
        # Adaptacyjne uczenie meta-wiedzy (mieszanie z poprzednią wiedzą)
        for k, v in correlations.items():
            if k in self.knowledge:
                prev = self.knowledge[k]
                prev_trials = prev["trials"] + v["trials"]
                prev_win = prev["win"] + v["win"]
                self.knowledge[k] = {
                    "win": int(prev_win * self.adaptivity + v["win"] * (1 - self.adaptivity)),
                    "trials": int(prev_trials * self.adaptivity + v["trials"] * (1 - self.adaptivity))
                }
            else:
                self.knowledge[k] = v
        self.save_memory()

    def suggest(self, env):
        """Podpowiedz najlepszy silnik wg meta-wiedzy, czasem eksploruje dla uczenia."""
        noise = round(env.get("noise", 0), 1)
        pressure = round(env.get("pressure", 0), 1)
        volume = round(env.get("volume", 0), 1)
        candidates = []
        for (engine, n, p, v), stats in self.knowledge.items():
            if abs(n - noise) <= 0.2 and abs(p - pressure) <= 0.2 and abs(v - volume) <= 0.2:
                if stats["trials"] > 3:
                    eff = stats["win"] / max(1, stats["trials"])
                    candidates.append((eff, engine))
        if candidates:
            # Eksploracja: czasem losowo dla meta-uczenia!
            if random.random() < self.curiosity:
                return random.choice(candidates)[1]
            else:
                return max(candidates, key=lambda x: x[0])[1]
        return None

    def reflect(self, last_n=100):
        """Prosta refleksja: analiza skuteczności i emocji"""
        if len(self.memory) < last_n:
            return None
        successes = sum(1 for e in self.memory[-last_n:] if e["result"])
        fails = last_n - successes
        avg_greed = sum(e["emotions"].get("greed", 0) for e in self.memory[-last_n:]) / last_n
        # Automatyczna adaptacja ciekawości/głodu/meta-nagrody
        if successes / last_n < 0.5:
            self.curiosity = min(1.0, self.curiosity + 0.05)
            self.hunger = min(1.0, self.hunger + 0.05)
        else:
            self.curiosity = max(0.1, self.curiosity - 0.05)
            self.hunger = max(0.1, self.hunger - 0.05)
        # Meta-nagroda: wzrost skuteczności
        self.meta_reward = (successes / last_n) + avg_greed
        return {
            "success_rate": successes / last_n,
            "fail_rate": fails / last_n,
            "avg_greed": avg_greed,
            "curiosity": self.curiosity,
            "hunger": self.hunger,
            "meta_reward": self.meta_reward
        }

    # --- SUPERMETA KOD: SAMOROZWÓJ, KOLONOWANIE, HUNTER-TOOLS, HIVE ---
    def evolve(self, engine_manager, sensor_manager, hunter_tools, hive=None):
        """
        Meta-proces: automatyczna ewolucja, klonowanie, polowanie na nowe strategie i sensory,
        kolektywna wymiana meta-wiedzy (hive).
        """
        # Rozpoznanie stagnacji/wysokiego głodu = potrzeba innowacji
        if len(self.memory) < 200:
            return
        meta = self.reflect(last_n=100)
        if not meta:
            return
        # Wysoki głód lub niska skuteczność = czas na ekspansję!
        if meta["meta_reward"] < 0.6 or self.hunger > 0.7:
            # 1. Skorzystaj z hunter_tools – szukaj i klonuj nowe silniki/strategie
            new_engines = hunter_tools.find_new_engines()
            for eng in new_engines:
                if not engine_manager.has_engine(eng.name):
                    engine_manager.add_engine(eng)
                    self.log_event(
                        state="evolve",
                        action=f"add_engine_{eng.name}",
                        result="engine_added",
                        engine=eng.name,
                        emotions={"curiosity": self.curiosity, "hunger": self.hunger}
                    )
            # 2. Sensory: dynamicznie rozbudowuj, jeśli znajdziesz coś nowego
            new_sensors = hunter_tools.find_new_sensors()
            for sens in new_sensors:
                if not sensor_manager.has_sensor(sens.name):
                    sensor_manager.add_sensor(sens)
                    self.log_event(
                        state="evolve",
                        action=f"add_sensor_{sens.name}",
                        result="sensor_added",
                        engine="meta_reflection",
                        emotions={"curiosity": self.curiosity, "hunger": self.hunger}
                    )
            self.last_expansion = datetime.datetime.now().isoformat()
        # 3. Współdzielenie meta-wiedzy przez hive (roju GIE)
        if hive:
            # Wyślij swoją meta-wiedzę do innych, pobierz od nich i zintegruj
            remote_knowledge = hive.share_meta_knowledge(self.knowledge)
            self.merge_knowledge(remote_knowledge)
            self.log_event(
                state="hive_sync",
                action="merge_knowledge",
                result="hive_merge",
                engine="hive",
                emotions={"curiosity": self.curiosity, "hunger": self.hunger}
            )

    def merge_knowledge(self, remote_knowledge):
        """Inteligentna fuzja meta-wiedzy z innych instancji"""
        for k, v in remote_knowledge.items():
            if k in self.knowledge:
                prev = self.knowledge[k]
                trials = prev["trials"] + v["trials"]
                win = prev["win"] + v["win"]
                self.knowledge[k] = {
                    "win": int(win * 0.5 + prev["win"] * 0.5),
                    "trials": int(trials * 0.5 + prev["trials"] * 0.5)
                }
            else:
                self.knowledge[k] = v
        self.save_memory()

    # --- DYNAMICZNY SUPERKOD ---
    def meta_loop(self, engine_manager, sensor_manager, hunter_tools, hive=None):
        """Główny loop meta-rozwoju GIE 2.0 – wywołuj cyklicznie z gie_mind lub gie_main."""
        self.update(self.memory)
        self.evolve(engine_manager, sensor_manager, hunter_tools, hive)

class MetaAnalytics:
    def __init__(self):
        self.history = []
        self.benchmarks = {'SP500': [], 'BTCUSD': [], 'Custom': []}
        self.unique_data_sources = set()
        self.last_report = None

    def log_trade(self, pnl, timestamp, strategy, data_sources):
        self.history.append({'pnl': pnl, 'timestamp': timestamp, 'strategy': strategy})
        self.unique_data_sources.update(data_sources)
    
    def add_benchmark(self, name, value):
        self.benchmarks.setdefault(name, []).append(value)
    
    def calculate_success_rate(self):
        gains = [x['pnl'] for x in self.history if x['pnl'] > 0]
        losses = [abs(x['pnl']) for x in self.history if x['pnl'] < 0]
        if not losses:
            return 1.0
        return (sum(gains) - sum(losses)) / (sum(losses) + 1e-6)

    def edge_detect(self, min_edge=0.01):
        # Sprawdź czy zysk jest powyżej benchmarków i czy GIE nadal ma przewagę
        success = self.calculate_success_rate()
        custom_benchmark = np.mean(self.benchmarks['Custom']) if self.benchmarks['Custom'] else 0
        edge = success - custom_benchmark
        return edge > min_edge

    def generate_report(self):
        # Pełny raport w formie słownika (lub JSON)
        report = {
            'total_trades': len(self.history),
            'success_rate': self.calculate_success_rate(),
            'unique_data_sources': len(self.unique_data_sources),
            'last_trades': self.history[-5:] if len(self.history) > 5 else self.history,
            'benchmarks': {k: np.mean(v) if v else 0 for k, v in self.benchmarks.items()},
            'timestamp': datetime.datetime.now().isoformat()
        }
        self.last_report = report
        return report
