# utils/meta_logger.py
import os
import re
import json
import logging
from datetime import datetime, timedelta


class MetaLogger:
    """
    Metalogger analizuje logi GIE, wykrywa trendy, anomalia, auto-feedback, alarmy i nagrody.
    To warstwa refleksyjna AI — automatycznie reaguje na sukcesy/porażki.
    """

    def __init__(self, log_path="data/logs/gie.log", meta_log_path="data/logs/meta.log"):
        self.log_path = log_path
        self.meta_log_path = meta_log_path
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        os.makedirs(os.path.dirname(meta_log_path), exist_ok=True)
        self._setup_logger()

    def _setup_logger(self):
        self.logger = logging.getLogger("GIE_META_LOGGER")
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

        fh = logging.FileHandler(self.log_path, encoding="utf-8")
        fh.setFormatter(formatter)

        if not self.logger.handlers:
            self.logger.addHandler(fh)

    # INTERFEJS DO LOGOWANIA
    def debug(self, message: str):
        self.logger.debug(message)

    def info(self, message: str):
        self.logger.info(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str):
        self.logger.error(message)

    def critical(self, message: str):
        self.logger.critical(message)

    # FUNKCJE META
    def parse_logs(self, since_minutes=60):
        if not os.path.exists(self.log_path):
            return []
        logs = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f.readlines():
                logs.append(line.strip())
        now = datetime.now()
        filtered_logs = []
        for entry in logs:
            try:
                tstr = entry.split(" ")[0] + " " + entry.split(" ")[1]
                t = datetime.strptime(tstr, "%Y-%m-%d %H:%M:%S,%f")
                if now - t < timedelta(minutes=since_minutes):
                    filtered_logs.append(entry)
            except:
                continue
        return filtered_logs

    def analyze(self, logs=None):
        if logs is None:
            logs = self.parse_logs()
        stats = {
            "INFO": 0,
            "WARNING": 0,
            "ERROR": 0,
            "EVENTS": {},
            "METRICS": {},
        }
        for entry in logs:
            if "ERROR" in entry:
                stats["ERROR"] += 1
            if "WARNING" in entry:
                stats["WARNING"] += 1
            if "INFO" in entry:
                stats["INFO"] += 1

            m = re.search(r"EVENT::(\w+)\s\|\sDATA:(.+)", entry)
            if m:
                event = m.group(1)
                stats["EVENTS"][event] = stats["EVENTS"].get(event, 0) + 1

            m2 = re.search(r"METRIC::(\w+)=(-?\d+(\.\d+)?)", entry)
            if m2:
                name = m2.group(1)
                val = float(m2.group(2))
                stats["METRICS"][name] = stats["METRICS"].get(name, []) + [val]
        return stats

    def meta_reflect(self, stats):
        actions = []
        if "profit" in stats["METRICS"]:
            mean_profit = sum(stats["METRICS"]["profit"]) / len(stats["METRICS"]["profit"])
            if mean_profit > 0:
                actions.append(f"REWARD: Mean profit positive: {mean_profit:.2f}")
            else:
                actions.append("PENALTY: Negative mean profit")
        self.write_meta_log(actions)
        return actions

    def write_meta_log(self, actions):
        with open(self.meta_log_path, "a", encoding="utf-8") as f:
            for act in actions:
                f.write(f"{datetime.now()} META_ACTION::{act}\n")

    def auto_action(self):
        logs = self.parse_logs()
        stats = self.analyze(logs)
        actions = self.meta_reflect(stats)
        return actions


# --------------------------
# DODATKOWY JSONL LOGGER (równoległy)
class MetaLoggerJSON:
    def __init__(self, logfile="data/meta_log.jsonl"):
        self.logfile = logfile
        os.makedirs(os.path.dirname(logfile), exist_ok=True)

    def log(self, entry):
        with open(self.logfile, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def log_decision(self, decision, result, meta_info):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "decision": decision,
            "result": result,
            "meta": meta_info,
        }
        self.log(entry)
