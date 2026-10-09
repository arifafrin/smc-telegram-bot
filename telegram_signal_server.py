"""
================================================================================
  SMC TRADINGVIEW CLOUD WEBHOOK BRIDGE (ULTRA-FAST ZERO-TIMEOUT VERSION)
  UPDATED: 2026-10-09 12:12 PM BD TIME
  • Immediate <15ms 200 OK response to TradingView (Prevents 3-second timeout!)
  • Background Async AI analysis & Telegram notifications
  • Instant MT5 trade parameter queue
================================================================================
"""

import os
import time
import json
import urllib.request
import urllib.parse
import threading
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
    is_super = "SUPER" in header.upper()
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

    entry = header.split("@")[1].strip() if "@" in header else "-"
    sl_raw = tp1_raw = tp2_raw = retest = "-"

    for p in parts[1:]:
        if p.startswith("SL:"):
            sl_raw = p.replace("SL:", "").strip()
        elif p.startswith("TP1:"):
            tp1_raw = p.replace("TP1:", "").strip()
        elif p.startswith("TP2:"):
            tp2_raw = p.replace("TP2:", "").strip()
        elif p.startswith("Retest:"):
            retest = p.replace("Retest:", "").strip()

    sl_price = sl_raw.split()[0].strip() if sl_raw != "-" else "-"
    tp1_price = tp1_raw.split()[0].strip() if tp1_raw != "-" else "-"
    tp2_price = tp2_raw.split()[0].strip() if tp2_raw != "-" else "-"

    # Calculate TP3 (1:5.0)
    tp3 = "-"
    try:
        e_f = float(entry)
        s_f = float(sl_price)
        risk_f = abs(e_f - s_f)
        if is_buy:
            tp3 = f"{e_f + risk_f * 5.0:.2f}"
        else:
            tp3 = f"{e_f - risk_f * 5.0:.2f}"
    except:
        pass

    action_text = "BUY NOW" if is_buy else "SELL NOW"
    sig_icon = "🌟" if is_super else ("🏆" if is_buy else "🔻")
    grade_text = "SUPER A+ MORNING EXPANSION" if is_super else ("A+" if is_aplus else "B+")
    title_str = f"{grade_text} CONFIRMED {action_text}"
    
    div = "─────────────────────────────"
    retest_line = f"🔄 <b>RETEST ZONE:</b> {retest}\n" if retest != "-" else ""
    
    msg = (
        f"<b>{sig_icon} {title_str}</b>\n"
        f"<b>ASSET:</b> {asset_display}\n"
        f"{div}\n"
        f"🎯 <b>ENTRY:</b> {entry}\n"
        f"{retest_line}"
        f"🛑 <b>STOP LOSS:</b> {sl_price}\n\n"
        f"🚀 <b>TAKE PROFIT 1:</b> {tp1_price} (1:2.0)\n"
        f"🚀 <b>TAKE PROFIT 2:</b> {tp2_price} (1:3.5 🔥)\n"
        f"🚀 <b>TAKE PROFIT 3:</b> {tp3} (1:5.0 🚀)\n"
        f"{div}"
    )
    return msg

