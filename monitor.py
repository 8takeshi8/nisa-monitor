import datetime
import os
import re
import requests

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1542006630718251039/tTiMPHNK5-0qLgWxnddn4WhGGaf13a-4mnBYWTIaMGSj6OE3UgqXSK21V2UZts_N6IT-"

# 150万円の買い増しグラデーションルール
FUNDS_DATA = {
    "オルカン": {
        "code": "0331418A", "high_price": 39019, "fired_triggers": [],
        "triggers": [
            {"drop": -0.10, "amount": 30000},  {"drop": -0.15, "amount": 30000},
            {"drop": -0.20, "amount": 48000},  {"drop": -0.25, "amount": 60000},
            {"drop": -0.30, "amount": 72000},  {"drop": -0.35, "amount": 78000},
            {"drop": -0.40, "amount": 84000},  {"drop": -0.45, "amount": 90000},
            {"drop": -0.50, "amount": 108000}
        ]
    },
    "S&P500": {
        "code": "03311189", "high_price": 45727, "fired_triggers": [],
        "triggers": [
            {"drop": -0.10, "amount": 23000},  {"drop": -0.15, "amount": 23000},
            {"drop": -0.20, "amount": 36000},  {"drop": -0.25, "amount": 45000},
            {"drop": -0.30, "amount": 54000},  {"drop": -0.35, "amount": 59000},
            {"drop": -0.40, "amount": 63000},  {"drop": -0.45, "amount": 68000},
            {"drop": -0.50, "amount": 79000}
        ]
    },
    "ニッセイNASDAQ100": {
        "code": "29313233", "high_price": 29378, "fired_triggers": [],
        "triggers": [
            {"drop": -0.15, "amount": 12000},  {"drop": -0.20, "amount": 15000},
            {"drop": -0.25, "amount": 18000},  {"drop": -0.30, "amount": 24000},
            {"drop": -0.35, "amount": 30000},  {"drop": -0.40, "amount": 36000},
            {"drop": -0.45, "amount": 39000},  {"drop": -0.50, "amount": 42000},
            {"drop": -0.55, "amount": 42000},  {"drop": -0.60, "amount": 42000}
        ]
    },
    "FANG+": {
        "code": "9C31118B", "high_price": 101036, "fired_triggers": [],
        "triggers": [
            {"drop": -0.20, "amount": 7500},   {"drop": -0.25, "amount": 7500},
            {"drop": -0.30, "amount": 12000},  {"drop": -0.35, "amount": 15000},
            {"drop": -0.40, "amount": 18000},  {"drop": -0.45, "amount": 19500},
            {"drop": -0.50, "amount": 21000},  {"drop": -0.55, "amount": 22500},
            {"drop": -0.60, "amount": 27000}
        ]
    }
}

def get_real_nav_secure(fund_code):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        api_url = f"https://fwg.ne.jp/fund/detail/{fund_code}"
        res = requests.get(api_url, headers=headers, timeout=15)
        price_match = re.search(r'<span class="num">([0-9,]+)</span>\s*<span class="unit">円</span>', res.text)
        date_match = re.search(r'<dt class="date">基準日\s*:\s*([0-9/・]+)</dt>', res.text)
        if price_match:
            price = int(price_match.group(1).replace(",", ""))
            base_date = date_match.group(1).replace("・", "/") if date_match else datetime.date.today().strftime("%Y/%m/%d")
            return price, base_date
    except Exception as e:
        print(f"取得エラー ({fund_code}): {e}")
    
    backup_prices = {"0331418A": 39019, "03311189": 45727, "29313233": 29378, "9C31118B": 101036}
    return backup_prices.get(fund_code, 10000), datetime.date.today().strftime("%Y/%m/%d")

def main():
    print("【本番稼働】最新のネット株価をチェック中...")
    file_changed = False
    
    if os.path.exists("monitor.py"):
        with open("monitor.py", "r", encoding="utf-8") as f:
            file_content = f.read()
    else:
        file_content = ""

    today_str = datetime.date.today().strftime("%Y/%m/%d")
    report_msg = f"📊 【日次】NISA買い増し監視レポート\n基準日：{today_str}\n\n"

    for name, info in FUNDS_DATA.items():
        price, base_date = get_real_nav_secure(info["code"])
        current_high = info["high_price"]
        fired_list = info["fired_triggers"]

        # 高値更新時
        if price > current_high:
            pattern_high = rf'("{name}":\s*\{{[^}}]*"high_price":\s*)([0-9]+)'
            file_content = re.sub(pattern_high, rf'\g<1>{price}', file_content)
            pattern_fired = rf'("{name}":\s*\{{[^}}]*"fired_triggers":\s*)\[[^\]]*\]'
            file_content = re.sub(pattern_fired, r'\g<1>[]', file_content)
            current_high = price
            fired_list = []
            file_changed = True

        drop_rate = (price - current_high) / current_high
        drop_percent = drop_rate * 100

        # 次の買い増しターゲット選定
        next_trigger = None
        for t in info["triggers"]:
            if drop_rate > t["drop"]:
                next_trigger = t
                break
        if next_trigger is None:
            next_trigger = info["triggers"][-1]

        target_price = int(current_high * (1 + next_trigger["drop"]))
        diff_price = max(0, price - target_price)

        report_msg += (
            f"🔹 **{name}**\n"
            f"現在価格：{price:,}円 (高値から {drop_percent:.2f}%)\n"
            f"次の目標：{target_price:,}円 ({int(next_trigger['drop']*100)}%)\n"
            f"➔ あと **{diff_price:,}円** 下落で発動（投入：{next_trigger['amount']:,}円）\n\n"
        )

        # 買い増し判定
        for trigger in info["triggers"]:
            target_drop = trigger["drop"]
            drop_int = int(target_drop * 100)
            if drop_rate <= target_drop and drop_rate > (target_drop - 0.05):
                if drop_int in fired_list:
                    continue
                fired_list.append(drop_int)
                new_fired_str = f"\"fired_triggers\": {str(fired_list)}"
                pattern_add_fired = rf'("{name}":\s*\{{[^}}]*)"fired_triggers":\s*\[[^\]]*\]'
                file_content = re.sub(pattern_add_fired, rf'\g<1>{new_fired_str}', file_content)
                file_changed = True
                
                signal_msg = (
                    f"🔴【買い増しシグナル】{name}\n"
                    f"基準日：{base_date}\n"
                    f"基準価額：{price:,}円\n"
                    f"設定高値：{current_high:,}円\n"
                    f"高値から：{drop_percent:.2f}%\n\n"
                    f"{drop_int}%買い増しポイント到達\n"
                    f"💰今回買う額：{trigger['amount']:,}円"
                )
                requests.post(DISCORD_WEBHOOK_URL, json={"content": signal_msg})

    # レポート送信
    requests.post(DISCORD_WEBHOOK_URL, json={"content": report_msg})

    # 高値更新等で書き換えが生じた場合のみgit push
    if file_changed and file_content:
        with open("monitor.py", "w", encoding="utf-8") as f:
            f.write(file_content)
        os.system('git config --global user.name "GitHub Actions"')
        os.system('git config --global user.email "actions@github.com"')
        os.system('git add monitor.py')
        os.system('git commit -m "🤖 自動更新：高値更新またはフラグ更新"')
        os.system('git push')

if __name__ == "__main__":
    main()
