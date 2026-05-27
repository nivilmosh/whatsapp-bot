from flask import Flask, request
import requests
import anthropic

app = Flask(__name__)

import os
from dotenv import load_dotenv
load_dotenv()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
CLAUDE_CLIENT = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))

def send_whatsapp(to, text):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": text}
    }
    requests.post(url, json=data, headers=headers)

def ask_claude(message):
    response = CLAUDE_CLIENT.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        system="אתה נציג שירות לקוחות מנומס ומועיל. ענה בעברית בצורה קצרה וברורה. אם השאלה מורכבת מאוד, כתוב בדיוק: 'אעביר אותך לנציג אנושי'",
        messages=[{"role": "user", "content": message}]
    )
    return response.content[0].text

@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == "MY_VERIFY_TOKEN":
        return request.args.get("hub.challenge")
    return "שגיאה", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    try:
        msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
        from_number = msg["from"]
        text = msg["text"]["body"]

        reply = ask_claude(text)

        if "אעביר אותך לנציג אנושי" in reply:
            send_whatsapp(from_number, "מעביר אותך לנציג. רגע בבקשה!")
            # כאן אפשר לשלוח התראה לוואטסאפ של הנציג
        else:
            send_whatsapp(from_number, reply)
    except Exception as e:
        print(f"שגיאה: {e}")
    return "OK", 200

if __name__ == "__main__":
    app.run(port=5000)