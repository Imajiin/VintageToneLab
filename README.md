Vintage Tone Lab: Analizator YIN 

![Project Status](https://img.shields.io/badge/status-active-success)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![Framework](https://img.shields.io/badge/framework-Flask-lightgrey)

**Vintage Tone Lab** to aplikacja webowa w klimacie retro (wzorowana na wzmacniaczu Marshalla), służąca do analizy sygnału z gitary elektrycznej w czasie rzeczywistym. Projekt łączy niskolatencyjne przetwarzanie dźwięków z interfejsów **Focusrite Scarlett** z autorską implementacją algorytmu detekcji wysokości dźwięku **YIN**

---

## 1. Wymagania sprzętowe (Hardware Setup)

Projekt został zoptymalizowany pod konktretną konfigurację, ale wspiera też rozwiązania mobilne:

* **Interfejs Audio** Focusrite Scarlett (używana 3rd Generation Solo).
    * *Ustawienia*:* Input 1, tryb **INST** (Instrument), opcjonalnie **AIR**.
* **Alternatywa** Wnudowany mikrofon laptopa (wymagana kalibracja bramki szumów w aplikacji).
* **Instrument** Gitara elektryczna / basowa.

---

## 2.Instrukcja uruchomienia (Dev Guide)

### Wymagania sprzętowe
* Python 3.9+
* Sterowniki Focusrite Control (ASIO) zainstalowane w systemie.

## Instalacja 
1. Sklonuj repozytorium
    ```bash
    git clone []
    cd VintageToneLab

2. Tworzenie i aktywacja środowiska wirtualnego 
```python -m venv venv
    source venv/bin/activate #Linux/macOS
    .\venv\Scripts\activate  #Windows

3. Instalacja zależności:
```pip install -r requirements.txt

4. Uruchomienie serwera
```python app.py

---
## 3. Wykorzystane technologie i algorytmy

####  PPP 
* **Algorytm YIN:** Autorska implementacja estymacji częstotliwości podstawowej. Wykorzystujemy kroki: 
    * *Difference Function* (minimalizacja błędu fazy),
    * *Cumulative Mean Normalized Difference* (eliminacja błędów oktawowych),
    * *Absolute Thresholding* oraz *Interpolacja Paraboliczna* dla precyzji do 0.1 Hz.
* **Digital Signal Processing (DSP):** Przetwarzanie sygnału w czasie rzeczywistym z wykorzystaniem biblioteki `NumPy` do operacji macierzowych na buforach audio.
* **Bramka Szumów (Noise Gate):** Dynamiczne odcinanie sygnału poniżej zadanego progu RMS, co pozwala na czystą pracę z mikrofonem laptopa.

#### PAI 
* **Flask & WebSockets:** Wykorzystanie protokołu WebSocket (Socket.io) do strumieniowania danych audio z backendu do frontendu bez przeładowywania strony.
* **Vintage UI (Marshall Style):** Interfejs zaprojektowany w czystym CSS, wykorzystujący techniki *box-shadow* i gradienty do imitacji fizycznego panelu wzmacniacza gitarowego.
* **Canvas API:** Wykorzystanie elementu HTML5 Canvas do renderowania płynnych animacji wskazówki analogowego tunera (60 FPS).

---

##  4. Dokumentacja API 

Aplikacja udostępnia interfejs komunikacyjny, co pozwala na jej integrację z innymi systemami audio.

### Endpointy REST (Flask)
| Endpoint | Metoda | Parametry | Opis |
| :--- | :--- | :--- | :--- |
| `/api/devices` | `GET` | brak | Zwraca listę dostępnych urządzeń wejściowych audio (ID, Nazwa). |
| `/api/select_device` | `POST` | `{"id": int}` | Ustawia aktywne urządzenie wejściowe (np. Scarlett). |

### Komunikaty WebSocket (Socket.io)
* **`volume_update`**: Emituje dane o poziomie sygnału w skali 0-100 (RMS).
* **`pitch_update`**: Emituje słownik `{"note": "E2", "freq": 82.41, "cents": -2}`, pozwalający na aktualizację tunera.

---

##  5. Instrukcja użytkowania (User Guide)

1.  **Podłączenie:** Podłącz gitarę do wejścia 1 (Input 1) w interfejsie Scarlett. Upewnij się, że przycisk **INST** jest podświetlony.
2.  **Uruchomienie:** Odpal serwer `app.py` i wejdź na `localhost:5000`.
3.  **Kalibracja:** Jeśli używasz mikrofonu, zachowaj ciszę przez chwilę, aby bramka szumów mogła się dostosować.
4.  **Strojenie:** Uderz w wybraną strunę. Na złotym panelu Marshalla zobaczysz nazwę nuty.
    * Wskazówka na środku: Gitara nastrojona.
    * Wskazówka w lewo: Dźwięk za niski.
    * Wskazówka w prawo: Dźwięk za wysoki.

---

##  6. Instrukcja dla dewelopera

Jeśli chcesz rozbudować projekt:
1.  Logika analizy dźwięku znajduje się w pliku `yin_algorithm.py`.
2.  Style wizualne wzmacniacza zdefiniowane są w `static/css/style.css`.
3.  Aby dodać nowy efekt (np. Distortion), zaimplementuj nową funkcję w `audio_manager.py` operującą na tablicy `numpy.ndarray`.

---
*Projekt wykonany na potrzeby zaliczenia przedmiotów PPP, PAI oraz OiRPOS.*
