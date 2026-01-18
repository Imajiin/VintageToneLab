import sounddevice as sd
import numpy as np

def print_sound_level(indata, outdata, frames, time, status):
    if status:
        print(f"Status: {status}")
    
    # Pobieramy głośność lewego (0) i prawego (1) kanału osobno
    # Focusrite Solo: 0 = Mikrofon, 1 = Gitara (Inst)
    volume_left = np.linalg.norm(indata[:, 0]) * 10
    
    if indata.shape[1] > 1:
        volume_right = np.linalg.norm(indata[:, 1]) * 10
    else:
        volume_right = 0
    
    # Rysujemy paski w terminalu
    bar_left = "#" * int(volume_left)
    bar_right = "#" * int(volume_right)
    
    print(f"MIC (L): {bar_left:<20} | GITARA (R): {bar_right:<20}", end='\r')

try:
    print("--- DOSTĘPNE URZĄDZENIA ---")
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        if dev['max_input_channels'] > 0:
            print(f"{i}: {dev['name']}")

    device_id = int(input("\nPodaj ID swojego Focusrite (MME/DirectSound): "))
    
    print("\nNaciśnij Ctrl+C aby zakończyć.\nGRAJ TERAZ NA GITARZE!\n")
    
    with sd.Stream(device=(device_id, None), channels=2, callback=print_sound_level):
        while True:
            sd.sleep(1000)

except KeyboardInterrupt:
    print("\nZakończono.")
except Exception as e:
    print(f"\nBŁĄD: {e}")