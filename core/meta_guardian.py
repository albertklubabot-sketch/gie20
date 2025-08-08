import time
import json
import os
import traceback

class MetaGuardian:
    def __init__(self, gie_system, config_path='./config/meta_guardian.json'):
        self.gie_system = gie_system
        self.config = self.load_config(config_path)
        self.meta_log = []
        self.last_snapshot = None

    def load_config(self, config_path):
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        # fallback domyślny:
        return {
            "max_drawdown": 0.2,
            "max_open_trades": 20,
            "max_grid_size": 7,
            "min_equity_margin": 0.25,
            "snapshot_dir": "./data/snapshots",
            "logfile": "./data/meta_guardian.log",
            "alert_email": "",
            "meta_tune": True,
            "monitor_cycle_sec": 60
        }

    def monitor_all(self):
        try:
            self.log("Rozpoczęto meta-monitoring...")
            self.check_drawdown()
            self.check_open_trades()
            self.check_grid_risk()
            self.check_equity_margin()
            self.predict_risk()
            self.meta_reflection()
            self.save_snapshot()
        except Exception as e:
            self.log(f"[ALERT] Błąd w meta_guardian: {e}\n{traceback.format_exc()}")

    def check_drawdown(self):
        capital = self.gie_system.get_total_capital()
        equity = self.gie_system.get_equity()
        dd = (capital - equity) / capital
        if dd > self.config["max_drawdown"]:
            self.log(f"[DRAWDOWN] Przekroczony limit straty! DD={dd:.2%}")
            self.handle_drawdown(dd)

    def check_open_trades(self):
        open_trades = self.gie_system.get_open_trades()
        if len(open_trades) > self.config["max_open_trades"]:
            self.log(f"[TRADE LIMIT] Za dużo pozycji otwartych: {len(open_trades)}")
            self.handle_overtrading(len(open_trades))

    def check_grid_risk(self):
        for grid in self.gie_system.get_open_grids():
            if len(grid['positions']) > self.config["max_grid_size"]:
                self.log(f"[GRID] Grid przekracza limit! {len(grid['positions'])} pozycji.")
                self.handle_grid_overload(grid)

    def check_equity_margin(self):
        margin_level = self.gie_system.get_margin_level()
        if margin_level < self.config["min_equity_margin"]:
            self.log(f"[MARGIN] Poziom margin zagrożony! {margin_level:.2%}")
            self.handle_margin_risk(margin_level)

    def predict_risk(self):
        # Przykład: analizuj trendy, rozpoznawaj "runaway trend" (ML/model heurystyczny, simple moving avg)
        for grid in self.gie_system.get_open_grids():
            predicted = self.gie_system.predict_trend(grid)
            if predicted.get('risk_of_runaway'):
                self.log(f"[PREDICT] Wysokie ryzyko długiego trendu: {predicted}")
                self.handle_predicted_trend_risk(grid, predicted)

    def handle_drawdown(self, dd):
        # Możesz zamykać część stratnych pozycji, wysłać alarm, ograniczyć ekspozycję
        self.gie_system.reduce_exposure(target_dd=self.config["max_drawdown"])

    def handle_overtrading(self, n):
        # Zatrzymaj otwieranie nowych pozycji, zamknij najmniej rentowne
        self.gie_system.limit_open_trades(self.config["max_open_trades"])

    def handle_grid_overload(self, grid):
        # Zamknij część gridu, przeprowadź symulację, wyślij alert do roju GIE
        self.gie_system.close_riskiest_grid_positions(grid, keep=self.config["max_grid_size"])

    def handle_margin_risk(self, margin_level):
        # Automatyczne zamykanie najbardziej stratnych pozycji lub full emergency stop
        self.gie_system.emergency_margin_action()

    def handle_predicted_trend_risk(self, grid, predicted):
        # Ogranicz grid, wyślij alert, zmniejsz ekspozycję
        self.gie_system.adapt_grid_on_trend_risk(grid, predicted)

    def meta_reflection(self):
        # Po każdej pętli zapis refleksyjny do logu/meta-pamięci, auto-korekta parametrów
        entry = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "equity": self.gie_system.get_equity(),
            "drawdown": (self.gie_system.get_total_capital() - self.gie_system.get_equity()) / self.gie_system.get_total_capital(),
            "margin_level": self.gie_system.get_margin_level(),
            "open_trades": len(self.gie_system.get_open_trades()),
            "meta_msg": "Meta-refleksja cyklu"
        }
        self.meta_log.append(entry)
        if self.config.get("meta_tune", True):
            self.auto_tune_parameters(entry)

    def auto_tune_parameters(self, entry):
        # Przykład prosty: zmiana grid size po kilku ostrzeżeniach
        if entry['drawdown'] > self.config["max_drawdown"] * 0.8:
            old = self.config["max_grid_size"]
            self.config["max_grid_size"] = max(3, old - 1)
            self.log(f"[META-TUNE] Zmniejszono max_grid_size z {old} do {self.config['max_grid_size']} (drawdown wysokie)")

    def save_snapshot(self):
        from datetime import datetime
        snap_dir = self.config.get("snapshot_dir", "./data/snapshots")
        if not os.path.exists(snap_dir):
            os.makedirs(snap_dir)
        snap = {
            "time": datetime.now().isoformat(),
            "meta_log": self.meta_log[-1] if self.meta_log else {},
            "open_trades": len(self.gie_system.get_open_trades()),
            "capital": self.gie_system.get_total_capital(),
            "equity": self.gie_system.get_equity(),
            "margin_level": self.gie_system.get_margin_level()
        }
        fname = os.path.join(snap_dir, f"meta_snapshot_{int(time.time())}.json")
        with open(fname, 'w') as f:
            json.dump(snap, f, indent=2)
        self.last_snapshot = fname
        self.log(f"[SNAPSHOT] Zapisano snapshot stanu portfela: {fname}")

    def log(self, msg):
        logfile = self.config.get("logfile", "./data/meta_guardian.log")
        with open(logfile, 'a', encoding='utf-8') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
        print(f"[MetaGuardian] {msg}")
