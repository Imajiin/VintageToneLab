import sounddevice as sd

print("--- LISTA URZĄDZEŃ WYJŚCIOWYCH ---")
devices = sd.query_devices()
for i, dev in enumerate(devices):
    if dev['max_output_channels'] > 0:
        api = sd.query_hostapis(dev['hostapi'])['name']
        print(f"ID: {i} | {dev['name']} | API: {api}")