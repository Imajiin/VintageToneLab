import numpy as np

# --- BAZA ---
class Effect:
    def __init__(self, fs=48000):
        self.active = False
        self.fs = fs
        self.params = {}
    
    def process(self, signal):
        if not self.active: return signal
        return self.apply(signal)
    
    def apply(self, signal): return signal
# --- 1. TUNER (TU-3 Logic) ---
# --- 1. TUNER (TU-3 Logic - WERSJA BEZ MUTE) ---
# --- 1. TUNER (TU-3 PRO VERSION) ---
class BossTU3(Effect):
    def __init__(self, fs):
        super().__init__(fs)
        # Większy bufor = większa precyzja dla niskich strun (E, A)
        self.buffer = np.zeros(8192) 
        self.ptr = 0
        self.is_ready = False
        self.NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    def process(self, signal):
        # Tuner tylko analizuje, sygnał przepuszcza bez zmian (True Bypass)
        self._analyze(signal)
        return signal 

    def _analyze(self, signal):
        # Pobieramy tylko jeden kanał (mono) do analizy
        mono_signal = signal[:, 0]
        chunk_size = len(mono_signal)
        
        # Bufor cykliczny
        if self.ptr + chunk_size > len(self.buffer):
            # Przesuwamy dane w lewo (FIFO)
            self.buffer = np.roll(self.buffer, -chunk_size)
            self.ptr = len(self.buffer) - chunk_size
            
        self.buffer[self.ptr : self.ptr + chunk_size] = mono_signal
        # self.ptr nie zwiększamy w nieskończoność w buforze przesuwnym, 
        # ale tutaj prościej jest trzymać stały wskaźnik końca.
        self.is_ready = True

    def get_tuner_data(self):
        if not self.is_ready: 
            return {'note': '--', 'cents': 0}

        # 1. Okno Hanninga
        windowed = self.buffer * np.hanning(len(self.buffer))
        
        # 2. FFT
        spectrum = np.abs(np.fft.rfft(windowed))
        
        # 3. Szukanie piku
        peak_idx = np.argmax(spectrum)
        max_val = spectrum[peak_idx]

        # --- POPRAWKA: ZMNIEJSZONY PRÓG (BYŁO 2.0) ---
        if max_val < 0.1: 
            return {'note': '--', 'cents': 0}

        # 4. Interpolacja
        if 0 < peak_idx < len(spectrum) - 1:
            y0, y1, y2 = spectrum[peak_idx-1], spectrum[peak_idx], spectrum[peak_idx+1]
            denom = (y0 - 2*y1 + y2)
            if denom != 0:
                delta = 0.5 * (y0 - y2) / denom
                true_idx = peak_idx + delta
            else:
                true_idx = peak_idx
        else:
            true_idx = peak_idx

        # 5. Konwersja na Hz
        freq = true_idx * self.fs / len(self.buffer)

        # --- DIAGNOSTYKA (USUŃ TO JAK JUŻ BĘDZIE DZIAŁAĆ) ---
        # print(f"TUNER DEBUG: Siła={max_val:.2f} | Hz={freq:.2f}") 
        # ----------------------------------------------------

        # 6. Filtrowanie (Gitara: E2=82Hz ... E4=330Hz ... High=1200Hz)
        if freq < 60 or freq > 1500:
            return {'note': '--', 'cents': 0}

        # 7. Wynik
        if freq > 0:
            midi_num = 12 * np.log2(freq / 440.0) + 69
            midi_rounded = int(round(midi_num))
            note_idx = midi_rounded % 12
            deviation = (midi_num - midi_rounded) * 100
            
            note_name = self.NOTE_NAMES[note_idx]
            return {'note': note_name, 'cents': int(deviation)}
            
        return {'note': '--', 'cents': 0}
        
# --- 2. COMPRESSOR (CS-3) ---
class BossCS3(Effect):
    def __init__(self, fs):
        super().__init__(fs)
        self.params = {'level': 0.5, 'attack': 0.5, 'sustain': 0.5} 
        self.envelope = 0.0

    def apply(self, signal):
        attack_coef = 0.01 + self.params['attack'] * 0.1
        release_coef = 0.005 
        thresh = 1.0 - (self.params['sustain'] * 0.8)
        
        output = np.zeros_like(signal)
        for i in range(len(signal)):
            lvl = abs(signal[i, 0])
            if lvl > self.envelope: self.envelope += attack_coef * (lvl - self.envelope)
            else: self.envelope += release_coef * (lvl - self.envelope)
            
            gain = 1.0
            if self.envelope > thresh: gain = thresh / (self.envelope + 0.001)
            
            makeup = 1.0 + self.params['level'] * 3.0
            output[i, 0] = signal[i, 0] * gain * makeup
            
        return np.clip(output, -0.95, 0.95)

