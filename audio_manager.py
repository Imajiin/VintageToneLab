import sounddevice as sd
import numpy as np
from effects import (
    BossTU3, BossCS3, BossPS6, BossDS1, BossOD1, BossFZ5, 
    BossBF3, BossBP1W, BossCE2W, BossDM2W, BossRV6
)

class AudioManager:
    def __init__(self):
        self.refresh_devices()
        self.stream = None
        self.fs = 44100 # Bezpieczny start
        self.callback_function = None
        self.gain = 1.0 
        self.eq_params = {'treble': 0.5, 'middle': 0.5, 'bass': 0.5, 'presence': 0.5, 'master': 0.5}
        self.tuner_timer = 0 

        # --- PEDALBOARD ---
        self.chain = {
            'tuner': BossTU3(self.fs),
            'comp':  BossCS3(self.fs),
            'pitch': BossPS6(self.fs),
            'dist':  BossDS1(self.fs),
            'drive': BossOD1(self.fs),
            'fuzz':  BossFZ5(self.fs),
            'boost': BossBP1W(self.fs),
            'flanger': BossBF3(self.fs),
            'chorus': BossCE2W(self.fs),
            'delay':  BossDM2W(self.fs),
            'reverb': BossRV6(self.fs)
        }
        self.order = ['tuner', 'comp', 'pitch', 'dist', 'drive', 'fuzz', 'boost', 'flanger', 'chorus', 'delay', 'reverb']
        self.lp_memory = 0.0
        self.hp_memory_in = 0.0
        self.hp_memory_out = 0.0

    def refresh_devices(self):
        try:
            self.devices = sd.query_devices()
        except:
            self.devices = []

    def set_gain(self, value): self.gain = value

    def list_inputs(self):
        input_devices = []
        print("\n--- DOSTĘPNE STEROWNIKI ---")
        for i, dev in enumerate(self.devices):
            hostapi_name = sd.query_hostapis(dev['hostapi'])['name']
            
            # BLOKUJEMY TYLKO WDM-KS (Bo on u Ciebie nie działa)
            if "WDM-KS" in dev['name'] or "KS" in hostapi_name:
                continue 

            if dev['max_input_channels'] > 0:
                print(f"ID {i}: {dev['name']} ({hostapi_name})")
                input_devices.append({
                    'id': i,
                    'name': f"{dev['name']} ({hostapi_name})",
                    'sr': dev['default_samplerate']
                })
        
        # Sortowanie: DirectSound/MME wyżej, bo są bezpieczniejsze
        input_devices.sort(key=lambda x: ("MME" in x['name'] or "DirectSound" in x['name']), reverse=True)
        return input_devices

    def _find_matching_output(self, input_id):
        try:
            in_info = sd.query_devices(input_id)
            target_api = in_info['hostapi']
            # Szukamy Focusrite na tym samym API
            for i, dev in enumerate(self.devices):
                if dev['hostapi'] == target_api and dev['max_output_channels'] > 0:
                    if "Focusrite" in in_info['name'] and "Focusrite" in dev['name']:
                        return i
            # Fallback
            for i, dev in enumerate(self.devices):
                if dev['hostapi'] == target_api and dev['max_output_channels'] > 0:
                    return i
            return sd.default.device[1]
        except:
            return sd.default.device[1]

    def set_effect_state(self, name, is_active):
        if name in self.chain: self.chain[name].active = is_active

    def set_effect_param(self, name, param, value):
        if name in self.chain and param in self.chain[name].params:
            self.chain[name].params[param] = value

    def apply_amp_sim(self, signal):
        # --- WERSJA "SAFE MODE" (GWARANCJA DŹWIĘKU) ---
        
        # 1. Pobierz ustawienia gałek
        master = self.eq_params.get('master', 0.5)
        bass = self.eq_params.get('bass', 0.5)
        mid = self.eq_params.get('middle', 0.5)
        treble = self.eq_params.get('treble', 0.5)
        gain = self.eq_params.get('preamp', 0.5)

        # 2. Zabezpieczenie: Jeśli Master jest 0, ustaw na połowę (dla testu)
        if master <= 0.05: 
            master = 0.5

        # 3. Prosta symulacja EQ (zamiast filtrów)
        # Podbijamy sygnał w zależności od ustawień EQ
        eq_factor = 0.8 + (bass * 0.2) + (mid * 0.4) + (treble * 0.3)
        
        # 4. Dodajemy lekki "brud" (przester) od Preampu
        # Tanh tworzy miękkie obcinanie (tube sound)
        drive_signal = np.tanh(signal * (1.0 + gain * 5.0))

        # 5. Wyjście
        # Mnożymy przez Master i EQ. 2.0 to zapas głośności.
        output = drive_signal * master * eq_factor * 2.0
        
        return output

    def audio_callback(self, indata, outdata, frames, time, status):
        # 1. Wejście (Suma kanałów)
        if indata.shape[1] >= 2:
            signal = (indata[:, 0:1] + indata[:, 1:2]) * 0.5
        else:
            signal = indata[:, 0:1]

        signal = signal * self.gain
        
        # --- POMIAR 1: WEJŚCIE ---
        vol_in = float(np.abs(signal).mean() * 100)

        # 2. PĘTLA EFEKTÓW (Tu może ginąć dźwięk)
        for name in self.order:
            # ZABEZPIECZENIE: Jeśli któryś efekt zwraca błędy, zignoruj go
            try:
                signal = self.chain[name].process(signal)
            except:
                pass # Ignoruj błędy efektów

        # --- POMIAR 2: PO EFEKTACH ---
        vol_loop = float(np.abs(signal).mean() * 100)

        # 3. WZMACNIACZ (Tu też może ginąć)
        final_signal = self.apply_amp_sim(signal)
        
        # --- POMIAR 3: WYJŚCIE ---
        vol_out = float(np.abs(final_signal).mean() * 100)

        # DIAGNOSTYKA W KONSOLI (Klucz do zagadki)
        #if vol_in > 0.1:
           # print(f"IN: {vol_in:.1f} -> EFEKTY: {vol_loop:.1f} -> AMP: {vol_out:.1f}")

        # Przypisanie na wyjście
        outdata[:, 0] = final_signal[:, 0]
        outdata[:, 1] = final_signal[:, 0]

       # UI Updates
        if self.callback_function:
            vol = float(np.abs(final_signal).mean() * 20)
            
            # Zwolnij odświeżanie tunera (co ok. 10 ramek), żeby nie mrugał jak szalony
            self.tuner_timer += 1
            tuner_info = None
            
            if self.tuner_timer > 4: # Zmniejszyłem z 6 na 4 dla płynności
                self.tuner_timer = 0
                
                # Pobieramy dane TYLKO jeśli Tuner jest włączony (Active)
                if self.chain['tuner'].active:
                    tuner_info = self.chain['tuner'].get_tuner_data()
                else:
                    # Jeśli wyłączony, wyślij null, żeby zgasić diody w JS
                    tuner_info = None 

            self.callback_function(vol, tuner_info)

    def start_streaming(self, device_id, callback):
        self.stop_streaming()
        self.callback_function = callback
        try:
            in_info = sd.query_devices(device_id)
            native_sr = int(in_info['default_samplerate'])
            
            # Bezpiecznik: jeśli sterownik zgłasza dziwne wartości, weź 44100
            if native_sr < 44100: native_sr = 44100
            self.fs = native_sr
            
            for ef in self.chain.values(): ef.fs = self.fs

            output_id = self._find_matching_output(device_id)
            print(f"CONNECTING: {in_info['name']} | SR: {self.fs}")

            self.stream = sd.Stream(
                device=(device_id, output_id),
                channels=(2, 2),
                samplerate=self.fs,
                callback=self.audio_callback,
                blocksize=0, # Auto-size (Najbezpieczniejsze)
                latency=None # Auto-latency (Najbezpieczniejsze)
            )
            self.stream.start()
            print(">>> AUDIO POŁĄCZONE <<<")
        except Exception as e:
            print(f"!!! BŁĄD KRYTYCZNY: {e}")
            raise e

    def stop_streaming(self):
        if self.stream:
            try: self.stream.stop(); self.stream.close()
            except: pass
            self.stream = None