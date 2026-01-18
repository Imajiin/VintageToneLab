# VintageToneLab 🎸

**VintageToneLab** to wirtualny pedalboard gitarowy i symulator wzmacniacza działający w przeglądarce internetowej w czasie rzeczywistym. Aplikacja wykorzystuje język Python do cyfrowego przetwarzania sygnału (DSP) oraz interfejs Web (HTML/CSS/JS) do sterowania efektami.

Stworzone jako projekt zaliczeniowy, demonstrujący możliwości przetwarzania audio w Pythonie przy użyciu bibliotek `numpy` i `sounddevice`.

## 🌟 Funkcje

* **11 Wirtualnych Efektów** inspirowanych klasycznymi kostkami BOSS (m.in. Distortion DS-1, Overdrive OD-1, Chorus CE-2, Delay DM-2, Reverb RV-6).
* **Symulacja Wzmacniacza** typu JCM 900 z pełną korekcją (EQ) i symulacją kolumny.
* **Wbudowany Tuner Chromatyczny** działający w trybie True Bypass.
* **System Presetów** (Clean, Blues, Metal, Ambient).
* **Interfejs w przeglądarce** komunikujący się z silnikiem audio przez WebSocket (brak opóźnień w sterowaniu).
* **Auto-detekcja sprzętu** (obsługa sterowników MME/DirectSound).

## 🛠️ Technologie

* **Backend:** Python 3.11, Flask, Flask-SocketIO.
* **Audio Engine:** NumPy (obliczenia macierzowe DSP), SoundDevice (PortAudio wrapper).
* **Frontend:** HTML5, CSS3 (Custom Design), JavaScript (Vanilla).

## 🚀 Instalacja i Uruchomienie

1.  **Sklonuj repozytorium:**
    ```bash
    git clone [https://github.com/Imajiin/VintageToneLab.git](https://github.com/Imajiin/VintageToneLab.git)
    cd VintageToneLab
    ```

2.  **Stwórz i aktywuj środowisko wirtualne:**
    * Windows:
        ```powershell
        python -m venv venv
        venv\Scripts\activate
        ```
    * Mac/Linux:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Zainstaluj zależności:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Podłącz gitarę:**
    * Podłącz interfejs audio (np. Focusrite Scarlett) do komputera.
    * Podłącz gitarę do wejścia instrumentalnego.

5.  **Uruchom aplikację:**
    ```bash
    python app.py
    ```

6.  **Otwórz przeglądarkę:**
    Wejdź na adres: `http://127.0.0.1:5000`

## ⚠️ Uwagi dotyczące sterowników (Windows)

Aplikacja domyślnie wspiera sterowniki **MME / DirectSound**, co zapewnia najwyższą stabilność i kompatybilność na systemach Windows 10/11.
* Jeśli doświadczasz braku dźwięku na sterownikach WASAPI, wybierz z listy urządzenie z dopiskiem **(MME)**.
* Zalecane ustawienie próbkowania w systemie i interfejsie: **44100 Hz** lub **48000 Hz**.

## 📜 Licencja
Projekt Open Source stworzony w celach edukacyjnych.