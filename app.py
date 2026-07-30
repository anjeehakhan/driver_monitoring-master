from flask import Flask, jsonify
from flask_cors import CORS
import threading
import time

# Flask setup
app = Flask(__name__)
CORS(app) # Mobile connection ke liye zaroori hai

# Default state
current_behavior = {
    "state": "Focused" # Options: "Focused", "Drowsy", "Phone Use"
}

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify(current_behavior)

def start_server():
    # host='0.0.0.0' takay phone connect kar sakay
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

if __name__ == "__main__":
    # 1. Flask ko background thread mein start karein
    threading.Thread(target=start_server).start()
    print("Bridge API is running on http://localhost:5000/status")

    # 2. AB YAHAN APNA EXISTING PROJECT CALL KAREIN
    # Example: Agar aapka detection logic main.py mein hai
    # Toh aap wahan se results lane ke liye functions import kar sakte hain
    
    while True:
        # Yahan aap apna dms.py ya facial.py wala function call karein
        # Jo aapko return karay ke driver "Drowsy" hai ya "Focused"
        
        # Maan lijiye aapka logic result deta hai, toh bas is line ko update karein:
        # current_behavior["state"] = "Drowsy" 
        
        time.sleep(0.5)