# core/engines/refleksyjny.py

import logging
import random
from datetime import datetime

from core.base_engine import BaseEngine
from core.meta_reflection import MetaReflection
from core.gie_manifest import gie_manifest

from utils.logger import Logger             # klasyczny logger systemowy
from utils.meta_logger import MetaLogger    # meta-logger (dla zaawansowanej analizy)

class RefleksyjnyEngine(BaseEngine):
    """
    Silnik Refleksyjny GIE 2.0.
    Decyzje na bazie wielopoziomowej analizy, samorefleksji i uczenia się na własnych działaniach.
    Integruje się z meta_reflection, gie_manifest, sensorycznym środowiskiem i systemem nagród.
    """

    def __init__(self, gie_id, manifest=gie_manifest, meta_reflector: MetaReflection = None, logger: Logger = None, metalogger: MetaLogger = None):
        self.gie_id = gie_id
        self.manifest = manifest
        self.meta_reflector = meta_reflector or MetaReflection()
        self.logger = logger or Logger("data/logs", log_name="refleksyjny.log")
        self.metalogger = metalogger or MetaLogger()
        self.performance_history = []
        self.reward = 0.0
        self.reflection_depth = 3   # Jak głęboko analizuje własne decyzje
        self.curiosity = 0.5        # Motywator eksploracji nowych ścieżek
        self.last_decision = None

    def decide(self, sensory_data, market_context, engine_votes=None):
        """
        Główna funkcja podejmowania decyzji.

        sensory_data: dict  # aktualne dane ze wszystkich sensorów
        market_context: dict  # kluczowe dane rynkowe (np. tick, czas, stan rynku)
        engine_votes: dict  # decyzje pozostałych silników
        """
        # 1. Analiza kontekstu sensorycznego i rynkowego
        reflection_insight = self.meta_reflector.analyze(sensory_data, market_context, engine_votes, depth=self.reflection_depth)

        # 2. Porównanie z historycznymi decyzjami i nagrodami
        optimal_action = self._select_action(reflection_insight, engine_votes)

        # 3. Uczenie się na feedbacku
        self._update_performance(optimal_action, market_context)

        # 4. Logowanie decyzji
        self._log_decision(optimal_action, sensory_data, market_context, engine_votes)

        # 5. Aktualizacja "głodu sukcesu" i ciekawości
        self._adjust_motivation()

        self.last_decision = optimal_action
        return optimal_action

    def _select_action(self, insight, engine_votes):
        """
        Analiza insightów z meta-reflektora, głosów innych silników i własnych statystyk.
        Decyzja jest kompromisem między bezpieczeństwem a eksploracją.
        """
        # Przykład: wybierz najczęściej proponowaną przez inne silniki akcję, ale czasem eksperymentuj
        if engine_votes:
            actions = list(engine_votes.values())
            dominant_action = max(set(actions), key=actions.count)
        else:
            dominant_action = insight.get('suggested_action', 'hold')

        # Refleksyjność: czy ostatnie podobne decyzje były skuteczne?
        if self.performance_history and random.random() < self.curiosity:
            last_perf = self.performance_history[-1]
            if last_perf['action'] == dominant_action and last_perf['reward'] < 0:
                # Ostatnia decyzja była zła – zmień strategie
                alt_action = insight.get('alternative_action', 'hold')
                return alt_action

        # Eksploracja: czasem wybierz nową akcję
        if random.random() < self.curiosity:
            return insight.get('exploratory_action', dominant_action)

        return dominant_action

    def _update_performance(self, self_action, market_context):
        """
        Uczenie się na skuteczności decyzji – analizuje wynik i zapisuje performance.
        """
        # Przykładowo: reward = zmiana wartości portfela po akcji (to zależy od Twojego systemu)
        reward = self.meta_reflector.evaluate_action_performance(self.gie_id, self_action, market_context)
        self.performance_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": self_action,
            "reward": reward
        })
        self.reward = reward

    def _log_decision(self, action, sensory_data, market_context, engine_votes):
        """
        Zaawansowane logowanie decyzji dla analizy meta-poziomu.
        """
        log_entry = {
            "gie_id": self.gie_id,
            "engine": "Refleksyjny",
            "timestamp": datetime.utcnow().isoformat(),
            "sensory_data": sensory_data,
            "market_context": market_context,
            "action": action,
            "engine_votes": engine_votes,
            "reward_so_far": self.reward
        }
        self.logger.log(log_entry)

    def _adjust_motivation(self):
        """
        Dynamiczne dostosowanie poziomu ciekawości i 'głodu sukcesu'.
        """
        # Prosty mechanizm nagradzania/kary
        if len(self.performance_history) > 3:
            last_rewards = [h["reward"] for h in self.performance_history[-3:]]
            avg_reward = sum(last_rewards) / 3
            if avg_reward < 0:
                self.curiosity = min(1.0, self.curiosity + 0.05)  # Gdy jest źle, szukaj nowych rozwiązań
            else:
                self.curiosity = max(0.05, self.curiosity - 0.02)  # Gdy działa, bądź mniej ryzykowny

    def reflect(self):
        """
        Wywołanie głębokiej autonalizy (meta-refleksja) – np. do cyklicznego uczenia się, debugowania.
        """
        summary = self.meta_reflector.deep_reflection(self.gie_id, self.performance_history)
        self.logger.log({"gie_id": self.gie_id, "engine": "Refleksyjny", "meta_reflection": summary})
        return summary

    def clone(self):
        """
        Zwraca nową instancję silnika refleksyjnego do użycia przez gie_clone.py.
        """
        return RefleksyjnyEngine(
            gie_id=self.gie_id,
            manifest=self.manifest,
            meta_reflector=self.meta_reflector,
            logger=self.logger
        )

class RefleksyjnyEngine:
    def run(self):
        print("[RefleksyjnyEngine] Tryb refleksyjny aktywowany")

    def evolve(self):
        print("[RefleksyjnyEngine] Ewolucja refleksyjna")

    def evaluate(self, test_data):
        return min(test_data)  # Przykład: refleksja na podstawie minimalnej wartości
