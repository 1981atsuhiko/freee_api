import requests
import logging

# ログの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FreeeAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.freee.co.jp/hr/api/v1"

    def log_rate_limit_info(self, response):
        limit = int(response.headers.get('X-RateLimit-Limit', 0))
        remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
        reset = response.headers.get('X-RateLimit-Reset')
        remaining_requests = limit - remaining
        logging.info(f"Rate Limit: {limit}, Remaining: {remaining}, Reset: {reset}")

    def get_employees(self, company_id, year, month, with_no_payroll_calculation=True):
        url = f"{self.base_url}/employees"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "FREEE-VERSION": "2022-02-01"
        }
        all_employees = []
        offset = 0
        limit = 50

        while True:
            params = {
                "company_id": company_id,
                "year": year,
                "month": month,
                "limit": limit,
                "offset": offset,
                "with_no_payroll_calculation": str(with_no_payroll_calculation).lower()
            }
            response = requests.get(url, headers=headers, params=params)
            self.log_rate_limit_info(response)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    employees = data
                else:
                    employees = data.get('employees', [])
                all_employees.extend(employees)
                if len(employees) < limit:
                    break
                offset += limit
            else:
                logging.error(f"Error: {response.status_code} - {response.text}")
                response.raise_for_status()

        return all_employees

    def get_all_employees(self, company_id, limit=100, with_no_payroll_calculation=True):
        url = f"{self.base_url}/companies/{company_id}/employees"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "accept": "application/json",
            "FREEE-VERSION": "2022-02-01"
        }
        all_employees = []
        offset = 0

        while True:
            params = {
                "limit": limit,
                "offset": offset,
                "with_no_payroll_calculation": str(with_no_payroll_calculation).lower()
            }
            response = requests.get(url, headers=headers, params=params)
            self.log_rate_limit_info(response)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    employees = data
                else:
                    employees = data.get('employees', [])
                all_employees.extend(employees)
                if len(employees) < limit:
                    break
                offset += limit
            else:
                logging.error(f"Error: {response.status_code} - {response.text}")
                response.raise_for_status()

        return all_employees

    def get_employee_group_memberships(self, company_id, base_date, limit=100, offset=0):
        url = f"{self.base_url}/employee_group_memberships"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "accept": "application/json",
            "FREEE-VERSION": "2022-02-01"
        }
        all_memberships = []

        while True:
            params = {
                "company_id": company_id,
                "base_date": base_date,
                "limit": limit,
                "offset": offset,
                "with_no_payroll_calculation": "true"
            }
            response = requests.get(url, headers=headers, params=params)
            self.log_rate_limit_info(response)
            if response.status_code == 200:
                data = response.json()
                memberships = data.get('employee_group_memberships', [])
                all_memberships.extend(memberships)
                if len(memberships) < limit:
                    break
                offset += limit
            else:
                logging.error(f"Error: {response.status_code} - {response.text}")
                response.raise_for_status()

        return all_memberships

    def get_employee_payroll_statements(self, company_id, year, month, limit=100, offset=0):
        url = f"{self.base_url}/salaries/employee_payroll_statements"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "accept": "application/json",
            "FREEE-VERSION": "2022-02-01"
        }
        all_statements = []

        while True:
            params = {
                "company_id": company_id,
                "year": year,
                "month": month,
                "limit": limit,
                "offset": offset
            }
            response = requests.get(url, headers=headers, params=params)
            self.log_rate_limit_info(response)
            if response.status_code == 200:
                data = response.json()
                statements = data.get('employee_payroll_statements', [])
                all_statements.extend(statements)
                if len(statements) < limit:
                    break
                offset += limit
            else:
                logging.error(f"Error: {response.status_code} - {response.text}")
                response.raise_for_status()

        return all_statements

    def get_employee_profile_custom_fields(self, company_id, employee_id, year, month):
        url = f"{self.base_url}/employees/{employee_id}/profile_custom_fields"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "accept": "application/json",
            "FREEE-VERSION": "2022-02-01"
        }
        params = {
            "company_id": company_id,
            "year": year,
            "month": month - 1
        }
        response = requests.get(url, headers=headers, params=params)
        self.log_rate_limit_info(response)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Error: {response.status_code} - {response.text}")
            response.raise_for_status()

    def get_user_info(self):
        url = "https://api.freee.co.jp/api/1/users/me"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "FREEE-VERSION": "2022-02-01"
        }
        response = requests.get(url, headers=headers)
        self.log_rate_limit_info(response)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Error: {response.status_code} - {response.text}")
            response.raise_for_status()