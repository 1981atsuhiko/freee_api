# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request, redirect, render_template
from dotenv import load_dotenv
import os
import requests
import json
from datetime import datetime
from utils.db_utils import get_prefecture_name
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
# 従業員一覧からを取得
def employees_base():
    try:
        access_token = get_valid_access_token()
        freee_api = FreeeAPI(access_token)
        company_id = 10426042  # 取得した事業所IDを使用
        now = datetime.now()
        year = now.year
        month = now.month
        employees_data_base = freee_api.get_employees(company_id, year, month)
        #キーで検索して配列に詰めなおし
        filtered_employees_base = [{
            'id': emp['id'],
            'num': emp.get('num', 'N/A'),
            'entry_date': emp.get('entry_date', 'N/A'),
            'retire_date': emp.get('retire_date', None),
            'display_name': emp.get('display_name', 'N/A'),
            'name': f"{emp.get('profile_rule', {}).get('last_name', 'N/A')} {emp.get('profile_rule', {}).get('first_name', 'N/A')}",
            'name_kana': f"{emp.get('profile_rule', {}).get('last_name_kana', 'N/A')} {emp.get('profile_rule', {}).get('first_name_kana', 'N/A')}",
            'sex': '男性' if emp.get('profile_rule', {}).get('gender') == 'male' else '女性' if emp.get('profile_rule', {}).get('gender') == 'female' else 'N/A',
            'birth_date': emp.get('birth_date', 'N/A'),
            'age': calculate_age(emp.get('birth_date', 'N/A')),
            'zipcode':f"{emp.get('profile_rule', {}).get('zipcode1', 'N/A')} - {emp.get('profile_rule', {}).get('zipcode2', 'N/A')}",
            'prefecture': get_prefecture_name(emp.get('profile_rule', {}).get('prefecture_code', 0) + 1),
            'address': emp.get('profile_rule', {}).get('address', 'N/A'),
            'phone': f"{emp.get('profile_rule', {}).get('phone1', 'N/A')} - {emp.get('profile_rule', {}).get('phone2', 'N/A')} - {emp.get('profile_rule', {}).get('phone3', 'N/A')}",
            'married': '未婚' if emp.get('profile_rule', {}).get('married') == False else '既婚' if emp.get('profile_rule', {}).get('married') == True else 'N/A',
        } for emp in employees_data_base]
        return render_template('employees.html', employees_base=filtered_employees_base)
    except Exception as e:
        return str(e), 500
# 全期間従業員から取得
# 年齢を計算
def calculate_age(birth_date_str):
    if birth_date_str == 'N/A':
        return 'N/A'
    birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d')
    today = datetime.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age

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