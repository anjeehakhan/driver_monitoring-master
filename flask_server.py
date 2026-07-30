from flask import Flask, jsonify
from flask_cors import CORS
# Yahan apne detection logic ko import karein (e.g., from main import get_current_state)

app = Flask(__name__)
CORS(app) # Taake mobile app isse connect kar sakay

# Ye variable aapka detection system update karega
current_status = "Focused" 

@app.route('/status', methods=['GET'])
def get_status():
    # Yahan aap apne detection system se real-time state le sakte hain
    # Example state: "Focused", "Drowsy", "Phone Use"
    return jsonify({"state": current_status})

if __name__ == '__main__':
    # '0.0.0.0' allow karta hai ke aapka phone aapke computer se connect ho sakay
    app.run(host='0.0.0.0', port=5000, debug=True)