import os
import json
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

# ═══════════════════════════════════════════════════════════════
# 🔑 CONFIGURATION (Environment Variables)
# ═══════════════════════════════════════════════════════════════
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID_HERE")
GEMINI_API_KEY     = os.environ.get("GEMINI_API_KEY", "")
QWEN_API_KEY       = os.environ.get("Qwen_Cloud_API_KEY", os.environ.get("QWEN_API_KEY", ""))

def format_telegram_alert(raw_text):
    """TradingView alert-কে সুন্দর বক্সড ও হাইলাইটেড ফরম্যাটে সাজায়"""
    if "|" not in raw_text:
        return f"🔔 <b>TRADINGVIEW SMC ALERT</b> 🔔\n\n{raw_text}"
    
    parts = [p.strip() for p in raw_text.split("|")]
    header = parts[0]
    
    is_buy = "BUY" in header.upper()
    is_sell = "SELL" in header.upper()
    is_aplus = "A+" in header.upper()
    
    ticker = "XAUUSD"
    entry = "-"
    if "@" in header:
        h_split = header.split("@")
        entry = h_split[1].strip()
        if " on " in h_split[0]:
            ticker = h_split[0].split(" on ")[1].strip()
            
    sl = tp1 = tp2 = retest = "-"
    for p in parts[1:]:
        if p.startswith("SL:"):
            sl = p.replace("SL:", "").strip()
        elif p.startswith("TP1:"):
            tp1 = p.replace("TP1:", "").strip()
        elif p.startswith("TP2:"):
            tp2 = p.replace("TP2:", "").strip()
        elif p.startswith("Retest:"):
            retest = p.replace("Retest:", "").strip()
            
    title_emoji = "🏆" if is_aplus else "⚖️"
    dir_emoji = "🟢" if is_buy else "🔴"
    action_text = "CONFIRMED BUY NOW 🚀" if is_buy else "CONFIRMED SELL NOW 📉"
    grade_text = "A+ GRADE SETUP (High Win Probability)" if is_aplus else "B+ GRADE SETUP (Standard Setup)"
    border = "━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    msg = (
        f"{border}\n"
        f"{title_emoji} <b>{grade_text}</b>\n"
        f"{dir_emoji} <b>ACTION: {action_text}</b>\n"
        f"{border}\n\n"
        f"📊 <b>Asset:</b> <code>{ticker}</code>\n"
        f"🎯 <b>Entry Price:</b> <code>{entry}</code>\n"
        f"🔄 <b>Retest Zone:</b> <code>{retest}</code>\n\n"
        f"🛑 <b>Stop Loss:</b> <code>{sl}</code>\n"
        f"🚀 <b>Take Profit 1:</b> <code>{tp1}</code> (1:2.0 • Lock BE)\n"
        f"🔥 <b>Take Profit 2:</b> <code>{tp2}</code> (1:3.5 • Runner Target)\n\n"
        f"{border}\n"
        f"🛡️ <i>Strategy: Smart Money Concepts (ICT)</i>\n"
        f"⚡ <i>Risk Management: Follow Strict SL & Move to BE at TP1</i>"
    )
    return msg

def send_telegram_message(text):
    """টেলিগ্রাম বট API-এর মাধ্যমে সরাসরি মেসেজ পাঠায় (আপনার ও ফ্রেন্ডের উভয় আইডিতে যাবে)"""
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("[ERROR] Telegram Bot Token set kora hoyni!")
        return False
    
    chat_ids = [cid.strip() for cid in str(TELEGRAM_CHAT_ID).split(",") if cid.strip()]
    if not chat_ids:
        print("[ERROR] No valid Chat ID found!")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    any_success = False

    for cid in chat_ids:
        payload = {
            "chat_id": cid,
            "text": text,
            "parse_mode": "HTML"
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    any_success = True
        except Exception as e:
            print(f"[ERROR] Telegram send failed for chat_id {cid}: {e}")

    return any_success

def analyze_with_qwen(signal_text):
    if not QWEN_API_KEY:
        return ""
    endpoints = [
        "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions",
        "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    ]
    prompt = (f"Act as an elite ICT/SMC institutional trader. In 2 short bullet points, give a sharp execution tip "
              f"for this Gold (XAUUSD) signal:\n{signal_text}\nKeep it under 35 words. Be precise.")
    payload = {
        "model": "qwen-plus",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 100
    }
    data = json.dumps(payload).encode('utf-8')
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {QWEN_API_KEY}"}
    for url in endpoints:
        try:
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                res_json = json.loads(resp.read().decode('utf-8'))
                ai_text = res_json['choices'][0]['message']['content']
                return f"\n\n🤖 <b>Qwen AI Tip:</b>\n<i>{ai_text.strip()}</i>"
        except:
            continue
    return ""

def analyze_with_gemini(signal_text):
    if not GEMINI_API_KEY:
        return ""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        prompt = (f"Act as an elite ICT/SMC institutional trader. In 2 short bullet points, give a sharp execution tip "
                  f"for this Gold (XAUUSD) signal:\n{signal_text}\nKeep it under 35 words. Be precise.")
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            res_json = json.loads(resp.read().decode('utf-8'))
            ai_text = res_json['candidates'][0]['content']['parts'][0]['text']
            return f"\n\n🤖 <b>Gemini AI Tip:</b>\n<i>{ai_text.strip()}</i>"
    except:
        return ""

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        raw_body = self.rfile.read(content_length).decode('utf-8')
        print(f"[RECEIVED WEBHOOK]: {raw_body}")

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

        formatted_signal = format_telegram_alert(message_to_send)

        ai_insight = analyze_with_qwen(message_to_send)
        if not ai_insight:
            ai_insight = analyze_with_gemini(message_to_send)

        final_tg_msg = formatted_signal + ai_insight

        success = send_telegram_message(final_tg_msg)

        self.send_response(200 if success else 500)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok" if success else "failed"}).encode('utf-8'))

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<h1>TradingView to Telegram SMC Webhook Bridge is LIVE!</h1>")

def run(port=8080):
    server_address = ('', port)
    httpd = HTTPServer(server_address, WebhookHandler)
    print(f"[START] SMC Webhook Server running on port {port}...")
    httpd.serve_forever()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    run(port)
