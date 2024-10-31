from flask import Blueprint, render_template, request, current_app
import logging
import asyncio
from datetime import datetime
from api.employee_api import FreeeAPI
from api.token_utils import get_valid_access_token
from utils.db_utils import get_prefecture_name
employees_bp = Blueprint('employees', __name__)

@employees_bp.route('/employees', methods=['GET'])
def employees():
    try:
        # GETリクエストの値をログで出力
        logging.info(f"GET parameters: {request.args}")

        access_token = get_valid_access_token()
        freee_api = FreeeAPI(access_token)
        company_id = 10426042  # 取得した事業所IDを使用

        # 選択された年月を取得
        selected_month = request.args.get('month')
        if selected_month:
            year, month = map(int, selected_month.split('/'))
        else:
            now = datetime.now()
            year = now.year
            month = now.month

        base_date = datetime(year, month, 1).strftime('%Y-%m-%d')

        # ログ出力
        logging.info(f"Selected year: {year}, Selected month: {month}")

        async def fetch_data():
            logging.info(f"Fetching data for year: {year}, month: {month}")
            employees_data_base = await freee_api.get_employees(company_id, year, month)
            employees_data_all = await freee_api.get_all_employees(company_id, year, month)  # yearとmonthを追加
            memberships_data = await freee_api.get_employee_group_memberships(company_id, base_date)
            payroll_statements = await freee_api.get_employee_payroll_statements(company_id, year, month)

            return employees_data_base, employees_data_all, memberships_data, payroll_statements

        employees_data_base, employees_data_all, memberships_data, payroll_statements = asyncio.run(fetch_data())

        filtered_employees_base = []
        for employee in employees_data_base:
            entry_date = employee.get('entry_date', 'N/A')
            retire_date = employee.get('retire_date', 'N/A')
            if entry_date == 'N/A' and retire_date == 'N/A':
                continue  # entry_dateとretire_dateの両方がN/Aの場合はスキップ

            filtered_employees_base.append({
                'id': employee['id'],
                'num': employee.get('num', 'N/A'),
                'entry_date': entry_date,
                'retire_date': retire_date,
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
            })

        filtered_employees_all = [{
            'id': employee['id'],
            'num': employee.get('num', 'N/A'),
            'out_display_name': employee.get('display_name', 'N/A'),
            'email': employee.get('email', 'N/A'),
            'retire_date': employee.get('retire_date', None),
            'retire_status': '退職' if employee.get('retire_date') else None
        } for employee in employees_data_all]

        memberships_dict = {}
        for membership in memberships_data:
            id = membership.get('id', 'N/A')
            group_memberships = membership.get('group_memberships', [])
            if id not in memberships_dict:
                memberships_dict[id] = []
            for group in group_memberships:
                memberships_dict[id].append({
                    'group_id': group.get('group_id', 'N/A'),
                    'group_code': group.get('group_code', 'N/A'),
                    'group_name': group.get('group_name', 'N/A')
                })

        employees_dict = {employee['id']: employee for employee in filtered_employees_base}
        for employee in filtered_employees_all:
            if employee['id'] in employees_dict:
                employees_dict[employee['id']]['retire_status'] = employee['retire_status']
                employees_dict[employee['id']]['email'] = employee['email']
            else:
                employees_dict[employee['id']] = employee

        for employee in employees_dict.values():
            id = employee['id']
            if id in memberships_dict:
                employee['group_memberships'] = memberships_dict[id]
            else:
                employee['group_memberships'] = [{
                    'group_id': 'N/A',
                    'group_code': 'N/A',
                    'group_name': 'N/A'
                }]

        payroll_dict = {statement['employee_num']: statement for statement in payroll_statements}
        for employee in employees_dict.values():
            num = employee['num']
            if num in payroll_dict:
                payroll = payroll_dict[num]
                employee['payroll'] = {
                    'employee_num': payroll.get('employee_num', 'N/A'),
                    'gross_payment_amount': int(float(payroll.get('gross_payment_amount', 'N/A'))),
                    'payments': payroll.get('payments', []),
                    'overtime_pays': payroll.get('overtime_pays', [])
                }
            else:
                employee['payroll'] = None

        async def fetch_custom_fields():
            tasks = []
            for employee in employees_dict.values():
                employee_id = employee['id']
                tasks.append(freee_api.get_employee_profile_custom_fields(company_id, employee_id, year, month))
            return await asyncio.gather(*tasks)

        custom_fields_list = asyncio.run(fetch_custom_fields())
        for employee, custom_fields in zip(employees_dict.values(), custom_fields_list):
            employee['custom_fields'] = custom_fields
        merged_employees = sorted(employees_dict.values(), key=lambda x: x['num'])
        return render_template('employees.html', employees=merged_employees)
    except Exception as e:
        logging.error(f"エラーが発生しました: {str(e)}")
        return str(e), 500

def calculate_age(birth_date_str):
    if birth_date_str == 'N/A':
        return 'N/A'
    birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d')
    today = datetime.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age