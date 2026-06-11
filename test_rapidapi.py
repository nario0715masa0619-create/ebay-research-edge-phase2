import sys
sys.path.insert(0, '.')
import os

rapidapi_key = os.getenv("RAPIDAPI_KEY")
rapidapi_host = os.getenv("RAPIDAPI_HOST")

if not rapidapi_key:
    print("RapidAPI: ❌ KEY MISSING")
elif not rapidapi_host:
    print("RapidAPI: ❌ HOST MISSING")
else:
    print("RapidAPI: ✅ CREDENTIALS PRESENT")