# --- 3. PITCH SHIFTER (PS-6) ---
class BossPS6(Effect):
    def __init__(self, fs):
        super().__init__(fs)
        self.params = {'pitch': 0.5, 'balance': 0.5} 
        self.buffer = np.zeros(8000)
        self.w_ptr = 0
        self.r_ptr = 0.0
        
    def apply(self, signal):
        shift_factor = 0.5 + self.params['pitch'] 
        mix = self.params['balance']
        output = np.zeros_like(signal)
        buf_len = len(self.buffer)
        
        for i in range(len(signal)):
            self.buffer[self.w_ptr] = signal[i, 0]
            idx_int = int(self.r_ptr)
            frac = self.r_ptr - idx_int
            s1 = self.buffer[idx_int % buf_len]
            s2 = self.buffer[(idx_int + 1) % buf_len]
            shifted = s1 * (1 - frac) + s2 * frac
            
            output[i, 0] = signal[i, 0] * (1-mix) + shifted * mix
            
            self.w_ptr = (self.w_ptr + 1) % buf_len
            self.r_ptr = (self.r_ptr + shift_factor)
            if self.r_ptr >= buf_len: self.r_ptr -= buf_len
        return output

# --- 4. DISTORTION (DS-1) ---
class BossDS1(Effect):
    def __init__(self, fs):
        super().__init__(fs)
        self.params = {'dist': 0.5, 'tone': 0.5, 'level': 0.5}

    def apply(self, signal):
        drive = 1.0 + self.params['dist'] * 30.0
        # Hard Clipping
        distorted = np.clip(signal * drive, -0.8, 0.8)
        
        # Tone Stack (Scoop)
        t = self.params['tone']
        low_end = np.zeros_like(distorted)
        curr = 0.0
        for i in range(len(distorted)):
            curr += 0.1 * (distorted[i, 0] - curr)
            low_end[i, 0] = curr
        
        high_end = distorted - low_end
        tone_mix = low_end * (1.0 - t) + high_end * t
        
        return tone_mix * self.params['level'] * 2.0

# --- 5. OVERDRIVE (OD-1) ---
class BossOD1(Effect):
    def __init__(self, fs):
        super().__init__(fs)
        self.params = {'drive': 0.5, 'level': 0.5}

    def apply(self, signal):
        drive = 1.0 + self.params['drive'] * 20.0
        # Asymetryczny clipping
        pos = np.tanh(signal * drive)
        neg = np.tanh(signal * drive * 0.7) 
        clipped = np.where(signal > 0, pos, neg)
        return clipped * self.params['level']

# --- 6. FUZZ (FZ-5) ---
class BossFZ5(Effect):
    def __init__(self, fs):
        super().__init__(fs)
        self.params = {'fuzz': 0.5, 'level': 0.5}
        
    def apply(self, signal):
        gain = 5.0 + self.params['fuzz'] * 50.0
        raw = (signal + 0.1) * gain
        return np.clip(raw, -0.9, 0.9) * self.params['level'] * 0.5

# --- 7. BOOSTER (BP-1W) ---
class BossBP1W(Effect):
    def __init__(self, fs):
        super().__init__(fs)
        self.params = {'gain': 0.5, 'level': 0.5}
        
    def apply(self, signal):
        drive = 1.0 + self.params['gain'] * 5.0
        # Saturacja preampu
        saturated = signal * drive - (signal * drive)**3 / 3 
        return saturated * self.params['level']

