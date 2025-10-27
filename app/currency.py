import requests

def get_currency_code(currency_name):
    try:
        currencies = requests.get("https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies.json").json()
        for code, name in currencies.items():
            if name == currency_name:
                return code

    except Exception as error:
        return {"error": error}

def get_currency(currency_code):
    try:
        return requests.get("https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies.json").json()[currency_code]
    except Exception as error:
        return {"error": error}

def get_rate(code_1, code_2):
    try:
        return requests.get(f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/{code_1}.json").json()[code_1][code_2]

    except Exception as error:
        return {"error": error}