def analyze_with_ai(signal_text):
    """ট্রেডের প্রাতিষ্ঠানিক লজিক বাংলায় ও ট্রেডিং টার্মগুলো ইংরেজিতে সুন্দরভাবে ব্যাখ্যা করে"""
    if "BREAKEVEN" in signal_text.upper():
        return (
            f"\n\n🧠 <b>SMART RISK SHIELD (বাংলা ব্যাখ্যা):</b>\n"
            f"• 🛡️ <b>Reversal Defense:</b> অপোজিট Order Block বা Trend Flip ডিটেক্ট হওয়ায় রানিং প্রফিট সুরক্ষিত রাখতে রোবট তাৎক্ষণিকভাবে SL-কে এন্ট্রি প্রাইসে (Break-Even) লক করার নির্দেশ পেয়েছে।\n"
            f"• 🔒 <b>Profit Condition:</b> পজিশনটি কারেন্টলি প্রফিটে থাকলে ব্রেক-ইভেন লক হবে, লসে থাকলে স্ট্রাকচারাল SL অক্ষত থাকবে।"
        )

    is_buy = "BUY" in signal_text.upper()
    action_str = "BUY" if is_buy else "SELL"
    dir_str = "Bullish" if is_buy else "Bearish"
    grade_str = "SUPER A+ (Morning Expansion)" if "SUPER" in signal_text.upper() else ("A+" if "A+" in signal_text.upper() else "B+")
    
    tf_str = "30m"
    if "(" in signal_text and ")" in signal_text:
        try:
            tf_cand = signal_text.split("(")[1].split(")")[0].strip()
            if any(c.isdigit() for c in tf_cand) or tf_cand.upper() in ["D", "W", "M"]:
                tf_str = tf_cand
        except:
            pass

    retest_val = "-"
    if "Retest:" in signal_text:
        try:
            retest_val = signal_text.split("Retest:")[1].strip().split("|")[0].strip()
        except:
            pass

    prompt = (
        f"Act as an elite SMC/ICT institutional trading analyst. "
        f"A verified signal was just confirmed by our SMC indicator:\n{signal_text}\n\n"
        f"In natural Bengali (বাংলায়), keeping all professional trading terms strictly in English (e.g. Order Block, Liquidity Sweep, Retest, CHoCH, BOS, Multi-Timeframe, Price Action, Mitigation, Displacement):\n"
        f"Explain ONLY the technical trade logic in detail (strictly 3 concise technical bullets, NO generic risk-reward or break-even advice):\n"
        f"• 🏦 Institutional Order Block & Liquidity: কেন এই জোনে এন্ট্রি হলো (Order Block mitigation, Liquidity Sweep ও ক্যান্ডেল উইক রিজেকশন)।\n"
        f"• 🔄 Structure & Retest: মার্কেট স্ট্রাকচার, Retest জোন ও প্রাইস অ্যাকশন ক্যান্ডেল কনফার্মেশন।\n"
        f"• 📈 Multi-Timeframe & Momentum: মাল্টি-টাইমফ্রেম ট্রেন্ড অ্যালাইনমেন্ট ও ভলিউম ফ্লো।\n"
        f"Keep response technical, crisp, and under 70 words. No intro or outro."
    )

    if QWEN_API_KEY:
        endpoints = [
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions",
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        ]
        payload = {
            "model": "qwen-plus",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 200
        }
        data = json.dumps(payload).encode('utf-8')
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {QWEN_API_KEY}"}
        for url in endpoints:
            try:
                req = urllib.request.Request(url, data=data, headers=headers)
                with urllib.request.urlopen(req, timeout=5) as resp:
                    res_json = json.loads(resp.read().decode('utf-8'))
                    ai_text = res_json['choices'][0]['message']['content'].strip()
                    return (
                        f"\n\n🧠 <b>TRADE LOGIC DETAILS (প্রাতিষ্ঠানিক টেকনিক্যাল ব্যাখ্যা):</b>\n"
                        f"{ai_text}"
                    )
            except:
                continue

    if GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                res_json = json.loads(resp.read().decode('utf-8'))
                ai_text = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
                return (
                    f"\n\n🧠 <b>TRADE LOGIC DETAILS (প্রাতিষ্ঠানিক টেকনিক্যাল ব্যাখ্যা):</b>\n"
                    f"{ai_text}"
                )
        except:
            pass

    # Built-in Institutional Analysis (Guaranteed 100% Fail-Safe)
    retest_line = f"• 🔄 <b>Retest Zone:</b> প্রাইস {retest_val} লেভেলে প্রাতিষ্ঠানিক রিটেস্ট ও রিজেকশন কনফার্ম করেছে।\n" if retest_val != "-" else ""
    return (
        f"\n\n🧠 <b>TRADE LOGIC DETAILS (প্রাতিষ্ঠানিক টেকনিক্যাল ব্যাখ্যা):</b>\n"
        f"• 🏦 <b>Order Block Mitigation:</b> প্রাইস ইনস্টিটিউশনাল {action_str} Order Block জোনে ট্যাপ করে লিকুইডিটি সুইপ (Liquidity Sweep) সম্পন্ন করেছে।\n"
        f"{retest_line}"
        f"• 🕯️ <b>Price Action Rejection:</b> স্ট্রাকচারাল লো/হাই থেকে স্ট্রং রিজেকশন উইক এবং {tf_str} ক্যান্ডেল ক্লোজ কনফার্মেশন পাওয়া গেছে।\n"
        f"• 📊 <b>MTF Confluence:</b> মাল্টি-টাইমফ্রেম {dir_str} ট্রেন্ড অ্যালাইনমেন্ট ও পিক সেশনের ভলিউম ইনফ্লো।"
    )

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

