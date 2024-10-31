from flask import Flask
from flask_session import Session
from dotenv import load_dotenv
import os

# .envファイルを読み込む
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.urandom(24)

    # 環境変数からクライアントID、クライアントシークレット、リダイレクトURIを取得
    app.config['CLIENT_ID'] = os.getenv("CLIENT_ID")
    app.config['CLIENT_SECRET'] = os.getenv("CLIENT_SECRET")
    app.config['REDIRECT_URI'] = os.getenv("REDIRECT_URI")

    # Flask-Sessionの設定
    app.config['SESSION_TYPE'] = 'filesystem'
    Session(app)

    # カスタムフィルタの定義
    def get_payment_amount(payments, name):
        for payment in payments:
            if payment['name'] == name:
                return int(float(payment['amount']))
        return 'N/A'

    def get_overtime_details(overtime_pays, name):
        for item in overtime_pays:
            if item['name'] == name:
                # 分を時間に変換し、小数点第2位までにフォーマット
                time_in_minutes = item['time'] if item['time'] is not None else 0
                hours = float(time_in_minutes) / 60
                formatted_hours = "{:.2f}".format(hours)
                return {
                    'time': formatted_hours,
                    'amount': int(float(item['amount']))
                }
        return {'time': 'N/A', 'amount': 'N/A'}

    def get_custom_field_value(custom_fields, field_name):
        for group in custom_fields.get('profile_custom_field_groups', []):
            for field in group.get('profile_custom_field_rules', []):
                if field['name'] == field_name:
                    result = {
                        'value': field['value'],
                        'name': field['file_name'],
                        'id': field['id']
                    }
                    if 'file_name' in field and field['file_name'] not in [None, 'N/A'] and '.pdf' in field['file_name']:
                        result['fileType'] = 'pdf'
                    return result
        return 'N/A'

    app.jinja_env.filters['get_payment_amount'] = get_payment_amount
    app.jinja_env.filters['get_overtime_details'] = get_overtime_details
    app.jinja_env.filters['get_custom_field_value'] = get_custom_field_value

    # Blueprintの登録
    from routes.home import home_bp
    from routes.auth import auth_bp
    from routes.employees import employees_bp
    from routes.business import business_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(business_bp)

    return app