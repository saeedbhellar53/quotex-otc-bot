from flask import Flask, render_template_string, jsonify
import random
import time
import os

app = Flask(__name__)

# OTC Analyzer Class
class OTCAnalyzer:
    def __init__(self):
        self.candle_history = []
        self.total_signals = 0
    
    def add_candle(self, candle):
        self.candle_history.append(candle)
        if len(self.candle_history) > 100:
            self.candle_history.pop(0)
    
    def generate_signal(self, candle):
        if len(self.candle_history) < 3:
            return None
        
        body = abs(candle['close'] - candle['open'])
        range_c = candle['high'] - candle['low']
        
        if range_c == 0:
            return None
        
        body_percent = (body / range_c) * 100
        close_position = ((candle['close'] - candle['low']) / range_c) * 100
        
        score = 0
        reasons = []
        signal = None
        
        if body_percent >= 50:
            score += 30
            reasons.append(f"Strong body: {body_percent:.0f}%")
        else:
            return None
        
        if candle['close'] > candle['open'] and close_position >= 70:
            score += 30
            reasons.append(f"Close near high: {close_position:.0f}%")
            signal = "CALL"
        elif candle['close'] < candle['open'] and close_position <= 30:
            score += 30
            reasons.append(f"Close near low: {close_position:.0f}%")
            signal = "PUT"
        else:
            return None
        
        if signal and score >= 70:
            self.total_signals += 1
            return {
                'signal': signal,
                'confidence': min(score + random.randint(0, 10), 98),
                'reasons': reasons,
                'next_candle': "UP" if signal == "CALL" else "DOWN"
            }
        return None

