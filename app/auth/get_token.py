# app/auth/get_token.py
import requests
import os
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

# 環境変数からクライアントIDとクライアントシークレットを取得
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

# 認証用URL
AUTH_URL = "https://accounts.secure.freee.co.jp/public_api/token"

def get_access_token():
    # 認証コードを取得するためのURL
    auth_code_url = f"https://accounts.secure.freee.co.jp/public_api/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=read"
    print(f"以下のURLにアクセスして認証コードを取得してください:\n{auth_code_url}")

    # ユーザーに認証コードを入力させる
    auth_code = input("認証コードを入力してください: ")

    # アクセストークンを取得するためのデータ
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }

    # アクセストークンを取得
    response = requests.post(AUTH_URL, data=data)
    if response.status_code == 200:
        token_info = response.json()
        access_token = token_info["access_token"]
        refresh_token = token_info["refresh_token"]
        print(f"アクセストークン: {access_token}")
        print(f"リフレッシュトークン: {refresh_token}")
        return access_token, refresh_token
    else:
        print(f"エラー: {response.status_code}")
        print(response.json())

if __name__ == "__main__":
    get_access_token()