# --- 8. FLANGER (BF-3) ---
class BossBF3(Effect):
    def __init__(self, fs):
        super().__init__(fs)
        self.params = {'rate': 0.4, 'depth': 0.6, 'res': 0.5} 
        self.buffer = np.zeros(4000)
        self.ptr = 0
        self.lfo_phase = 0.0

    def apply(self, signal):
        rate = 0.1 + self.params['rate'] * 4.0
        depth = self.params['depth'] * 100
        feedback = self.params['res'] * 0.8
        output = np.zeros_like(signal)
        buf_len = len(self.buffer)
        lfo_step = (2 * np.pi * rate) / self.fs
        
        for i in range(len(signal)):
            lfo_val = (1.0 + np.sin(self.lfo_phase)) / 2.0
            current_delay = 20 + lfo_val * depth
            r_idx = int(self.ptr - current_delay) % buf_len
            delayed = self.buffer[r_idx]
            
            inp = signal[i, 0] + delayed * feedback
            self.buffer[self.ptr] = inp
            output[i, 0] = signal[i, 0] + delayed
            
            self.ptr = (self.ptr + 1) % buf_len
            self.lfo_phase += lfo_step
        return output * 0.7

# --- 9. CHORUS (CE-2W) ---
class BossCE2W(Effect):
    def __init__(self, fs):
        super().__init__(fs)
        self.params = {'rate': 0.3, 'depth': 0.5} 
        self.buffer = np.zeros(4800) 
        self.ptr = 0
        self.lfo_phase = 0.0

    def apply(self, signal):
        rate = 0.5 + self.params['rate'] * 3.0
        depth = 50 + self.params['depth'] * 200
        output = np.zeros_like(signal)
        buf_len = len(self.buffer)
        lfo_step = (2 * np.pi * rate) / self.fs
        
        for i in range(len(signal)):
            lfo = np.sin(self.lfo_phase)
            current_delay = 400 + lfo * depth 
            r_idx = int(self.ptr - current_delay) % buf_len
            delayed = self.buffer[r_idx] * 0.8 # Dark analog filter
            
            self.buffer[self.ptr] = signal[i, 0]
            output[i, 0] = signal[i, 0] + delayed
            
            self.ptr = (self.ptr + 1) % buf_len
            self.lfo_phase += lfo_step
        return output

# --- 10. DELAY (DM-2W) ---
class BossDM2W(Effect):
    def __init__(self, fs):
        super().__init__(fs)
        self.params = {'time': 0.3, 'repeat': 0.4, 'intensity': 0.5}
        self.buffer = np.zeros(fs * 2)
        self.ptr = 0
        self.lp_val = 0.0

    def apply(self, signal):
        # NAPRAWIONE: Usunięto błąd w tej linii
        delay_samples = int(0.02 * self.fs + self.params['time'] * 0.6 * self.fs)
        feedback = self.params['repeat'] * 0.9 
        mix = self.params['intensity']
        output = np.zeros_like(signal)
        buf_len = len(self.buffer)
        
        for i in range(len(signal)):
            r_idx = (self.ptr - delay_samples) % buf_len
            delayed = self.buffer[r_idx]
            
            # Analog Degradation Filter
            self.lp_val += 0.3 * (delayed - self.lp_val)
            filtered_delayed = self.lp_val
            
            # TU BYŁ BŁĄD SKŁADNI - TERAZ JEST POPRAWNIE:
            current_in = signal[i, 0]
            
            to_buffer = current_in + filtered_delayed * feedback
            self.buffer[self.ptr] = np.tanh(to_buffer) 
            
            output[i, 0] = current_in + filtered_delayed * mix
            self.ptr = (self.ptr + 1) % buf_len
        return output

# --- 11. REVERB (RV-6) ---
class BossRV6(Effect):
    def __init__(self, fs):
        super().__init__(fs)
        self.params = {'time': 0.4, 'level': 0.4} 
        self.delays = [int(fs*0.029), int(fs*0.037), int(fs*0.043)]
        self.buffers = [np.zeros(d+10) for d in self.delays]
        self.ptrs = [0, 0, 0]

    def apply(self, signal):
        decay = 0.5 + self.params['time'] * 0.45
        level = self.params['level']
        output = np.zeros_like(signal)
        
        for i in range(len(signal)):
            inp = signal[i, 0]
            wet_sum = 0.0
            for k in range(3):
                buf = self.buffers[k]
                ptr = self.ptrs[k]
                read_val = buf[ptr]
                wet_sum += read_val
                buf[ptr] = inp + read_val * decay
                self.ptrs[k] = (ptr + 1) % len(buf)
            output[i, 0] = inp + wet_sum * level * 0.3
        return output