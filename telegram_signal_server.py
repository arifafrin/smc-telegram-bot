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

def to_bold_sans(s):
    res = []
    for c in s:
        code = ord(c)
        if 65 <= code <= 90:
            res.append(chr(0x1D5D4 + code - 65))
        elif 97 <= code <= 122:
            res.append(chr(0x1D5EE + code - 97))
        elif 48 <= code <= 57:
            res.append(chr(0x1D7EC + code - 48))
        else:
            res.append(c)
    return ''.join(res)

def format_clean_signal(raw_text):
    """টেলিগ্রামের ফ্রন্ট-ফেসিং বোল্ড সিগন্যাল (বড় টেক্সট ও আইকন হাইলাইট)"""
    if "|" not in raw_text:
        # If this is already a pre-formatted test signal, allow it
        if "CONFIRMED BUY" in raw_text or "CONFIRMED SELL" in raw_text:
            return raw_text
        # Otherwise, silently drop intermediate junk (CHoCH, BOS, Sweep, OB)
        return None
    
    parts = [p.strip() for p in raw_text.split("|")]
    header = parts[0]
    
    is_buy = "BUY" in header.upper()
    is_aplus = "A+" in header.upper()
    
    ticker = "XAUUSD"
    if " on " in header and "@" in header:
        ticker = header.split(" on ")[1].split("@")[0].strip()
    elif " on " in header:
        ticker = header.split(" on ")[1].strip()

    tf_tag = ""
    if "(" in ticker and ")" in ticker:
        tf_part = ticker[ticker.find("(")+1:ticker.find(")")].strip()
        if any(c.isdigit() for c in tf_part) or tf_part.upper() in ["D", "W", "M"]:
            tf_tag = tf_part
            ticker = ticker[:ticker.find("(")].strip()

    t_up = ticker.upper()
    asset_name = f"{ticker} (GOLD)" if ("XAU" in t_up or "GOLD" in t_up) else (
                 f"{ticker} (BITCOIN)" if ("BTC" in t_up) else (
                 f"{ticker} (CRUDE OIL)" if ("OIL" in t_up or "WTI" in t_up or "CL" in t_up) else ticker))

    asset_display = f"{asset_name} • {tf_tag}" if tf_tag else asset_name

    entry = "-"
    if "@" in header:
        entry = header.split("@")[1].strip()
        
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

    # Calculate TP3 (1:5.0)
    tp3 = "-"
    try:
        e_f = float(entry)
        s_f = float(sl)
        risk_f = abs(e_f - s_f)
        if is_buy:
            tp3 = f"{e_f + risk_f * 5.0:.2f}"
        else:
            tp3 = f"{e_f - risk_f * 5.0:.2f}"
    except:
        pass

    sig_icon = "🏆" if is_buy else "🔻"
    action_text = "BUY NOW" if is_buy else "SELL NOW"
    grade_text = "A+" if is_aplus else "B+"
    title_str = f"{grade_text} CONFIRMED {action_text}"
    
    div = "─────────────────────────────"
    retest_line = f"🔄 <b>Retest Zone: {retest}</b>\n" if retest != "-" else ""
    
    msg = (
        f"<b>{sig_icon} {title_str}</b>\n"
        f"<b>Asset: {asset_display}</b>\n"
        f"{div}\n"
        f"🎯 <b>Entry: {entry}</b>\n"
        f"{retest_line}\n"
        f"🛑 <b>Stop Loss: {sl}</b>\n\n"
        f"🚀 <b>Take Profit 1: {tp1} (1:2.0)</b>\n"
        f"🚀 <b>Take Profit 2: {tp2} (1:3.5)</b>\n"
        f"🚀 <b>Take Profit 3: {tp3} (1:5.0)</b>\n"
        f"{div}"
    )
    return msg

def analyze_with_ai(signal_text):
    """See More ক্লিক করলে বাংলায় শর্ট প্রাতিষ্ঠানিক ব্যাখ্যা খুলবে"""
    prompt = (
        f"Act as an elite SMC/ICT institutional trader. "
        f"In Bengali (বাংলায়), giving all trading terms in English "
        f"(e.g., Order Block, Liquidity Sweep, FVG, Break-Even, Retest Zone, Stop Loss, Take Profit, CHoCH, Displacement), "
        f"provide 2 or 3 short sharp bullet points under 45 words explaining institutional rationale and execution.\n\n"
        f"Signal Data: {signal_text}"
    )

    if QWEN_API_KEY:
        endpoints = [
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions",
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        ]
        payload = {
            "model": "qwen-plus",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 120
        }
        data = json.dumps(payload).encode('utf-8')
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {QWEN_API_KEY}"}
        for url in endpoints:
            try:
                req = urllib.request.Request(url, data=data, headers=headers)
                with urllib.request.urlopen(req, timeout=4) as resp:
                    res_json = json.loads(resp.read().decode('utf-8'))
                    ai_text = res_json['choices'][0]['message']['content'].strip()
                    empty = '\u2800'
                    return (
                        f"\n\n<blockquote expandable>🔍 <b>See More — AI Analysis</b>\n"
                        f"{empty}\n{empty}\n"
                        f"🧠 <b>Institutional Analysis:</b>\n{ai_text}</blockquote>"
                    )
            except:
                continue

    if GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                res_json = json.loads(resp.read().decode('utf-8'))
                ai_text = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
                empty = '\u2800'
                return (
                    f"\n\n<blockquote expandable>🔍 <b>See More — AI Analysis</b>\n"
                    f"{empty}\n{empty}\n"
                    f"🧠 <b>Institutional Analysis:</b>\n{ai_text}</blockquote>"
                )
        except:
            pass

    return ""

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

        clean_table = format_clean_signal(message_to_send)
        if not clean_table:
            print(f"[DROPPED NON-SIGNAL]: {message_to_send[:100]}")
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ignored"}).encode('utf-8'))
            return

        ai_block = analyze_with_ai(message_to_send)

        final_tg_msg = clean_table + ai_block
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