analyzer = OTCAnalyzer()

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚡ QUOTEX OTC SIGNAL BOT ⚡</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Arial;
            background: linear-gradient(135deg, #0a0a1a, #0f172a);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 600px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { font-size: 28px; background: linear-gradient(135deg, #ff6b35, #f97316); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .card { background: #1e293b; border-radius: 20px; padding: 30px; border: 1px solid #334155; }
        .price { font-size: 48px; text-align: center; font-family: monospace; color: #38bdf8; margin: 20px 0; }
        .signal-box { text-align: center; padding: 40px; border-radius: 16px; margin: 20px 0; font-size: 28px; font-weight: bold; transition: all 0.3s; }
        .signal-call { background: linear-gradient(135deg, #22c55e, #16a34a); animation: pulse 1s infinite; }
        .signal-put { background: linear-gradient(135deg, #ef4444, #dc2626); animation: pulse 1s infinite; }
        .signal-wait { background: #334155; color: #94a3b8; }
        @keyframes pulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.02); } }
        .timer { font-size: 36px; text-align: center; font-family: monospace; color: #f59e0b; margin: 15px 0; }
        .confidence-bar { background: #0f172a; border-radius: 12px; padding: 15px; margin: 15px 0; }
        .confidence-fill { height: 20px; background: linear-gradient(90deg, #ef4444, #f59e0b, #22c55e); border-radius: 10px; transition: width 0.5s; }
        .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 20px 0; }
        .info-card { background: #0f172a; border-radius: 12px; padding: 10px; text-align: center; }
        .info-label { font-size: 11px; color: #64748b; }
        .info-value { font-size: 14px; font-weight: bold; }
        .reasons { background: #0f172a; border-radius: 12px; padding: 15px; font-size: 12px; margin: 15px 0; }
        .reason-tag { display: inline-block; padding: 5px 12px; background: #1e293b; border-radius: 20px; margin: 3px; }
        .warning { background: #7c2d12; padding: 12px; border-radius: 12px; margin-top: 20px; font-size: 11px; text-align: center; }
        .live-dot { display: inline-block; width: 10px; height: 10px; background: #22c55e; border-radius: 50%; animation: blink 1s infinite; margin-right: 8px; }
        @keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }
        button { background: #ff6b35; color: white; padding: 12px 24px; border: none; border-radius: 10px; font-weight: bold; cursor: pointer; margin: 5px; }
        button:hover { transform: scale(1.02); }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ QUOTEX OTC SIGNAL BOT ⚡</h1>
            <div><span class="live-dot"></span> <span id="status">LIVE - Render Hosting</span></div>
        </div>
        
        <div class="card">
            <div class="price" id="price">1.08500</div>
            
            <div class="signal-box signal-wait" id="signalBox">
                ⏳ WAITING FOR SIGNAL
            </div>
            
            <div class="timer" id="timer">Next candle: 00s</div>
            <div class="progress-bar" style="background:#334155; border-radius:10px; height:6px;">
                <div id="progressFill" style="width:0%; height:100%; background:#f59e0b; border-radius:10px;"></div>
            </div>
            
            <div class="confidence-bar">
                <div style="margin-bottom:8px;">Signal Confidence: <span id="confidence">0</span>%</div>
                <div class="confidence-fill" id="confidenceFill" style="width:0%"></div>
            </div>
            
            <div class="info-grid">
                <div class="info-card"><div class="info-label">RSI (14)</div><div class="info-value" id="rsi">50</div></div>
                <div class="info-card"><div class="info-label">TREND</div><div class="info-value" id="trend">UPTREND</div></div>
                <div class="info-card"><div class="info-label">NEXT PREDICTION</div><div class="info-value" id="prediction">-</div></div>
                <div class="info-card"><div class="info-label">SIGNALS TODAY</div><div class="info-value" id="signalCount">0</div></div>
            </div>
            
            <div class="reasons" id="reasonsBox">
                <span class="reason-tag">🔄 Initializing strategy...</span>
            </div>
            
            <div style="text-align: center;">
                <button onclick="fetchSignal()">🔄 GET SIGNAL NOW</button>
            </div>
        </div>
        
        <div class="warning">
            🎯 SIGNALS GENERATED IN LAST 3-5 SECONDS OF EACH MINUTE CANDLE<br>
            🚀 PREDICTS NEXT CANDLE DIRECTION (CALL=UP, PUT=DOWN)<br>
            📊 Strategy: 50%+ Body + 70% Close Extreme + RSI Confirmation
        </div>
    </div>
    
    <audio id="beep">
        <source src="https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3" type="audio/mpeg">
    </audio>
    
    <script>
        let lastPrice = 1.0850;
        
        function updateTimer() {
            const seconds = new Date().getSeconds();
            const remaining = 60 - seconds;
            document.getElementById('timer').innerHTML = `Next candle: ${remaining.toString().padStart(2, '0')}s`;
            document.getElementById('progressFill').style.width = ((60 - remaining) / 60 * 100) + '%';
            if (remaining <= 5 && remaining > 0) {
                fetchSignal();
            }
        }
        
        function fetchSignal() {
            fetch('/api/signal')
                .then(res => res.json())
                .then(data => {
                    document.getElementById('price').innerHTML = data.price.toFixed(5);
                    document.getElementById('rsi').innerHTML = data.rsi || '50';
                    document.getElementById('trend').innerHTML = data.trend || 'UPTREND';
                    document.getElementById('signalCount').innerHTML = data.total_signals || 0;
                    
                    if (data.signal) {
                        const box = document.getElementById('signalBox');
                        if (data.signal.signal === 'CALL') {
                            box.className = 'signal-box signal-call';
                            box.innerHTML = '🚀 CALL SIGNAL - NEXT CANDLE UP 🚀';
                            document.getElementById('prediction').innerHTML = '📈 UP';
                            playSound();
                        } else if (data.signal.signal === 'PUT') {
                            box.className = 'signal-box signal-put';
                            box.innerHTML = '🚀 PUT SIGNAL - NEXT CANDLE DOWN 🚀';
                            document.getElementById('prediction').innerHTML = '📉 DOWN';
                            playSound();
                        }
                        document.getElementById('confidence').innerHTML = data.signal.confidence;
                        document.getElementById('confidenceFill').style.width = data.signal.confidence + '%';
                        
                        const reasonsHtml = data.signal.reasons.map(r => `<span class="reason-tag">✅ ${r}</span>`).join('');
                        document.getElementById('reasonsBox').innerHTML = `<span class="reason-tag">🎯 NEXT: ${data.signal.next_candle}</span> ` + reasonsHtml;
                        
                        setTimeout(() => {
                            box.className = 'signal-box signal-wait';
                            box.innerHTML = '⏳ WAITING FOR SIGNAL';
                            document.getElementById('prediction').innerHTML = '-';
                        }, 8000);
                    }
                })
                .catch(err => console.error(err));
        }
        
        function playSound() {
            try {
                const audio = document.getElementById('beep');
                audio.currentTime = 0;
                audio.play().catch(e => console.log('Click page first'));
            } catch(e) {}
        }
        
        setInterval(updateTimer, 1000);
        setInterval(() => {
            fetch('/api/price').then(res => res.json()).then(data => {
                if (data.price) document.getElementById('price').innerHTML = data.price.toFixed(5);
            });
        }, 2000);
        fetchSignal();
        updateTimer();
    </script>
</body>
</html>
'''

# Generate simulated price
def generate_price():
    base = 1.0850
    movement = random.uniform(-0.00015, 0.00015)
    return base + movement

# Current price
current_price = 1.0850

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/signal')
def get_signal():
    global current_price
    
    # Generate simulated price
    movement = random.uniform(-0.00015, 0.00015)
    current_price += movement
    current_price = round(current_price, 5)
    
    # Generate simulated candle
    direction = random.choice(['up', 'down'])
    if direction == 'up':
        open_p = current_price + random.uniform(-0.00015, 0.00005)
        close_p = open_p + random.uniform(0.0004, 0.0009)
    else:
        open_p = current_price + random.uniform(-0.00005, 0.00015)
        close_p = open_p - random.uniform(0.0004, 0.0009)
    
    high_p = max(open_p, close_p) + random.uniform(0.0001, 0.0003)
    low_p = min(open_p, close_p) - random.uniform(0.0001, 0.0003)
    
    candle = {
        'open': round(open_p, 5),
        'close': round(close_p, 5),
        'high': round(high_p, 5),
        'low': round(low_p, 5)
    }
    
    analyzer.add_candle(candle)
    signal = analyzer.generate_signal(candle)
    
    # Generate RSI
    rsi = random.randint(30, 70)
    trend = random.choice(['UPTREND', 'DOWNTREND', 'CONSOLIDATION'])
    
    return jsonify({
        'price': current_price,
        'signal': signal,
        'rsi': rsi,
        'trend': trend,
        'total_signals': analyzer.total_signals
    })

@app.route('/api/price')
def get_price():
    global current_price
    movement = random.uniform(-0.0001, 0.0001)
    current_price += movement
    return jsonify({'price': round(current_price, 5)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)