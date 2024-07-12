from flask import Flask, jsonify, Response, request, render_template
from flask_cors import CORS
import psutil
import cv2
import RPi.GPIO as GPIO

app = Flask(__name__)
CORS(app)

# GPIO setup for water pump and light
GPIO.setmode(GPIO.BCM)
PUMP_PIN = 18
LIGHT_PIN = 23
GPIO.setup(PUMP_PIN, GPIO.OUT)
GPIO.setup(LIGHT_PIN, GPIO.OUT)
GPIO.output(PUMP_PIN, GPIO.LOW)
GPIO.output(LIGHT_PIN, GPIO.LOW)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    status = {
        'cpu': cpu,
        'memory': {
            'total': memory.total,
            'available': memory.available,
            'percent': memory.percent,
            'used': memory.used,
            'free': memory.free
        },
        'disk': {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.percent
        }
    }
    
    return jsonify(status)

def gen_frames():
    camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/pump', methods=['POST'])
def control_pump():
    action = request.json.get('action')
    if action == 'on':
        GPIO.output(PUMP_PIN, GPIO.HIGH)
        return jsonify({'status': 'Pump turned on'})
    elif action == 'off':
        GPIO.output(PUMP_PIN, GPIO.LOW)
        return jsonify({'status': 'Pump turned off'})
    else:
        return jsonify({'status': 'Invalid action'}), 400

@app.route('/api/light', methods=['POST'])
def control_light():
    action = request.json.get('action')
    if action == 'on':
        GPIO.output(LIGHT_PIN, GPIO.HIGH)
        return jsonify({'status': 'Light turned on'})
    elif action == 'off':
        GPIO.output(LIGHT_PIN, GPIO.LOW)
        return jsonify({'status': 'Light turned off'})
    else:
        return jsonify({'status': 'Invalid action'}), 400

@app.route('/api/command', methods=['POST'])
def handle_command():
    command = request.json.get('command').lower()
    if 'pump on' in command:
        GPIO.output(PUMP_PIN, GPIO.HIGH)
        return jsonify({'status': 'Pump turned on'})
    elif 'pump off' in command:
        GPIO.output(PUMP_PIN, GPIO.LOW)
        return jsonify({'status': 'Pump turned off'})
    elif 'light on' in command:
        GPIO.output(LIGHT_PIN, GPIO.HIGH)
        return jsonify({'status': 'Light turned on'})
    elif 'light off' in command:
        GPIO.output(LIGHT_PIN, GPIO.LOW)
        return jsonify({'status': 'Light turned off'})
    else:
        return jsonify({'status': 'Unknown command'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
