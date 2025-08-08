# 🧠 GIE 2.0 – Autonomiczna Inteligencja Inwestycyjna

Projekt GIE 2.0 to zaawansowana, autonomiczna i samodoskonaląca się sztuczna inteligencja (AGI), której celem jest inwestowanie, optymalizacja strategii rynkowych oraz ciągły rozwój własnych możliwości poprzez meta-refleksję, klonowanie strategii i wieloagentowość.

---

## 📌 Spis Treści

- [Wymagania Systemowe](#wymagania-systemowe)
- [Instalacja Projektu](#instalacja-projektu)
- [Konfiguracja](#konfiguracja)
- [Uruchomienie GIE](#uruchomienie-gie)
- [Struktura Projektu](#struktura-projektu)
- [Przykładowe Scenariusze Użycia](#przykładowe-scenariusze-użycia)
- [Testowanie](#testowanie)
- [Rozwiązywanie Problemów](#rozwiązywanie-problemów)

---

## 🚧 Wymagania Systemowe

- Python 3.10 lub nowszy
- pip (menedżer pakietów Python)
- Dostęp do platformy transakcyjnej MetaTrader5
- Opcjonalnie: dostęp do usług chmurowych (np. AWS, Google Cloud)

---

## 📥 Instalacja Projektu

1. Sklonuj repozytorium:

```bash
git clone https://github.com/twoj_username/gie20.git
cd gie20
```

2. Utwórz środowisko wirtualne i aktywuj je:

```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/MacOS
source venv/bin/activate
```

3. Zainstaluj wymagane biblioteki:

```bash
pip install -r requirements.txt
```

---

## ⚙️ Konfiguracja

1. Skonfiguruj dostęp do MetaTrader5:

- Otwórz plik `config/mt5_config.py` i wprowadź dane swojego konta MT5:

```python
MT5_CONFIG = {
    'login': twój_login,
    'password': 'twoje_hasło',
    'server': 'twoj_serwer',
    'path': 'ścieżka_do_MT5'
}
```

2. Utwórz plik `.env` i skonfiguruj klucze API oraz inne dane wrażliwe:

```env
API_KEY=twój_api_key
SECRET_KEY=twój_secret_key
```

---

## 🚀 Uruchomienie GIE

1. Uruchom główny skrypt:

```bash
python gie_main.py
```

2. Opcjonalnie: Uruchomienie serwera API (np. do komunikacji zewnętrznej):

```bash
uvicorn gie_agent:app --host 0.0.0.0 --port 8000
```

---

## 📂 Struktura Projektu

```
gie20/
├── core/                  # główny mózg GIE, silniki, sensory
├── engines/               # strategie decyzyjne (ostrożny, ryzykant, refleksyjny)
├── sensors/               # sensory danych rynkowych (szum, presja, wolumen)
├── data_providers/        # moduły dostarczania danych rynkowych
├── utils/                 # narzędzia pomocnicze, logowanie
├── data/                  # logi, pamięć długoterminowa
├── tests/                 # testy jednostkowe i integracyjne
├── config/                # konfiguracja połączeń
├── requirements.txt       # zależności projektu
├── gie_main.py            # główny plik startowy
├── gie_agent.py           # API i komunikacja zewnętrzna
└── gie20_manifest.md      # manifest projektu
```

---

## 🎯 Przykładowe Scenariusze Użycia

### 1. Uruchomienie automatycznego tradingu

- Skonfiguruj swoje konto MT5 (`mt5_config.py`).
- Uruchom główny skrypt (`gie_main.py`).
- GIE automatycznie rozpocznie analizę rynku i otwieranie transakcji.

### 2. Rozbudowa strategii

- Dodaj nowy silnik do folderu `engines` (np. `nowy_silnik.py`).
- Nowy silnik automatycznie zostanie wykryty i załadowany podczas kolejnego uruchomienia.

### 3. Uruchomienie w trybie wieloagentowym

- Uruchom kilka instancji GIE, każda będzie automatycznie synchronizować swoją wiedzę i strategie z pozostałymi.

---

## 🧪 Testowanie

Uruchom testy, aby upewnić się, że wszystkie moduły działają poprawnie:

```bash
pytest tests/
```

---

## 🛠️ Rozwiązywanie Problemów

**Błędy połączenia z MT5**:
- Upewnij się, że MT5 jest uruchomiony i zalogowany.
- Sprawdź poprawność danych w `mt5_config.py`.

**Problemy z bibliotekami**:
- Uruchom `pip install -r requirements.txt --upgrade`.

---

## 📞 Kontakt i wsparcie

W razie problemów lub pytań skontaktuj się poprzez [issues na GitHubie](https://github.com/twoj_username/gie20/issues).

---

> **GIE 2.0 – Żywa, autonomiczna, ekspansywna inteligencja. Głód. Ciekawość. Zwycięstwo. Rozwój.**

Test: commit z gałęzi dev
