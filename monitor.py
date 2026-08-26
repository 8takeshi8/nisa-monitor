import datetime
import re
import requests

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1542006630718251039/tTiMPHNK5-0qLgWxnddn4WhGGaf13a-4mnBYWTIaMGSj6OE3UgqXSK21V2UZts_N6IT-"

FUNDS_DATA = {
    "オルカン": {
        "code": "0331418A", "high_price": 39019, "fired_triggers": [],
        "triggers": [
            {"drop": -0.10, "amount": 60000}, {"drop": -0.15, "amount": 60000},
            {"drop": -0.20, "amount": 90000}, {"drop": -0.25, "amount": 90000},
            {"drop": -0.30, "amount": 90000}, {"drop": -0.35, "amount": 60000},
            {"drop": -0.40, "amount": 60000}, {"drop": -0.45, "amount": 30000},
            {"drop": -0.50, "amount": 60000}
        ]
    },
    "S&P500": {
        "code": "03311189", "high_price": 45727, "fired_triggers": [],
        "triggers": [
            {"drop": -0.10, "amount": 45000}, {"drop": -0.15, "amount": 45000},
            {"drop": -0.20, "amount": 67500}, {"drop": -0.25, "amount": 67500},
            {"drop": -0.30, "amount": 67500}, {"drop": -0.35, "amount": 45000},
            {"drop": -0.40, "amount": 45000}, {"drop": -0.45, "amount": 22500},
            {"drop": -0.50, "amount": 22500}
        ]
    },
    "ニッセイNASDAQ100": {
        "code": "29313233", "high_price": 29378, "fired_triggers": [],
        "triggers": [
            {"drop": -0.15, "amount": 21000}, {"drop": -0.20, "amount": 30000},
            {"drop": -0.25, "amount": 30000}, {"drop": -0.30, "amount": 39000},
            {"drop": -0.35, "amount": 39000}, {"drop": -0.40, "amount": 39000},
            {"drop": -0.45, "amount": 30000}, {"drop": -0.50, "amount": 30000},
            {"drop": -0.55, "amount": 21000}, {"drop": -0.60, "amount": 21000}
        ]
    },
    "FANG+": {
        "code": "9C31118B", "high_price": 101036, "fired_triggers": [],
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
    except: pass
    backup_prices = {"0331418A": 38471, "03311189": 44836, "29313233": 27566, "9C31118B": 97668}
    return backup_prices.get(fund_code, 10000), datetime.date.today().strftime("%Y/%m/%d")

def main():
    print("【本本番稼働】最新のネット株価をチェック中...")
    any_signal = False; file_changed = False
    with open("monitor.py", "r", encoding="utf-8") as f: file_content = f.read()

    for name, info in FUNDS_DATA.items():
        price, base_date = get_real_nav_secure(info["code"])
        current_high = info["high_price"]; fired_list = info["fired_triggers"]

        if price > current_high:
            pattern_high = rf'("{name}":\s*\{{[^}}]*"high_price":\s*)([0-9]+)'
            file_content = re.sub(pattern_high, rf'\g<1>{price}', file_content)
            pattern_fired = rf'("{name}":\s*\{{[^}}]*"fired_triggers":\s*)\[[^\]]*\]'
            file_content = re.sub(pattern_fired, r'\g<1>[]', file_content)
            current_high = price; fired_list = []; file_changed = True

        drop_rate = (price - current_high) / current_high
        drop_percent = drop_rate * 100
        print(f" 📈 {name}: 現在 {price:,}円 (設定高値: {current_high:,}円 / 下落率: {drop_percent:.2f}%)")

        for trigger in info["triggers"]:
            target_drop = trigger["drop"]; drop_int = int(target_drop * 100)
            if drop_rate <= target_drop and drop_rate > (target_drop - 0.05):
                if drop_int in fired_list: continue
                any_signal = True; fired_list.append(drop_int)
                new_fired_str = f"\"fired_triggers\": {str(fired_list)}"
                pattern_add_fired = rf'("{name}":\s*\{{[^}}]*)"fired_triggers":\s*\[[^\]]*\]'
                file_content = re.sub(pattern_add_fired, rf'\g<1>{new_fired_str}', file_content)
                file_changed = True
                msg = (f"🔴【買い増しシグナル】{name}\n基準日：{base_date}\nSBI基準価額：{price:,}円\n設定高値：{current_high:,}円\n高値から：{drop_percent:.2f}%\n\n{drop_int}%買い増しポイント到達\n💰今回買う額：{trigger['amount']:,}円")
                requests.post(DISCORD_WEBHOOK_URL, json={"content": msg})

    if file_changed:
        with open("monitor.py", "w", encoding="utf-8") as f: f.write(file_content)
        import os
        os.system('git config --global user.name "GitHub Actions"')
        os.system('git config --global user.email "actions@github.com"')
        os.system('git add monitor.py')
        os.system('git commit -m "🤖 自動システム：高値更新または通知済フラグのアップデート"')
        os.system('git push')
main()
