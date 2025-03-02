import time
import re
import csv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

# 検索クエリ
SEARCH_QUERY = "instagram " + os.getenv('SEARCH_WORD') + " site:instagram.com"
SEARCH_ENGINE_URL = f"https://www.bing.com/search?q={SEARCH_QUERY}&count=50"
CSV_FILE = "instagram_accounts.csv"

# Seleniumの設定
options = Options()
options.add_argument("--headless")
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# Chrome WebDriverのセットアップ
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)


def get_all_instagram_links():
    """Bing検索でInstagramのリンクをすべて取得"""
    driver.get(SEARCH_ENGINE_URL)
    time.sleep(5)

    all_links = set()
    page = 1

    while True:
        print(f"🔍 {page} ページ目を処理中...")
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # 検索結果のリンクを取得
        for a in soup.select("li.b_algo h2 a"):
            href = a.get("href")
            if "instagram.com" in href:
                all_links.add(href)

        # 次のページがあるかチェック
        next_page = driver.find_elements("css selector", "a.sb_pagN")
        if next_page:
            next_page[0].click()
            time.sleep(5)
            page += 1
        else:
            break

    return list(all_links)


def extract_username(instagram_url):
    """InstagramのURLからアカウント名を抽出"""
    match = re.match(r"https://www\.instagram\.com/([\w.-]+)/", instagram_url)
    return match.group(1) if match else None


def load_existing_usernames():
    """既存のCSVからアカウント名を読み込む"""
    existing_usernames = set()

    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader, None)  # ヘッダーをスキップ
            for row in reader:
                if row:
                    existing_usernames.add(row[0])  # username列を追加

    return existing_usernames


def save_to_csv(usernames):
    """アカウント名をCSVに保存（初回でも重複を排除）"""
    existing_usernames = load_existing_usernames()

    # **取得したデータ自体の重複を除外**
    unique_usernames = set(usernames)

    # **既存のCSVのデータと比較して新規アカウントのみ保存**
    new_usernames = unique_usernames - existing_usernames

    if not new_usernames:
        print("✅ 新規のアカウントはありません。")
        return

    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if not file_exists:  # 初回作成時にヘッダー追加
            writer.writerow(["username"])
        for username in new_usernames:
            writer.writerow([username])

    print(f"📁 {len(new_usernames)} 件の新規アカウントをCSVに追加しました。")


# メイン処理
if __name__ == "__main__":
    print("🔍 BingでInstagramのグルメアカウントを検索中...")
    links = get_all_instagram_links()

    if not links:
        print("⚠ Instagramのリンクが見つかりませんでした。")
    else:
        print(f"✅ {len(links)} 件のInstagramリンクを取得。")

    usernames = set()

    for link in links:
        username = extract_username(link)
        if username:
            print(f"✔ アカウント取得成功: {username}")
            usernames.add(username)
        else:
            print(f"❌ アカウント名の取得に失敗: {link}")

    if usernames:
        save_to_csv(usernames)

    driver.quit()
