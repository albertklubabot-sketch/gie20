# core/meta_master.py

import os
import importlib
import time
import traceback

class MetaMaster:
    def __init__(self, core_path='core', engines_path='engines', sensors_path='sensors', data_path='data', hive_enabled=True):
        self.core_path = core_path
        self.engines_path = engines_path
        self.sensors_path = sensors_path
        self.data_path = data_path
        self.hive_enabled = hive_enabled

        self.history = []
        self.gie_hunger = 0
        self.success_streak = 0
        self.meta_mood = "curious"
        self.max_hunger = 10  # po ilu cyklach głód wymusza ewolucję

        self.load_all_modules()

    def log(self, msg):
        print(f"[MetaMaster] {msg}")
        self.history.append((time.time(), msg))

    def load_all_modules(self):
        self.engines = self.dynamic_load(self.engines_path)
        self.sensors = self.dynamic_load(self.sensors_path)
        self.log(f"Loaded {len(self.engines)} engines and {len(self.sensors)} sensors.")

    def dynamic_load(self, folder):
        modules = {}
        for fname in os.listdir(folder):
            if fname.endswith('.py') and not fname.startswith('__'):
                mname = fname[:-3]
                try:
                    modules[mname] = importlib.import_module(f"{folder}.{mname}")
                except Exception as e:
                    self.log(f"Failed to load {folder}.{mname}: {e}")
        return modules

    def analyze_structure(self):
        # Meta-analityka: wykrywanie braków, dziur, zduplikowanych lub przestarzałych strategii/sensorów
        missing = []
        for folder in [self.engines_path, self.sensors_path]:
            if not os.path.exists(folder):
                missing.append(folder)
            elif len(os.listdir(folder)) == 0:
                missing.append(f"{folder} is empty")
        if missing:
            self.log(f"Found missing or empty modules: {missing}")
        return missing

    def check_performance_and_evolve(self):
        # Analizuje sukcesy/porazki, wyzwala „głód”, klonowanie, ewolucję
        profit = self.get_latest_profit()
        if profit < 0:
            self.gie_hunger += 1
            self.success_streak = 0
            self.meta_mood = "hungry"
            self.log(f"Gie is hungry! Hunger level: {self.gie_hunger}")
        else:
            self.success_streak += 1
            self.gie_hunger = 0
            self.meta_mood = "satisfied"

        if self.gie_hunger >= self.max_hunger:
            self.log("Hunger threshold exceeded – launching evolution cycle!")
            self.evolve_engines_and_sensors()
            self.gie_hunger = 0

    def get_latest_profit(self):
        # Analiza zysków – pobiera z plików/data/ itp. (przykład – do adaptacji pod Twój log profitów)
        profit_log = os.path.join(self.data_path, "profit.log")
        if os.path.exists(profit_log):
            with open(profit_log) as f:
                lines = f.readlines()
                if lines:
                    last = lines[-1].strip()
                    try:
                        return float(last)
                    except:
                        return 0
        return 0

    def evolve_engines_and_sensors(self):
        # Tworzy nowe strategie, klonuje, modyfikuje, integruje nowe sensory, uruchamia hunterów!
        self.log(">> Running meta-evolution: cloning engines, seeking new strategies...")
        # Przykład: klonowanie najlepszego silnika
        if self.engines:
            best_engine_name = max(self.engines, key=lambda e: self.mock_engine_performance(e))
            new_engine_name = f"{best_engine_name}_clone_{int(time.time())}"
            self.clone_engine(best_engine_name, new_engine_name)
            self.log(f"Cloned engine: {best_engine_name} → {new_engine_name}")
        # Przykład: szukanie nowych sensorów
        self.run_hunter_tools()

    def mock_engine_performance(self, engine_name):
        # Tu wstaw analizę skuteczności engine (docelowo: realna metryka)
        return hash(engine_name) % 100

    def clone_engine(self, src, dst):
        src_file = os.path.join(self.engines_path, f"{src}.py")
        dst_file = os.path.join(self.engines_path, f"{dst}.py")
        if os.path.exists(src_file):
            with open(src_file) as f:
                code = f.read()
            code = code.replace(src, dst)
            with open(dst_file, "w") as f:
                f.write(code)
        else:
            self.log(f"Cannot clone: {src_file} does not exist.")

    def run_hunter_tools(self):
        # Integracja hunter_tools (np. szukanie nowych strategii w repo, sieci)
        try:
            from utils import hunter_tools
            hunter_tools.run()
            self.log("Hunter tools executed for new data/strategies.")
        except Exception as e:
            self.log(f"Hunter tools unavailable or failed: {e}")

    def meta_reflect_and_rewrite(self):
        # Analiza i ewentualne przepisywanie kodu engines/sensors na bazie meta-wzorów!
        self.log("Meta-reflection: Analyzing own code and seeking improvements...")
        # ... rozbuduj wg potrzeb, na razie placeholder

    def run(self, cycles=100):
        self.log("MetaMaster is alive and running!")
        for i in range(cycles):
            try:
                self.analyze_structure()
                self.check_performance_and_evolve()
                self.meta_reflect_and_rewrite()
                if self.hive_enabled:
                    self.exchange_knowledge()
                time.sleep(2)
            except Exception as e:
                self.log(f"Exception in MetaMaster cycle: {e}\n{traceback.format_exc()}")

    def exchange_knowledge(self):
        # Współpraca i nauka kolektywna (placeholder)
        self.log("Exchanging knowledge with the hive... (not yet implemented)")

if __name__ == "__main__":
    meta_master = MetaMaster()
    meta_master.run()
