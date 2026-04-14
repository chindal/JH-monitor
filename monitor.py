import requests

TOKEN = "8757989630:AAHybEkn0_QoH2YqEsLmVg1HjBFWlsu9vIs
"
CHAT_ID = "8770376534
"

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
res = requests.post(url, data={
    "chat_id": CHAT_ID,
    "text": "🔥 직접 테스트"
})

print(res.text)
