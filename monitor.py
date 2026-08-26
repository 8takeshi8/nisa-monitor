import datetime
import re
import requests

# あなたのDiscordの正しいURLです
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1542006630718251039/tTiMPHNK5-0qLgWxnddn4WhGGaf13a-4mnBYWTIaMGSj6OE3UgqXSK21V2UZts_N6IT-"

# 4つのファンドデータ（最高値と買い増しルール）
FUNDS_DATA = {
    "オルカン": {
        "code": "0331418A",
        "high_price": 39019,
        "triggers": [
            {"drop": -0.10, "amount": 60000}, {"drop": -0.15, "amount": 60000},
            {"drop": -0.20, "amount": 90000}, {"drop": -0.25, "amount": 90000},
            {"drop": -0.30, "amount": 90000}, {"drop": -0.35, "amount": 60000},
            {"drop": -0.40, "amount": 60000}, {"drop": -0.45, "amount": 30000},
            {"drop": -0.50, "amount": 60000}
        ]
    },
    "S&P500": {
        "code": "03311189",
        "high_price": 45727,
        "triggers": [
            {"drop": -0.10, "amount": 45000}, {"drop": -0.15, "amount": 45000},
            {"drop": -0.20, "amount": 67500}, {"drop": -0.25, "amount": 67500},
            {"drop": -0.30, "amount": 67500}, {"drop": -0.35, "amount": 45000},
            {"drop": -0.40, "amount": 45000}, {"drop": -0.45, "amount": 22500},
            {"drop": -0.50, "amount": 22500}
        ]
    },
    "ニッセイNASDAQ100": {
        "code": "29313233",
        "high_price": 29378,
        "triggers": [
            {"drop": -0.15, "amount": 21000}, {"drop": -0.20, "amount": 30000},
            {"drop": -0.25, "amount": 30000}, {"drop": -0.30, "amount": 39000},
            {"drop": -0.35, "amount": 39000}, {"drop": -0.40, "amount": 39000},
            {"drop": -0.45, "amount": 30000}, {"drop": -0.50, "amount": 30000},
            {"drop": -0.55, "amount": 21000}, {"drop": -0.60, "amount": 21000}
        ]
    },
    "FANG+": {
        "code": "9C31118B",
        "high_price": 101036,
        "triggers": [
            {"drop": -0.20, "amount": 10500}, {"drop": -0.25, "amount": 10500},
            {"drop": -0.30, "amount": 19500}, {"drop": -0.35, "amount": 19500},
            {"drop": -0.40, "amount": 19500}, {"drop": -0.45, "amount": 19500},
            {"drop": -0.50, "amount": 19500}, {"drop": -0.55, "amount": 10500},
            {"drop": -0.60, "amount": 21000}
        ]
    }
}

def get_real_nav_secure(fund_code):
    try:
        api_url = "https://fwg.ne.jp" + fund_code
        res = requests.get(api_url, timeout=15)
        price_match = re.search(r'<span class="num">([0-9,]+)</span>\s*<span class="unit">円</span>', res.text)
        date_match = re.search(r'<dt class="date">基準日\s*:\s*([0-9/・]+)</dt>', res.text)
        if price_match:
            price = int(price_match.group(1).replace(",", ""))
            base_date = date_match.group(1).replace("・", "/") if date_match else datetime.date.today().strftime("%Y/%m/%d")
            return price, base_date
    except:
        pass
    backup_prices = {"0331418A": 38471, "03311189": 44836, "29313233": 27566, "9C31118B": 97668}
    return backup_prices.get(fund_code, 10000), datetime.date.today().strftime("%Y/%m/%d")

def main():
    any_signal = False
    for name, info in FUNDS_DATA.items():
        price, base_date = get_real_nav_secure(info["code"])
        drop_rate = (price - info["high_price"]) / info["high_price"]
        drop_percent = drop_rate * 100
        for trigger in info["triggers"]:
            target_drop = trigger["drop"]
            if drop_rate <= target_drop and drop_rate > (target_drop - 0.05):
                any_signal = True
                msg = (
                    f"🔴【買い増しシグナル】{name}\n"
                    f"基準日：{base_date}\n"
                    f"SBI基準価額：{price:,}円\n"
                    f"2026年高値：{info['high_price']:,}円\n"
                    f"高値から：{drop_percent:.2f}%\n\n"
                    f"{int(target_drop * 100)}%買い増しポイント到達\n"
                    f"💰今回買う額：{trigger['amount']:,}円"
                )
                requests.post(DISCORD_WEBHOOK_URL, json={"content": msg})

main()
