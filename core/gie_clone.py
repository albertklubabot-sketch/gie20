import os
import shutil
import uuid
import datetime
import json
import random

from .gie_mind import GieMind
from .gie_hive import GieHive
from .meta_reflection import MetaReflection
from .hunter_tools import HunterTools
from core.gie_manifest import gie_manifest

# Folder na klony i logi zawsze względny do tego pliku!
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data"))
CLONE_DIR = os.path.join(DATA_DIR, "clones")

STRATEGY_PROFILES = [
    "explorer", "conservative", "aggressive", "arbitrageur", "defender", "innovator"
]

class GieClone:
    """
    Superinteligentny klonator – rozmnaża, testuje, ewoluuje, selekcjonuje i rejestruje klony GIE.
    Każdy klon posiada własną pamięć, ID, log, parametry, status, profil strategii, reputację oraz meta-cele.
    """

    def __init__(self, parent_id, hunger_level, strategy_profile=None, manifest=None, hive=None):
        self.parent_id = parent_id
        self.clone_id = str(uuid.uuid4())
        self.created_at = datetime.datetime.now().isoformat()
        self.hunger_level = hunger_level
        self.status = "created"
        self.performance = None
        self.memory = {}
        self.manifest = manifest or gie_manifest()
        self.hive = hive or GieHive()
        # Log file zawsze do data/clones/
        os.makedirs(CLONE_DIR, exist_ok=True)
        self.log_file = os.path.join(CLONE_DIR, f"{self.clone_id}_log.json")
        self.strategy_profile = strategy_profile or random.choice(STRATEGY_PROFILES)
        self.reputation = 1000  # Startowa reputacja społeczna
        self.reward = 0
        self.penalty = 0
        self.meta_goals = self.init_meta_goals()
        self.clone_dna = self.encode_dna()
        self._log_event("Klon utworzony", extra={"parent_id": parent_id, "profile": self.strategy_profile})

    def _log_event(self, event, extra=None):
        log_entry = {
            "clone_id": self.clone_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "event": event,
            "extra": extra or {}
        }
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    def init_meta_goals(self):
        return [
            {"goal": "explore_new_markets", "progress": 0},
            {"goal": "discover_novel_strategies", "progress": 0},
            {"goal": "optimize_resource_usage", "progress": 0}
        ]

    def encode_dna(self):
        return {
            "profile": self.strategy_profile,
            "parent_id": self.parent_id,
            "created_at": self.created_at,
            "hunger": self.hunger_level
        }

    def clone_self(self, gie_mind_cfg=None):
        self._log_event("Rozpoczynam proces klonowania")
        partner_profile = self.strategy_profile
        if self.hive and hasattr(self.hive, "get_top_clone_profile"):
            partner_profile = self.hive.get_top_clone_profile()
        new_profile = self.cross_or_mutate_strategy(partner_profile)
        new_clone = GieClone(
            parent_id=self.clone_id,
            hunger_level=max(1, self.hunger_level - 1),
            strategy_profile=new_profile,
            manifest=self.manifest.clone(),
            hive=self.hive
        )
        new_clone.memory = self.memory.copy()
        if gie_mind_cfg:
            new_clone.memory['gie_mind_cfg'] = gie_mind_cfg
        self.register_clone(new_clone)
        self._log_event("Klon utworzony", extra={"clone_id": new_clone.clone_id, "profile": new_profile})
        return new_clone

    def cross_or_mutate_strategy(self, partner_profile):
        if random.random() < 0.5:
            return partner_profile
        else:
            return random.choice(STRATEGY_PROFILES)

    def register_clone(self, clone):
        if self.hive:
            self.hive.register_clone(clone.clone_id, parent_id=clone.parent_id, created_at=clone.created_at, profile=clone.strategy_profile)
            self._log_event("Klon zarejestrowany w Hive", extra={"clone_id": clone.clone_id, "profile": clone.strategy_profile})
        else:
            self._log_event("Brak Hive, rejestracja lokalna", extra={"clone_id": clone.clone_id})

    def test_clone(self, gie_mind_cfg=None):
        self._log_event("Testowanie klona")
        gie_mind = GieMind(config=gie_mind_cfg or self.memory.get('gie_mind_cfg'), strategy_profile=self.strategy_profile)
        performance = gie_mind.simulate_performance()
        self.performance = performance
        self.status = "tested"
        self._log_event("Test zakończony", extra={"performance": performance})
        self.update_reputation(performance)
        return performance

    def update_reputation(self, performance):
        if performance is not None:
            delta = int(performance * 10)
            self.reputation += delta
            if performance < 0:
                self.penalty += abs(delta)
            self._log_event("Aktualizacja reputacji", extra={"reputation": self.reputation})

    def social_learn(self, clones):
        top_clone = max(clones, key=lambda c: c.reputation)
        if top_clone and top_clone.clone_id != self.clone_id:
            if random.random() < 0.5:
                self.memory.update(top_clone.memory)
                self._log_event("Uczenie społeczne od klona", extra={"from": top_clone.clone_id})

    def select_best_clones(self, clone_list, top_n=1):
        sorted_clones = sorted(clone_list, key=lambda x: (x.reputation, x.performance or 0), reverse=True)
        for idx, clone in enumerate(sorted_clones):
            clone._log_event("Selekcja klona", extra={"rank": idx+1})
        return sorted_clones[:top_n]

    def archive_clone(self):
        self.status = "archived"
        archive_dir = os.path.join(CLONE_DIR, "archive")
        os.makedirs(archive_dir, exist_ok=True)
        archive_path = os.path.join(archive_dir, f"{self.clone_id}.json")
        with open(archive_path, "w") as f:
            json.dump(self.__dict__, f, ensure_ascii=False, default=str)
        self._log_event("Klon zarchiwizowany")

    def reward_self(self, reward_value):
        self.reward += reward_value
        self._log_event("Nagroda dla klona", extra={"reward_value": reward_value, "total_reward": self.reward})

    def hunger_check(self, min_hunger=2):
        self._log_event("Sprawdzanie poziomu głodu", extra={"hunger_level": self.hunger_level})
        return self.hunger_level > min_hunger

    def mutate(self, mutation_rate=0.1):
        if random.random() < mutation_rate:
            old_profile = self.strategy_profile
            self.strategy_profile = random.choice(STRATEGY_PROFILES)
            self._log_event("Mutacja profilu strategii", extra={"old": old_profile, "new": self.strategy_profile})
        if "gie_mind_cfg" in self.memory:
            cfg = self.memory["gie_mind_cfg"]
            for key in cfg:
                if isinstance(cfg[key], (int, float)) and random.random() < mutation_rate:
                    old = cfg[key]
                    cfg[key] += random.uniform(-0.1, 0.1) * cfg[key]
                    self._log_event("Mutacja konfiguracji", extra={"param": key, "old": old, "new": cfg[key]})
            self.memory["gie_mind_cfg"] = cfg

    def meta_reflect(self):
        reflection = MetaReflection.reflect_on_clone(self)
        self._log_event("Meta-refleksja", extra={"reflection": reflection})

    def check_opportunity_and_autocloning(self, sensors):
        for sensor in sensors:
            if hasattr(sensor, "detect_opportunity") and sensor.detect_opportunity():
                self._log_event("Szansa wykryta przez sensor", extra={"sensor": str(sensor)})
                return self.clone_self()
        return None

    def optimize_resources(self):
        self._log_event("Optymalizacja zasobów – symulacja")

    def publish_dna(self):
        dna_dir = os.path.join(CLONE_DIR, "dna")
        os.makedirs(dna_dir, exist_ok=True)
        dna_path = os.path.join(dna_dir, f"{self.clone_id}_dna.json")
        with open(dna_path, "w") as f:
            json.dump(self.clone_dna, f, ensure_ascii=False, default=str)
        self._log_event("Zapisano DNA klona", extra={"dna_path": dna_path})

