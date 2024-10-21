# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request, redirect, render_template
from dotenv import load_dotenv
import os
import requests
import json
from datetime import datetime
from api.employee_api import FreeeAPI
from api.token_utils import get_valid_access_token, save_tokens_to_db

# .envファイルを読み込む
load_dotenv()

app = Flask(__name__)

# 環境変数からクライアントID、クライアントシークレット、リダイレクトURIを取得
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

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
        save_tokens_to_db(access_token, refresh_token)
        return render_template('callback.html')
    else:
        error_info = response.json()
        print(f"エラー: {response.status_code}")
        print(error_info)
        return f"エラー: {response.status_code}", 500

@app.route('/employees')
def employees():
    try:
        access_token = get_valid_access_token()
        freee_api = FreeeAPI(access_token)
        company_id = 10426042  # 取得した事業所IDを使用
        now = datetime.now()
        year = now.year
        month = now.month
        employees_data = freee_api.get_employees(company_id, year, month)
        # 必要な情報だけを抽出
        filtered_employees = [{
            'id': emp['id'], 
            'num': emp.get('num', 'N/A'), 
            'display_name': emp.get('display_name', 'N/A')
        } for emp in employees_data]
        return render_template('employees.html', employees=filtered_employees)
    except Exception as e:
        return str(e), 500

@app.route('/business_id')
def business_id():
    try:
        access_token = get_valid_access_token()
        freee_api = FreeeAPI(access_token)
        user_info = freee_api.get_user_info()
        business_id = user_info['user']['companies'][0]['id']
        return jsonify({"business_id": business_id})
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True)