# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request, redirect, render_template
from dotenv import load_dotenv
import os
import requests
import json
from api.employee_api import FreeeAPI

# .envファイルを読み込む
load_dotenv()

app = Flask(__name__)

# 環境変数からクライアントID、クライアントシークレット、リダイレクトURI、アクセストークン、リフレッシュトークンを取得
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
API_KEY = os.getenv("API_KEY")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")

freee_api = FreeeAPI(API_KEY)

def refresh_access_token(refresh_token):
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
        # 新しいアクセストークンを環境変数に設定
        os.environ["API_KEY"] = access_token
        print(f"新しいアクセストークン: {access_token}")
        return access_token
    else:
        error_info = response.json()
        print(f"エラー: {response.status_code}")
        print(error_info)
        return None

@app.route('/')
def home():
    return 'Hello, Flask!'

@app.route('/login')
def login():
    auth_code_url = f"https://accounts.secure.freee.co.jp/public_api/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=read"
    return redirect(auth_code_url)

@app.route('/callback')
def callback():
    auth_code = request.args.get('code')
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    response = requests.post("https://accounts.secure.freee.co.jp/public_api/token", data=data)
    if response.status_code == 200:
        token_info = response.json()
        access_token = token_info["access_token"]
        refresh_token = token_info["refresh_token"]
        # アクセストークンとリフレッシュトークンを環境変数に保存
        os.environ["API_KEY"] = access_token
        os.environ["REFRESH_TOKEN"] = refresh_token
        return f"アクセストークン: {access_token}<br>リフレッシュトークン: {refresh_token}"
    else:
        return f"エラー: {response.status_code}", 500

@app.route('/employees')
def employees():
    try:
        company_id = 10426042  # 取得した事業所IDを使用
        year = 2024
        month = 1
        employees_data = freee_api.get_employees(company_id, year, month)
        # JSONデータをデコード
        decoded_employees = json.loads(json.dumps(employees_data['employees'], ensure_ascii=False))
        return render_template('employees.html', employees=decoded_employees)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            # アクセストークンが無効な場合、リフレッシュトークンを使用して新しいアクセストークンを取得
            app.logger.info("アクセストークンが無効です。リフレッシュトークンを使用して新しいアクセストークンを取得します。")
            new_access_token = refresh_access_token(REFRESH_TOKEN)
            if new_access_token:
                freee_api.api_key = new_access_token
                employees_data = freee_api.get_employees(company_id, year, month)
                decoded_employees = json.loads(json.dumps(employees_data['employees'], ensure_ascii=False))
                return render_template('employees.html', employees=decoded_employees)
            else:
                app.logger.error("アクセストークンの再取得に失敗しました。")
                return "アクセストークンの再取得に失敗しました。", 500
        else:
            app.logger.error(f"HTTPエラーが発生しました: {e}")
            return str(e), 500

@app.route('/business_id')
def business_id():
    try:
        user_info = freee_api.get_user_info()
        business_id = user_info['user']['companies'][0]['id']
        return jsonify({"business_id": business_id})
    except requests.exceptions.HTTPError as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True)