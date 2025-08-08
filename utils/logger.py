# utils/logger.py – Kompletny, spójny Logger dla GIE20

import logging
import os
from datetime import datetime

class Logger:
    """
    Podstawowy logger GIE – szybki, czytelny, uniwersalny.
    Loguje zdarzenia, błędy, metryki, statusy systemowe.
    """

    def __init__(self, log_dir="data/logs", log_name="gie.log", level=logging.INFO):
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, log_name)
        self.logger = logging.getLogger("GIE_Logger")
        self.logger.setLevel(level)
        fh = logging.FileHandler(log_path)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        fh.setFormatter(formatter)
        if not self.logger.hasHandlers():
            self.logger.addHandler(fh)

    def log(self, message, level=logging.INFO):
        if level == logging.DEBUG:
            self.logger.debug(message)
        elif level == logging.WARNING:
            self.logger.warning(message)
        elif level == logging.ERROR:
            self.logger.error(message)
        else:
            self.logger.info(message)

    def log_event(self, event_type, data):
        msg = f"EVENT:{event_type} | DATA:{data}"
        self.logger.info(msg)

    def log_error(self, error_msg):
        self.logger.error(f"ERROR:{error_msg}")

    def log_metric(self, name, value):
        self.logger.info(f"METRIC:{name}={value}")

# Uniwersalna funkcja get_logger() – do użycia w całym projekcie
def get_logger(name="GIE20", level=logging.INFO, log_dir="data/logs"):
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        # Log do pliku (każda instancja osobno)
        log_path = os.path.join(log_dir, f"{name.lower()}_{datetime.now().strftime('%Y%m%d')}.log")
        fh = logging.FileHandler(log_path)
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        # Log na konsolę
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger

# Przykład użycia (usuń komentarz, jeśli chcesz przetestować standalone)
# logger = Logger()
# logger.log("System initialized", logging.INFO)
# logger.log_event("sensor_update", {"sensor":"Noise", "value":12.3})
# logger.log_error("Błąd przykładowy")
# logger.log_metric("profit", 123.45)

# test_logger = get_logger("GIE20")
# test_logger.info("Test komunikatu na konsolę i do pliku")
