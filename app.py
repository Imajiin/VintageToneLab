from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from audio_manager import AudioManager

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*") 
audio_mgr = AudioManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pedalboard')
def pedalboard():
    return render_template('pedalboard.html')

@app.route('/api/devices')
def get_devices():
    return jsonify(audio_mgr.list_inputs())

# NOWOŚĆ: Synchronizacja stanu pedalboardu
@app.route('/api/get_state')
def get_state():
    state = {}
    for name, effect in audio_mgr.chain.items():
        state[name] = {
            'active': effect.active,
            'params': effect.params
        }
    return jsonify(state)

@app.route('/api/select_devices', methods=['POST'])
def select_devices():
    data = request.json
    selected_id = data.get('id')
    
    def send_data_to_socket(volume, tuner_data):
        # Wysyłamy paczkę danych: głośność + tuner (jeśli dostępny)
        payload = {'level': volume}
        if tuner_data:
            payload['tuner'] = tuner_data
            
        socketio.emit('audio_update', payload) # Zmieniona nazwa eventu na 'audio_update'
    # ---------------------------------------
    
    try:
        audio_mgr.start_streaming(selected_id, send_data_to_socket)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
# --- AMP CONTROLS ---
@socketio.on('change_gain')
def handle_gain(data):
    audio_mgr.set_gain(data.get('value', 1.0))

@socketio.on('update_param')
def handle_param(data):
    param = data.get('param')
    val = data.get('value')
    if param == 'gain': audio_mgr.set_gain(val)
    elif param in audio_mgr.eq_params: audio_mgr.eq_params[param] = val / 10.0

# --- PEDALBOARD CONTROLS ---
@socketio.on('toggle_effect')
def handle_toggle(data):
    audio_mgr.set_effect_state(data.get('name'), data.get('active'))

@socketio.on('update_effect')
def handle_update(data):
    audio_mgr.set_effect_param(data.get('name'), data.get('param'), float(data.get('value')))

if __name__ == '__main__':
    socketio.run(app, debug=True)