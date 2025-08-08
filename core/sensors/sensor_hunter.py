import importlib
import os
import traceback
import logging
import time
import random
from core.base_sensor import BaseSensor

class SensorHunter:
    def __init__(self, sensors_folder="sensors/"):
        self.sensors_folder = sensors_folder
        self.sensors = []
        self.sensor_stats = {}
        self.logfile = "data/sensor_stats.log"
        self.hive = None  # opcjonalnie: referencja do gie_hive, jeśli chcesz podpiąć "rojową" wiedzę

        if not os.path.exists("data"):
            os.makedirs("data")
        self._init_logger()

    def _init_logger(self):
        logging.basicConfig(
            filename=self.logfile,
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s"
        )

    def scan_and_import(self):
        """Automatycznie znajduje i importuje wszystkie sensory z folderu."""
        for fname in os.listdir(self.sensors_folder):
            if fname.endswith('.py') and not fname.startswith('__'):
                module_name = fname[:-3]
                try:
                    module = importlib.import_module(f"sensors.{module_name}")
                    sensor_class = getattr(module, self._guess_sensor_classname(module_name), None)
                    if sensor_class:
                        sensor_instance = sensor_class()
                        if self.evaluate_sensor(sensor_instance):
                            self.sensors.append(sensor_instance)
                            self._log(f"Sensor {module_name} imported & accepted.")
                        else:
                            self._log(f"Sensor {module_name} imported but rejected (score too low).")
                    else:
                        self._log(f"Sensor class not found in module {module_name}.")
                except Exception as e:
                    self._log(f"Failed to import {module_name}: {e}\n{traceback.format_exc()}")

    def _guess_sensor_classname(self, module_name):
        # Zgodnie z konwencją: noise_sensor.py => NoiseSensor, volume_sensor.py => VolumeSensor
        parts = module_name.split('_')
        return ''.join(word.capitalize() for word in parts) + "Sensor"

    def evaluate_sensor(self, sensor):
        """Ocenia sensor na podstawie syntetycznych/testowych danych i zwraca True jeśli wart podpięcia."""
        try:
            test_data = self._generate_test_data()
            score = sensor.evaluate(test_data)
            self.sensor_stats[sensor.__class__.__name__] = score
            self._log(f"Sensor {sensor.__class__.__name__} scored {score:.3f} in evaluation.")
            # Próg możesz łatwo zmienić/dynamicznie adaptować
            return score >= 0.6
        except Exception as e:
            self._log(f"Sensor {sensor.__class__.__name__} evaluation error: {e}\n{traceback.format_exc()}")
            return False

    def _generate_test_data(self):
        # Tu możesz rozbudować generator testów, lub pobierać realne sample z gie_mind/market_data_manager
        return [random.uniform(0, 1) for _ in range(128)]

    def auto_improve_sensors(self):
        """Wyklucza sensory ze słabym score, loguje i zgłasza do roju."""
        for sensor in list(self.sensors):
            name = sensor.__class__.__name__
            score = self.sensor_stats.get(name, 0)
            if score < 0.5:
                self._log(f"Sensor {name} flagged for removal/upgrade (score={score:.3f})")
                self.sensors.remove(sensor)
                # Tutaj możesz podpiąć kod do auto-migracji/klonowania nowego sensora

    def report_to_hive(self):
        """Jeśli podłączono gie_hive, raportuje statystyki roju."""
        if self.hive:
            try:
                self.hive.update_sensor_stats(self.sensor_stats)
                self._log("Sensor stats reported to hive.")
            except Exception as e:
                self._log(f"Failed to report stats to hive: {e}")

    def _log(self, msg):
        print(msg)
        logging.info(msg)

    def run(self, with_hive=False):
        self.scan_and_import()
        self.auto_improve_sensors()
        if with_hive:
            self.report_to_hive()

    def reload_sensors(self):
        """Pozwala na dynamiczny reload sensorów (np. po aktualizacji kodu) bez restartu całej AI."""
        self.sensors.clear()
        self.scan_and_import()

    def evaluate_and_add(self, sensor):
        """Dla ręcznego dodania sensora z oceną (np. z zewnętrznego źródła/hive)."""
        if self.evaluate_sensor(sensor):
            self.sensors.append(sensor)
            self._log(f"Sensor {sensor.__class__.__name__} manually added after evaluation.")

# Uwaga! Sensory muszą implementować metodę .evaluate(test_data)
# Przykład:
#
# class NoiseSensor:
#     def evaluate(self, test_data):
#         # logika testowania skuteczności
#         return np.mean(test_data)  # przykładowy score

class SensorHunter:
    def activate(self):
        print("[SensorHunter] Sensor łowcy aktywowany")

    def mutate(self):
        print("[SensorHunter] Przetwarzanie mutacyjne łowcy")

    def evaluate(self, test_data):
        return len(test_data)  # Przykład: długość próbki
