# test_api.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

try:
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/sources",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
        },
    )

    print("Status:", response.status_code)
    print("Resposta:", response.text)

except Exception as e:
    print("Erro:", e)