# core/gie_hive.py

import os
import importlib

from core.gie_mind import GieMind
from utils.logger import Logger

class GieHive:
    """
    Zarządza wieloma instancjami Gie (klony, agenty, inteligencja rozproszona).
    Autonomiczne klonowanie, meta-refleksja, dynamiczne pluginy.
    """
    def __init__(self, market_data_manager, n_agents=3):
        # Folder na logi zawsze względem pliku!
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
        os.makedirs(data_dir, exist_ok=True)
        self.logger = Logger(path=os.path.join(data_dir, "gie_hive_log.txt"))
        self.market_data_manager = market_data_manager

        self.agents = [
            GieMind(
                market_data_manager,
                Logger(path=os.path.join(data_dir, f"gie_log_{i+1}.txt"))
            )
            for i in range(n_agents)
        ]
        self.sensors = self.load_plugins('sensors')
        self.engines = self.load_plugins('engines')

    def load_plugins(self, folder):
        # Ładowanie pluginów z podfolderu względem pliku
        plugins = {}
        folder_path = os.path.join(os.path.dirname(__file__), "..", folder)
        folder_path = os.path.abspath(folder_path)
        if not os.path.isdir(folder_path):
            self.logger.log(f"[ERROR] Folder pluginów nie istnieje: {folder_path}")
            return plugins

        for filename in os.listdir(folder_path):
            if filename.endswith('.py') and not filename.startswith('_'):
                modulename = filename[:-3]
                try:
                    module = importlib.import_module(f"core.{folder}.{modulename}")
                    plugins[modulename] = module
                except Exception as e:
                    self.logger.log(f"[ERROR] Nie udało się załadować pluginu {modulename} z {folder}: {e}")
        self.logger.log(f"Załadowano pluginy z {folder}: {list(plugins.keys())}")
        return plugins

    def run_all(self, n_cycles=100):
        self.logger.log(f"Startuje kolonię Gie. Liczba agentów: {len(self.agents)}")
        for cycle in range(n_cycles):
            self.logger.log(f"--- Cykl {cycle+1} ---")
            for idx, agent in enumerate(self.agents):
                self.logger.log_event(f"Agent #{idx+1}", "Rozpoczynam cykl")
                agent.act()
            self.meta_reflection()

    def add_agent(self):
        i = len(self.agents) + 1
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
        agent = GieMind(self.market_data_manager, Logger(path=os.path.join(data_dir, f"gie_log_{i}.txt")))
        self.agents.append(agent)
        self.logger.log_event("NOWY KLON", f"Dodano agenta #{i}")

    def remove_agent(self, idx):
        if 0 <= idx < len(self.agents):
            self.logger.log_event("USUNIĘCIE", f"Usuwam agenta #{idx+1}")
            del self.agents[idx]

    def share_knowledge(self):
        self.logger.log_event("DZIELENIE WIEDZY", "Synchronizuję wiedzę i strategie między agentami")
        base_hunger = sum(a.hunger for a in self.agents) / len(self.agents)
        base_satisfaction = sum(getattr(a, "satisfaction", 0) for a in self.agents) / len(self.agents)
        for agent in self.agents:
            agent.hunger = (agent.hunger + base_hunger) / 2
            if hasattr(agent, "satisfaction"):
                agent.satisfaction = (agent.satisfaction + base_satisfaction) / 2
        # Dodatkowo: wymiana najlepszych strategii i meta-parametrów

    def meta_reflection(self):
        performances = [agent.get_performance_metric() for agent in self.agents]
        best_idx = performances.index(max(performances))
        worst_idx = performances.index(min(performances))
        self.logger.log(f"Najlepszy agent: #{best_idx+1}, Najsłabszy agent: #{worst_idx+1}")
        # Klonuj najlepszego, ew. usuń najsłabszego jeśli jest ich dużo
        if len(self.agents) < 20:
            self.clone_agent(best_idx)
        if len(self.agents) > 5:
            self.remove_agent(worst_idx)
        self.share_knowledge()

    def clone_agent(self, idx):
        agent = self.agents[idx]
        new_agent = agent.clone()
        self.agents.append(new_agent)
        self.logger.log_event("META_KLON", f"Skopiowano agenta #{idx+1}")

    def scan_for_new_plugins(self):
        self.sensors.update(self.load_plugins('sensors'))
        self.engines.update(self.load_plugins('engines'))

# Można dodać regularne wywołania scan_for_new_plugins() w run_all()
