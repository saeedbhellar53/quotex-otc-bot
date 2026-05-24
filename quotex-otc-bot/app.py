from flask import Flask, render_template_string, jsonify
import random
import os
import time

app = Flask(__name__)

# Simple HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Quotex OTC Signal Bot</title>
    <style>
        body {
            background: linear-gradient(135deg, #0a0a1a, #0f172a);
            color: white;
            font-family: Arial;
            text-align: center;
            padding: 50px;
        }
        .signal {
            font-size: 48px;
            padding: 30px;
            border-radius: 20px;
            margin: 20px auto;
            max-width: 500px;
        }
        .call { background: #22c55e; }
        .put { background: #ef4444; }
        .wait { background: #64748b; }
        .price { font-size: 36px; font-family: monospace; margin: 20px; }
        button {
            background: #ff6b35;
            padding: 15px 30px;
            font-size: 18px;
            border: none;
            border-radius: 10px;
            color: white;
            cursor: pointer;
        }
        .timer { font-size: 24px; margin: 20px; }
    </style>
</head>
<body>
    <h1>🚀 QUOTEX OTC SIGNAL BOT</h1>
    <div class="price" id="price">Loading...</div>
    <div class="signal wait" id="signalBox">WAITING FOR SIGNAL</div>
    <div class="timer" id="timer">Next candle: --s</div>
    <div id="confidence">Confidence: 0%</div>
    <div id="reasons" style="margin: 20px;"></div>
    <button onclick="fetchSignal()">GET SIGNAL NOW</button>
    
    <script>
        function updateTimer() {
            const seconds = new Date().getSeconds();
            const remaining = 60 - seconds;
            document.getElementById('timer').innerHTML = `Next candle: ${remaining}s`;
            if (remaining <= 5 && remaining > 0) {
                fetchSignal();
            }
        }
        
        function fetchSignal() {
            fetch('/api/signal')
                .then(res => res.json())
                .then(data => {
                    document.getElementById('price').innerHTML = data.price;
                    if (data.signal) {
                        const box = document.getElementById('signalBox');
                        box.className = 'signal ' + data.signal.signal.toLowerCase();
                        box.innerHTML = data.signal.signal + ' SIGNAL!';
                        document.getElementById('confidence').innerHTML = 'Confidence: ' + data.signal.confidence + '%';
                        document.getElementById('reasons').innerHTML = data.signal.reasons.join(' + ');
                        new Audio('https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3').play();
                        setTimeout(() => {
                            box.className = 'signal wait';
                            box.innerHTML = 'WAITING FOR SIGNAL';
                        }, 8000);
                    }
                });
        }
        
        setInterval(updateTimer, 1000);
        setInterval(() => {
            fetch('/api/price').then(res => res.json()).then(data => {
                document.getElementById('price').innerHTML = data.price;
            });
        }, 2000);
        fetchSignal();
        updateTimer();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/price')
def get_price():
    # Generate random price
    base = 1.0850
    movement = random.uniform(-0.001, 0.001)
    price = base + movement
    return jsonify({'price': f"{price:.5f}"})

@app.route('/api/signal')
def get_signal():
    # Generate random candle and analyze
    direction = random.choice(['up', 'down'])
    
    if direction == 'up':
        open_price = 1.0850 + random.uniform(-0.0002, 0.0001)
        close_price = open_price + random.uniform(0.0004, 0.0009)
    else:
        open_price = 1.0850 + random.uniform(-0.0001, 0.0002)
        close_price = open_price - random.uniform(0.0004, 0.0009)
    
    high_price = max(open_price, close_price) + random.uniform(0.0001, 0.0003)
    low_price = min(open_price, close_price) - random.uniform(0.0001, 0.0003)
    
    body = abs(close_price - open_price)
    range_c = high_price - low_price
    body_percent = (body / range_c) * 100
    close_position = ((close_price - low_price) / range_c) * 100
    
    signal = None
    if body_percent >= 50:
        if close_price > open_price and close_position >= 70:
            signal = {
                'signal': 'CALL',
                'confidence': random.randint(75, 98),
                'reasons': [f"Strong body: {body_percent:.0f}%", f"Close near high: {close_position:.0f}%"]
            }
        elif close_price < open_price and close_position <= 30:
            signal = {
                'signal': 'PUT',
                'confidence': random.randint(75, 98),
                'reasons': [f"Strong body: {body_percent:.0f}%", f"Close near low: {close_position:.0f}%"]
            }
    
    return jsonify({
        'price': f"{close_price:.5f}",
        'signal': signal
    })

@app.route('/health')
def health():
    return "OK"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
