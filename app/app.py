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
def employees():
    try:
        access_token = get_valid_access_token()
        freee_api = FreeeAPI(access_token)
        company_id = 10426042  # 取得した事業所IDを使用
        now = datetime.now()
        year = now.year
        month = now.month
        base_date = now.strftime('%Y-%m-%d')

        # employees_base を取得
        employees_data_base = freee_api.get_employees(company_id, year, month)
        filtered_employees_base = [{
            'id': employee['id'],
            'num': employee.get('num', 'N/A'),
            'entry_date': employee.get('entry_date', 'N/A'),
            'retire_date': employee.get('retire_date', 'N/A'),
            'display_name': employee.get('display_name', 'N/A'),
            'name': f"{employee.get('profile_rule', {}).get('last_name', 'N/A')} {employee.get('profile_rule', {}).get('first_name', 'N/A')}",
            'name_kana': f"{employee.get('profile_rule', {}).get('last_name_kana', 'N/A')} {employee.get('profile_rule', {}).get('first_name_kana', 'N/A')}",
            'sex': '男性' if employee.get('profile_rule', {}).get('gender') == 'male' else '女性' if employee.get('profile_rule', {}).get('gender') == 'female' else 'N/A',
            'birth_date': employee.get('birth_date', 'N/A'),
            'age': calculate_age(employee.get('birth_date', 'N/A')),
            'zipcode': f"{employee.get('profile_rule', {}).get('zipcode1', 'N/A')} - {employee.get('profile_rule', {}).get('zipcode2', 'N/A')}",
            'prefecture': get_prefecture_name(employee.get('profile_rule', {}).get('prefecture_code', 0) + 1),
            'address': employee.get('profile_rule', {}).get('address', 'N/A'),
            'out_email': employee.get('profile_rule', {}).get('email', 'N/A'),
            'phone': f"{employee.get('profile_rule', {}).get('phone1', 'N/A')} - {employee.get('profile_rule', {}).get('phone2', 'N/A')} - {employee.get('profile_rule', {}).get('phone3', 'N/A')}",
            'married': '未婚' if employee.get('profile_rule', {}).get('married') == False else '既婚' if employee.get('profile_rule', {}).get('married') == True else 'N/A',
        } for employee in employees_data_base]

        # all_employees を取得
        employees_data_all = freee_api.get_all_employees(company_id)
        filtered_employees_all = [{
            'num': employee.get('num', 'N/A'),
            'out_display_name': employee.get('display_name', 'N/A'),
            'email': employee.get('email', 'N/A'),
            'retire_date': employee.get('retire_date', None),
            'retire_status': '退職' if employee.get('retire_date') else None
        } for employee in employees_data_all]

        # employee_group_memberships を取得
        memberships_data = freee_api.get_employee_group_memberships(company_id, base_date)
        memberships_dict = {}
        for membership in memberships_data:
            num = membership.get('num', 'N/A')
            group_memberships = membership.get('group_memberships', [])
            if num not in memberships_dict:
                memberships_dict[num] = []
            for group in group_memberships:
                memberships_dict[num].append({
                    'group_id': group.get('group_id', 'N/A'),
                    'group_code': group.get('group_code', 'N/A'),
                    'group_name': group.get('group_name', 'N/A')
                })

        # num を主キーとして結合
        employees_dict = {employee['num']: employee for employee in filtered_employees_base}
        for employee in filtered_employees_all:
            if employee['num'] in employees_dict:
                employees_dict[employee['num']]['retire_status'] = employee['retire_status']
                employees_dict[employee['num']]['email'] = employee['email']
            else:
                employees_dict[employee['num']] = employee

        # 所属情報を結合
        for employee in employees_dict.values():
            num = employee['num']
            if num in memberships_dict:
                employee['group_memberships'] = memberships_dict[num]
            else:
                employee['group_memberships'] = [{
                    'group_id': 'N/A',
                    'group_code': 'N/A',
                    'group_name': 'N/A'
                }]

        # 結合したデータをリストに変換し、numの昇順で並び替え
        merged_employees = sorted(employees_dict.values(), key=lambda x: x['num'])
        print(merged_employees)
        return render_template('employees.html', employees=merged_employees)
    except Exception as e:
        return str(e), 500

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