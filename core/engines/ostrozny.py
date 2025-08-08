import os
import random
import numpy as np
import datetime

from utils.logger import get_logger
from core.base_engine import BaseEngine
from core.meta_reflection import MetaReflection
from core.gie_manifest import gie_manifest

from core.sensors.noise_sensor import NoiseSensor
from core.sensors.pressure_sensor import PressureSensor
from core.sensors.volume_sensor import VolumeSensor
from core.sensors.sensor_hunter import SensorHunter

class OstroznyEngine(BaseEngine):
    """
    Silnik 'Ostrożny' | wyspecjalizowany w minimalizacji ryzyka, analizie niepewności i zachowaniu kapitału.
    Korzysta z zaawansowanej meta-refleksji, integruje sensory (szum, presja, wolumen), działa autonomicznie i w kolektywie.
    """

    def __init__(self, config=None, hive_api=None, manifest=None):
        super().__init__(name="Ostrozny", config=config)
        self.logger = get_logger("OstroznyEngine")
        self.sensors = {
            "noise": NoiseSensor(),
            "pressure": PressureSensor(),
            "volume": VolumeSensor()
        }
        self.meta_reflection = MetaReflection(self)
        self.hive_api = hive_api
        self.manifest = manifest if manifest else gie_manifest()
        self.risk_aversion = config.get("risk_aversion", 0.8) if config else 0.8
        self.last_action = None
        self.success_history = []
        self.memory = []
        self.curiosity = config.get("curiosity", 0.1) if config else 0.1
        self.hunger = 0.0  # Wewnętrzny stan "głodu" sukcesu (do samoregulacji)

    def sense_market(self, data):
        """
        Odbiera i analizuje dane rynkowe przez sensory.
        """
        sensory_data = {}
        for name, sensor in self.sensors.items():
            sensory_data[name] = sensor.process(data)
        self.logger.debug(f"Sensory data: {sensory_data}")
        return sensory_data

    def decide(self, market_data):
        """
        Główna logika podejmowania decyzji przez silnik ostrożny.
        """
        sensory = self.sense_market(market_data)
        risk_score = self.estimate_risk(sensory)
        opportunity_score = self.estimate_opportunity(sensory)

        # Meta-refleksja: uczenie się na błędach i sukcesach
        self.meta_reflection.reflect(self.memory, self.success_history)

        # Mechanizm ostrożności: priorytet bezpieczeństwa kapitału
        if risk_score > self.risk_aversion:
            action = "hold"
        elif opportunity_score > (1 - self.risk_aversion):
            action = "enter"
        else:
            # Zdarza się, że silnik próbuje nową strategię (ciekawość)
            action = "test" if random.random() < self.curiosity else "wait"

        # Zapisywanie decyzji i refleksja
        self.last_action = action
        self.memory.append({
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "sensory": sensory,
            "risk": risk_score,
            "opportunity": opportunity_score,
            "action": action
        })
        self.logger.info(f"OstroznyEngine decision: {action}, risk: {risk_score}, opp: {opportunity_score}")
        return action

    def estimate_risk(self, sensory):
        """
        Ocena ryzyka bazująca na danych z sensorów i własnej pamięci.
        """
        noise = sensory["noise"]["level"]
        pressure = sensory["pressure"]["level"]
        volume = sensory["volume"]["level"]

        # Prosta heurystyka – można zastąpić modelem RL lub siecią neuronową
        risk = 0.5 * noise + 0.3 * pressure - 0.2 * volume
        risk = np.clip(risk, 0, 1)
        # Uczenie się na podstawie przeszłych błędów
        risk += 0.1 * (1 - np.mean([x.get("success", 1) for x in self.success_history[-5:]])) if self.success_history else 0
        return risk

    def estimate_opportunity(self, sensory):
        """
        Szacowanie okazji rynkowej na podstawie sensorów.
        """
        volume = sensory["volume"]["level"]
        pressure = sensory["pressure"]["level"]
        noise = sensory["noise"]["level"]

        # Prosta heurystyka: duży wolumen, niskie ciśnienie, niski szum = okazja
        opportunity = 0.5 * volume - 0.3 * pressure - 0.2 * noise
        opportunity = np.clip(opportunity, 0, 1)
        return opportunity

    def reward(self, success):
        """
        System nagradzania i karania wpływa na parametry zachowania silnika (np. ostrożność, ciekawość).
        """
        self.success_history.append({"success": success, "timestamp": datetime.datetime.utcnow().isoformat()})
        # Zmiana "głodu" sukcesu
        if success:
            self.hunger = max(0, self.hunger - 0.1)
            self.risk_aversion = min(1.0, self.risk_aversion + 0.01)
        else:
            self.hunger = min(1.0, self.hunger + 0.2)
            self.risk_aversion = max(0.1, self.risk_aversion - 0.05)
            self.curiosity = min(1.0, self.curiosity + 0.05)

    # ---- Klonowanie, synchronizacja, instancjonowanie ----

    def should_clone(self):
        """
        Warunek: klonuj tylko jeśli 'hunger' > 0.9 i ostatnie 3 akcje nie były sukcesem.
        Możesz rozbudować tę logikę wg własnych potrzeb.
        """
        if self.hunger > 0.9 and sum([not x["success"] for x in self.success_history[-3:] if "success" in x]) == 3:
            return True
        return False

    def clone_self(self):
        """
        Tworzy własny klon z bieżącymi parametrami (np. do testów lub do pracy w roju),
        ALE tylko jeśli to niezbędne (wg should_clone()).
        """
        if self.should_clone():
            new_clone = OstroznyEngine(config={
                "risk_aversion": self.risk_aversion,
                "curiosity": self.curiosity
            }, hive_api=self.hive_api, manifest=self.manifest)
            self.logger.info("OstroznyEngine cloned itself.")
            return new_clone
        else:
            self.logger.info("Klonowanie nie jest konieczne.")
            return None

    def hive_sync(self):
        """
        Synchronizacja wiedzy z kolektywem GIE Hive.
        """
        if self.hive_api:
            self.hive_api.sync_engine_state(self.name, {
                "risk_aversion": self.risk_aversion,
                "curiosity": self.curiosity,
                "hunger": self.hunger,
                "memory": self.memory[-10:],
            })
            self.logger.info("OstroznyEngine synced state with Hive.")

    # Pozwala na dynamiczne ładowanie jako plugin:
    def get_engine_instance(config=None, hive_api=None, manifest=None):
        return OstroznyEngine(config=config, hive_api=hive_api, manifest=manifest)

# ---- Tryb testowy / plugin ----

class OstroznyEngine:
    def run(self):
        print("[OstroznyEngine] Tryb ostrożny aktywowany")

    def evolve(self):
        print("[OstroznyEngine] Ewolucja ostrożnej strategii")

    def evaluate(self, test_data):
        return sum(test_data) / (len(test_data) + 1)  # Przykład: średnia zachowawcza
