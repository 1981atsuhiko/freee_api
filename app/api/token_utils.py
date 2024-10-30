import sqlite3
import requests
import os
from dotenv import load_dotenv
from flask import session

# .envファイルを読み込む
load_dotenv()

# 環境変数からクライアントID、クライアントシークレット、リダイレクトURIを取得
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

def get_tokens_from_db():
    conn = sqlite3.connect('tokens.db')
    c = conn.cursor()
    c.execute('SELECT access_token, refresh_token FROM tokens WHERE id=1')
    row = c.fetchone()
    conn.close()
    if row:
        return row[0], row[1]
    return None, None

def save_tokens_to_db(access_token, refresh_token):
    conn = sqlite3.connect('tokens.db')
    c = conn.cursor()
    c.execute('REPLACE INTO tokens (id, access_token, refresh_token) VALUES (1, ?, ?)', (access_token, refresh_token))
    conn.commit()
    conn.close()

def get_access_token():
    access_token, refresh_token = get_tokens_from_db()
    if not access_token or not refresh_token:
        raise Exception("アクセストークンまたはリフレッシュトークンがデータベースに存在しません。")

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    response = requests.post("https://accounts.secure.freee.co.jp/public_api/token", data=data)
    if response.status_code == 200:
        token_info = response.json()
        access_token = token_info["access_token"]
        refresh_token = token_info["refresh_token"]
        save_tokens_to_db(access_token, refresh_token)
        print(f"新しいアクセストークン: {access_token}")
        print(f"新しいリフレッシュトークン: {refresh_token}")
        return access_token
    else:
        error_info = response.json()
        print(f"エラー: {response.status_code}")
        print(error_info)
        return None

def get_valid_access_token():
    access_token, _ = get_tokens_from_db()
    if not access_token:
        access_token = get_access_token()
    return access_token

def is_logged_in():
    return 'freee_token' in session and session['freee_token'] is not None