import json
import MetaTrader5 as mt5

CONFIG_PATH = "data_providers/mt5_secrets.json"

with open(CONFIG_PATH, "r") as f:
    mt5_config = json.load(f)

login = mt5_config["MT5_LOGIN"]
password = mt5_config["MT5_PASSWORD"]
server = mt5_config["MT5_SERVER"]
path = mt5_config.get("MT5_PATH")
symbol = mt5_config.get("MT5_SYMBOL", "EURUSD")

print(f"Próba połączenia z MT5 (login={login}, server={server}, path={path})...")

init_kwargs = dict(login=login, password=password, server=server)
if path:
    init_kwargs['path'] = path

if not mt5.initialize(**init_kwargs):
    print("❌ Błąd połączenia:", mt5.last_error())
else:
    print("[OK] Połączono z MT5!")

    # Sprawdź konto
    info = mt5.account_info()
    print("Konto:", info)

    # Tick testowy
    if symbol:
        tick = mt5.symbol_info_tick(symbol)
        print(f"Tick {symbol}:", tick)

    mt5.shutdown()
    print("Rozłączono.")
