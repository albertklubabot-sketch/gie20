# core/mt5_login.py

import os
import json
import MetaTrader5 as mt5

def mt5_login(profile: str = "default"):
    """
    Centralny login do MT5 (obsługuje wiele profili, np. klony gie20).
    """
    secrets_file = f"data_providers/mt5_secrets_{profile}.json"
    if not os.path.exists(secrets_file):
        secrets_file = "data_providers/mt5_secrets.json"
    with open(secrets_file, "r") as f:
        secrets = json.load(f)

    mt5_path = secrets.get("MT5_PATH", None)
    login = int(secrets["MT5_LOGIN"])
    password = secrets["MT5_PASSWORD"]
    server = secrets["MT5_SERVER"]

    if mt5_path:
        mt5.initialize(mt5_path)
    else:
        mt5.initialize()

    authorized = mt5.login(login, password, server)
    if not authorized:
        raise RuntimeError(f"MT5: Nie udało się zalogować do MT5! {mt5.last_error()}")
    print(f"[MT5_LOGIN] Zalogowano do MT5 jako {login}@{server}")
    return secrets.get("MT5_SYMBOL", "EURUSD")

def mt5_logout():
    mt5.shutdown()
    print("[MT5_LOGIN] Rozłączono z MT5.")
