import random
import copy
import importlib
import os

class StrategyEvolver:
    """
    Ultra-adaptacyjny moduł ewolucji silników GIE 2.0
    Funkcje:
    - Mutacja, krzyżowanie, klonowanie, adaptacja i meta-refleksja
    - Dynamiczne importowanie nowych silników z folderu 'engines'
    - Integracja z meta_reflection, hive, hunter i sensorycznym feedbackiem
    """

    def __init__(
        self,
        engines,
        stats,
        meta_reflection=None,
        hunger_sensor=None,
        hive=None,
        hunter=None,
        engines_dir="engines"
    ):
        self.engines = engines
        self.stats = stats
        self.meta_reflection = meta_reflection
        self.hunger_sensor = hunger_sensor
        self.hive = hive
        self.hunter = hunter
        self.engines_dir = engines_dir

    def get_weakest(self, n=1):
        """Wybiera n najsłabszych silników według skuteczności i głodu"""
        hunger = self.hunger_sensor() if self.hunger_sensor else 1.0
        scored = {
            k: (self.stats[k]['win'] / max(1, self.stats[k]['trials']) - 0.1 * hunger)
            for k in self.stats
        }
        weakest = sorted(scored, key=scored.get)[:n]
        return weakest

    def evolve(self, n=1, methods=("mutate", "crossover", "clone")):
        """Ewoluuje silniki na wiele sposobów"""
        weakest_keys = self.get_weakest(n=n)
        for key in weakest_keys:
            engine = self.engines[key]
            mutated = False

            # --- Mutacja
            if "mutate" in methods and hasattr(engine, "mutate"):
                print(f"[GIE-EVOLVER] Mutuję silnik: {key}")
                new_engine = engine.mutate()
                mutated = True

            # --- Krzyżowanie
            elif "crossover" in methods and hasattr(engine, "crossover"):
                partner_key = random.choice([k for k in self.engines if k != key])
                partner = self.engines[partner_key]
                print(f"[GIE-EVOLVER] Krzyżuję {key} z {partner_key}")
                new_engine = engine.crossover(partner)
                mutated = True

            # --- Klonowanie (backup/adaptacja)
            elif "clone" in methods:
                print(f"[GIE-EVOLVER] Klonuję silnik: {key}")
                new_engine = copy.deepcopy(engine)
                mutated = True

            else:
                print(f"[GIE-EVOLVER] Silnik {key} nie obsługuje mutacji/krzyżowania/klonowania!")
                continue

            # --- Dynamiczne nazewnictwo i rejestracja
            new_key = f"{key}_{random.randint(1000,9999)}"
            self.engines[new_key] = new_engine
            self.stats[new_key] = {'win': 0, 'trials': 0}
            print(f"[GIE-EVOLVER] Nowy silnik: {new_key}")

            # --- Meta-refleksja i historia mutacji
            if self.meta_reflection:
                self.meta_reflection.log_mutation(parent=key, child=new_key, method="evolve")

            # --- Integracja z hive (wymiana wiedzy)
            if self.hive and hasattr(self.hive, "broadcast_engine"):
                self.hive.broadcast_engine(new_key, new_engine)

            # --- Integracja z hunter (testowanie nowych źródeł)
            if self.hunter and hasattr(self.hunter, "evaluate_engine"):
                hunter_score = self.hunter.evaluate_engine(new_engine)
                print(f"[GIE-EVOLVER] Hunter ocenił nowy silnik ({new_key}): {hunter_score}")

    def dynamic_import_new_engines(self):
        """Automatycznie ładuje nowe silniki z katalogu 'engines/' (Python hot-plug!)"""
        loaded = []
        for fname in os.listdir(self.engines_dir):
            if fname.endswith(".py") and not fname.startswith("_"):
                modulename = fname[:-3]
                try:
                    module = importlib.import_module(f"{self.engines_dir}.{modulename}")
                    for attr in dir(module):
                        klass = getattr(module, attr)
                        if isinstance(klass, type):
                            key = f"{attr}_{random.randint(10000,99999)}"
                            self.engines[key] = klass()
                            self.stats[key] = {'win': 0, 'trials': 0}
                            loaded.append(key)
                            print(f"[GIE-EVOLVER] Załadowano nowy silnik: {key} ({attr})")
                except Exception as e:
                    print(f"[GIE-EVOLVER] Błąd ładowania {modulename}: {e}")
        return loaded

    def cleanup(self, keep_best_n=8):
        """Usuwa słabe silniki, zostawia tylko najlepsze N"""
        sorted_keys = sorted(
            self.stats,
            key=lambda k: self.stats[k]['win'] / max(1, self.stats[k]['trials']),
            reverse=True
        )
        to_remove = [k for k in self.engines if k not in sorted_keys[:keep_best_n]]
        for k in to_remove:
            print(f"[GIE-EVOLVER] Usuwam słaby silnik: {k}")
            del self.engines[k]
            del self.stats[k]

    def full_cycle(self):
        """Pełny cykl: importuj nowe silniki, ewoluuj, wyczyść stare"""
        print("[GIE-EVOLVER] Dynamiczny import nowych silników...")
        self.dynamic_import_new_engines()
        print("[GIE-EVOLVER] Rozpoczynam ewolucję...")
        self.evolve(n=2, methods=("mutate", "crossover", "clone"))
        print("[GIE-EVOLVER] Czyszczenie stada silników...")
        self.cleanup(keep_best_n=10)
        print("[GIE-EVOLVER] Cykl ewolucji zakończony.")

# --- Przykład użycia (dostosuj pod swój system!):
# from core.strategy_evolver import StrategyEvolver
# evolver = StrategyEvolver(
#     engines=your_engines,
#     stats=your_stats,
#     meta_reflection=meta_reflection_instance,
#     hunger_sensor=hunger_sensor_instance,
#     hive=gie_hive_instance,
#     hunter=hunter_tools_instance,
#     engines_dir="engines"
# )
# evolver.full_cycle()
