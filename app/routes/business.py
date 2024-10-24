from flask import Blueprint, jsonify
import logging
from api.employee_api import FreeeAPI
from api.token_utils import get_valid_access_token

business_bp = Blueprint('business', __name__)

@business_bp.route('/business_id')
def business_id():
    try:
        access_token = get_valid_access_token()
        freee_api = FreeeAPI(access_token)
        user_info = freee_api.get_user_info()
        business_id = user_info['user']['companies'][0]['id']
        return jsonify({"business_id": business_id})
    except Exception as e:
        logging.error(f"エラーが発生しました: {str(e)}")
        return str(e), 500