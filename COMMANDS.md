# GIE20 – Skróty Uruchamiania

## 1) Podstawowy start
```bash
python -m core.gie_main_switch
2) Wymuszenie UTF-8
python -X utf8 -m core.gie_main_switch

3) Start z własnym skryptem testowym
python -X utf8 -m core.test_mt5_connection.py


4) Aktywacja venv + start
source venv/bin/activate   # Linux/macOS
.\venv\Scripts\Activate.ps1 # PowerShell
python -X utf8 -m core.gie_main_switch

5) Windows (cmd)
call venv\Scripts\activate.bat
python-X utf8-m core.gie_main_switch

                                                      6) Debug + verbose
                                                      PYTHONUTF8=1 python -X utf8 -m core.gie_main_switch --debug --verbose


Dodaj szybki „sanity‐check” na samym początku pliku
W core/gie_main_switch.py, jeszcze przed jakimkolwiek importem, wstaw:

print("🚀 Startuję GIE20…") 
Uruchamianie z pełnym ścieżkami
Upewnij się, że w katalogu głównym projektu (tam, gdzie masz katalog core/) wykonujesz:

python -X utf8 -m core.gie_main_switch

Alternatywa „bez -m”
Jeżeli wolisz, możesz po prostu odpalić plik bez modułów:

python -X utf8 core/gie_main_switch.py


Dodatkowy flag verbose/debug
Jeśli twój skrypt potrafi przyjmować opcje, np. --verbose, możesz wymusić wypisywanie logów od razu:

python -X utf8 -m core.gie_main_switch --verbose



🚀 Minimalny “rutynowy” start GIE 2.0
(na Twoim Windows + PowerShell, dokładnie tak, jak pokazałeś na zrzutach)

Krok	Komenda (skopiuj ▶ wklej)	Co robi
1. przejdź do katalogu projektu	cd C:\gie20	(jeśli już jesteś – pomiń)
2. aktywuj wirtualne środowisko	& .\venv\Scripts\Activate.ps1	prompt zmieni się na (venv) PS C:\gie20>
3. uruchom meta-mózg w trybie UTF-8 + verbose	python -X utf8 -m core.gie_main_switch --verbose	• włącza globalne kodowanie UTF-8 (–X utf8)
• ładuje moduł core.gie_main_switch
• --verbose pokazuje pełne logi startowe

I to wszystko — aplikacja powinna przejść przez logowanie MT5, załadować silniki, sensory i wystartować pętlę.




📓 Inne, użyteczne skróty (trzymaj je w COMMANDS.md)
Sytuacja	Komenda
Test samego połączenia z MT5	python -X utf8 -m core.test_mt5_connection
Uruchomienie z własnym skryptem (np. scripts/my_script.py)	python -X utf8 scripts\my_script.py
Wyjście z venv	deactivate
(opcjonalnie) alias w aktualnej sesji	doskey gie=python -X utf8 -m core.gie_main_switch --verbose
(potem wystarczy wpisać gie)  




                    