from flask import Blueprint, redirect, request, render_template, current_app
import requests
import logging
from api.token_utils import save_tokens_to_db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    CLIENT_ID = current_app.config['CLIENT_ID']
    REDIRECT_URI = current_app.config['REDIRECT_URI']
    auth_code_url = f"https://accounts.secure.freee.co.jp/public_api/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=read"
    return redirect(auth_code_url)

@auth_bp.route('/callback')
def callback():
    CLIENT_ID = current_app.config['CLIENT_ID']
    CLIENT_SECRET = current_app.config['CLIENT_SECRET']
    REDIRECT_URI = current_app.config['REDIRECT_URI']
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
        logging.error(f"エラー: {response.status_code}")
        logging.error(error_info)
        return f"エラー: {response.status_code}", 500