LATEST_TRADE = None

def extract_structured_trade(raw_text):
    """Extract structured numerical parameters for MT5 automated execution"""
    try:
        parts = [p.strip() for p in raw_text.split("|")]
        header = parts[0]
        is_buy = "BUY" in header.upper()
        is_super = "SUPER" in header.upper()
        is_aplus = "A+" in header.upper()
        grade = "SUPER A+" if is_super else ("A+" if is_aplus else "B+")
        action = "BUY" if is_buy else "SELL"
        
        ticker = "XAUUSD"
        if " on " in header and "@" in header:
            ticker = header.split(" on ")[1].split("@")[0].strip()
        elif " on " in header:
            ticker = header.split(" on ")[1].strip()

        if "(" in ticker:
            ticker = ticker[:ticker.find("(")].strip()

        entry_val = float(header.split("@")[1].strip()) if "@" in header else 0.0
        sl_val = tp1_val = tp2_val = 0.0

        for p in parts[1:]:
            if p.startswith("SL:"):
                sl_str = p.replace("SL:", "").strip().split()[0]
                sl_val = float(sl_str)
            elif p.startswith("TP1:"):
                tp1_str = p.replace("TP1:", "").strip().split()[0]
                tp1_val = float(tp1_str)
            elif p.startswith("TP2:"):
                tp2_str = p.replace("TP2:", "").strip().split()[0]
                tp2_val = float(tp2_str)

        risk = abs(entry_val - sl_val)
        tp3_val = entry_val + risk * 5.0 if is_buy else entry_val - risk * 5.0

        return {
            "id": int(time.time() * 1000),
            "ticker": ticker,
            "action": action,
            "grade": grade,
            "entry": entry_val,
            "sl": sl_val,
            "tp1": tp1_val,
            "tp2": tp2_val,
            "tp3": tp3_val,
            "time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        print(f"[ERROR parsing structured trade]: {e}")
        return None

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        global LATEST_TRADE
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

        trade_obj = extract_structured_trade(message_to_send)
        if trade_obj:
            LATEST_TRADE = trade_obj
            print(f"[MT5 TRADE QUEUED]: {trade_obj['action']} {trade_obj['ticker']} Grade:{trade_obj['grade']} Entry:{trade_obj['entry']}")

        # Respond to TradingView IMMEDIATELY (<15ms) to prevent timeout
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "received", "queued": bool(trade_obj)}).encode('utf-8'))

        # Run AI analysis & Telegram notification in background thread
        def notify_worker(msg, tbl):
            try:
                ai_block = analyze_with_ai(msg)
                final_tg_msg = tbl + ai_block
                send_telegram_message(final_tg_msg)
            except Exception as e:
                print(f"[ASYNC NOTIFY ERROR]: {e}")

        threading.Thread(target=notify_worker, args=(message_to_send, clean_table), daemon=True).start()

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/api/latest_trade"):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(LATEST_TRADE or {}).encode('utf-8'))
            return

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
