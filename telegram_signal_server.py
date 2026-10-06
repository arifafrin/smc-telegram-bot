import os
import json
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

# ═══════════════════════════════════════════════════════════════
# 🔑 CONFIGURATION (আপনার API Keys এখানে বসান)
# ═══════════════════════════════════════════════════════════════
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID_HERE")
GEMINI_API_KEY     = os.environ.get("GEMINI_API_KEY", "") # ঐচ্ছিক: বসালে AI এনালাইসিস যুক্ত হবে

def send_telegram_message(text):
    """টেলিগ্রাম বট API-এর মাধ্যমে সরাসরি মেসেজ পাঠায়"""
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("[ERROR] Telegram Bot Token set kora hoyni!")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"[ERROR] Telegram send failed: {e}")
        return False

def analyze_with_gemini(signal_text):
    """ঐচ্ছিক: Gemini AI দিয়ে ১ লাইনে প্রফেশনাল ICT ব্রিফিং তৈরি করে"""
    if not GEMINI_API_KEY:
        return ""
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        prompt = (f"Act as an elite ICT/SMC institutional trader. In 2 short bullet points, give a sharp execution tip "
                  f"for this Gold (XAUUSD) signal:\n{signal_text}\nKeep it under 35 words. Be precise.")
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            res_json = json.loads(resp.read().decode('utf-8'))
            ai_text = res_json['candidates'][0]['content']['parts'][0]['text']
            return f"\n\n🤖 <b>Gemini ICT AI Insight:</b>\n<i>{ai_text.strip()}</i>"
    except Exception as e:
        print(f"[WARNING] Gemini analysis skipped: {e}")
        return ""

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        raw_body = self.rfile.read(content_length).decode('utf-8')
        print(f"[RECEIVED WEBHOOK]: {raw_body}")

        # মেসেজ পার্স করা
        message_to_send = ""
        try:
            data = json.loads(raw_body)
            if "message" in data:
                message_to_send = data["message"]
            elif "text" in data:
                message_to_send = data["text"]
            else:
                message_to_send = raw_body
        except:
            message_to_send = raw_body

        # Gemini AI বিশ্লেষণ যোগ করা (যদি API Key থাকে)
        ai_insight = analyze_with_gemini(message_to_send)

        # সুন্দর HTML টেলিগ্রাম ফরম্যাট
        final_tg_msg = (
            f"🔔 <b>TRADINGVIEW SMC + ICT ALERT</b> 🔔\n\n"
            f"{message_to_send}"
            f"{ai_insight}\n\n"
            f"⚡ <i>Execution: Strict SMC Risk Management | Tight SL</i>"
        )

        success = send_telegram_message(final_tg_msg)

        self.send_response(200 if success else 500)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {"status": "ok" if success else "failed"}
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_GET(self):
        """সার্ভার রানিং আছে কিনা চেক করার জন্য (Health Check)"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<h1>TradingView to Telegram SMC Webhook Bridge is LIVE!</h1>")

def run(port=8080):
    server_address = ('', port)
    httpd = HTTPServer(server_address, WebhookHandler)
    print(f"🚀 SMC Webhook Server running on port {port}...")
    httpd.serve_forever()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    run(port)
