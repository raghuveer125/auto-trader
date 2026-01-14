import requests

def google_finance_available(symbol: str) -> bool:
    try:
        if symbol.upper() == "SENSEX":
            url = "https://www.google.com/finance/quote/SENSEX:INDEXBOM"
        else:
            return False

        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=5)
        return r.status_code == 200
    except Exception:
        return False