class GieCloneManager:
    def __init__(self):
        self.clones = []

    def create_initial_clone(self, parent_id="ROOT", hunger_level=5):
        clone = GieClone(parent_id=parent_id, hunger_level=hunger_level)
        self.clones.append(clone)
        return clone

    def mass_cloning(self, iterations=3):
        for i in range(iterations):
            new_clones = []
            for clone in self.clones:
                if clone.hunger_check():
                    nowy_klon = clone.clone_self()
                    nowy_klon.mutate()
                    perf = nowy_klon.test_clone()
                    nowy_klon.optimize_resources()
                    nowy_klon.publish_dna()
                    new_clones.append(nowy_klon)
            self.clones.extend(new_clones)
            self.social_learning()
        self.select_and_archive()

    def social_learning(self):
        for clone in self.clones:
            clone.social_learn(self.clones)

    def select_and_archive(self):
        best_clones = self.clones[0].select_best_clones(self.clones, top_n=2)
        for clone in self.clones:
            if clone not in best_clones:
                clone.archive_clone()
        self.clones = best_clones

if __name__ == "__main__":
    manager = GieCloneManager()
    clone = manager.create_initial_clone()
    manager.mass_cloning(iterations=3)
    # Teraz manager.clones zawiera najlepsze, superinteligentne klony GIE!
