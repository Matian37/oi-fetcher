# OI-Fetcher

Program pozwalający na ściąganie swoich rozwiązań z platformy **Szkopuł** dla [checklisty OI](https://github.com/testowyuczen/oi).

---

## Jak działa?

Program używa biblioteczki Playwright do symulowania przegladarki i sciagniecia odpowiednich informacji ze strony. 
Wymagane jest podanie **loginu** i **hasła** (*wcale niepodejrzane*).

Aby nie wykonywać ogromnej ilości zapytań pobierane są wyniki ze strony [Archiwalnych Zadań OI](https://szkopul.edu.pl/task_archive/oi/).
* Warto pamiętać, że jeżeli wysłałeś zgłoszenie do oddzielnego konkursu nie będzie ono tu widoczne.
* Dodatkowo na tej stronie widać wynik **ostatniego** rozwiązania, a nie **maksymalnego**.

Program poprosi cię o lokalizacje folderu zawierającego checklistę i zaktualizujego rozwiązania.
Sciągnięcia lepszego wyniku niż znajduje się w checklistie dodaje te rozwiązanie do już istniejących, w przeciwnym razie robi nic.

## Jak go użyć?

* Pobierz repozytorium
```bash
git clone https://github.com/twoj_user/oi-fetcher.git
cd oi-fetcher
```

* Zainstaluj Pythona
 (najlepiej najnowszą wersję, albo 3.13.7 jeśli są problemy)

* Utwórz wirtualne środowisko w folderze repozytorium
```bash
python -m venv .venv
```

* Aktywuj je:
```bash
Windows (cmd):
.venv\Scripts\activate.bat

Linux / macOS:
source ./.venv/bin/activate
```

* Zainstaluj wymagania
```bash
pip install -r requirements.txt
playwright install firefox
```

* Uruchom program
```bash
python main.py
```
