import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet

class MT5ConfigError(Exception):
    pass

class MT5Config:
    """
    Superinteligentna konfiguracja dla GIE 2.0
    Obsługuje dynamiczne ładowanie, szyfrowanie,
    automatyczne wykrywanie środowiska, multi-broker, 
    logowanie błędów i meta-monitoring.
    """

    def __init__(self, config_file: Optional[str] = None, secret_key: Optional[str] = None):
        self.config_file = config_file or os.getenv("MT5_CONFIG_PATH", "data_providers/mt5_secrets.json")
        self.secret_key = secret_key or os.getenv("MT5_SECRET_KEY")
        self.config: Dict[str, Any] = {}
        self._load_config()

    def _decrypt(self, data: str) -> str:
        if not self.secret_key:
            # Brak klucza, zwracamy plaintext
            return data
        fernet = Fernet(self.secret_key.encode())
        return fernet.decrypt(data.encode()).decode()

    def _encrypt(self, data: str) -> str:
        if not self.secret_key:
            return data
        fernet = Fernet(self.secret_key.encode())
        return fernet.encrypt(data.encode()).decode()

    def _load_config(self):
        try:
            path = Path(self.config_file)
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Szyfrowane
                if data.get("_encrypted", False):
                    decrypted = self._decrypt(data["payload"])
                    self.config = json.loads(decrypted)
                else:
                    self.config = data
            else:
                # Alternatywnie : env lub zmienne środowiskowe
                self.config = {
                    "login": os.getenv("MT5_LOGIN"),
                    "password": os.getenv("MT5_PASSWORD"),
                    "server": os.getenv("MT5_SERVER"),
                    "path": os.getenv("MT5_PATH"),
                    "broker": os.getenv("MT5_BROKER", "default"),
                }
            self._validate_config()
        except Exception as e:
            self.log_error(f"Failed to load MT5 config: {e}")
            raise MT5ConfigError(f"Cannot load MT5 config: {e}")

    def _validate_config(self):
        keys = ["login", "password", "server"]
        for key in keys:
            if not self.config.get(key):
                raise MT5ConfigError(f"Missing required config parameter: {key}")

    def get(self, key: str, default: Optional[Any]=None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any, save: bool = False, encrypt: bool = False):
        self.config[key] = value
        if save:
            self.save(encrypt=encrypt)

    def save(self, encrypt: bool = False):
        path = Path(self.config_file)
        data = self.config
        if encrypt and self.secret_key:
            payload = self._encrypt(json.dumps(self.config))
            data = {"_encrypted": True, "payload": payload}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def log_error(self, message: str):
        print(f"[MT5Config ERROR] {message}")
        # Możesz zintegrować z własnym loggerem lub meta-loggerem GIE

    def reload(self):
        self._load_config()

    def info(self) -> Dict[str, Any]:
        return {k: v for k, v in self.config.items() if "pass" not in k.lower()}

    # Interfejs przyjazny dla innych modułów GIE:

    @property
    def login(self):
        return self.config.get("login")

    @property
    def password(self):
        return self.config.get("password")

    @property
    def server(self):
        return self.config.get("server")

    @property
    def path(self):
        return self.config.get("path")

    @property
    def broker(self):
        return self.config.get("broker", "default")


# # Użycie:
# from data_providers.mt5_config import MT5Config
# config = MT5Config()
# login = config.login

if __name__ == "__main__":
    config = MT5Config()
    print("MT5 configuration info (no passwords):", config.info())
