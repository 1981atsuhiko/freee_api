import aiohttp
import asyncio
import logging

# ログの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FreeeAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.freee.co.jp/hr/api/v1"

    async def log_rate_limit_info(self, response):
        limit = int(response.headers.get('X-RateLimit-Limit', 0))
        remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
        reset = response.headers.get('X-RateLimit-Reset')
        remaining_requests = limit - remaining
        logging.info(f"Rate Limit: {limit}, Remaining: {remaining}, Reset: {reset}")

    async def fetch(self, session, url, params):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "FREEE-VERSION": "2022-02-01"
        }
        async with session.get(url, headers=headers, params=params) as response:
            await self.log_rate_limit_info(response)
            response.raise_for_status()
            return await response.json()

    async def get_employees(self, company_id, year, month, with_no_payroll_calculation=True):
        url = f"{self.base_url}/employees"
        all_employees = []
        offset = 0
        limit = 50

        async with aiohttp.ClientSession() as session:
            while True:
                params = {
                    "company_id": company_id,
                    "year": year,
                    "month": month,
                    "limit": limit,
                    "offset": offset,
                    "with_no_payroll_calculation": str(with_no_payroll_calculation).lower()
                }
                data = await self.fetch(session, url, params)
                if isinstance(data, list):
                    employees = data
                else:
                    employees = data.get('employees', [])
                all_employees.extend(employees)
                if len(employees) < limit:
                    break
                offset += limit

        return all_employees

    async def get_all_employees(self, company_id, limit=100, with_no_payroll_calculation=True):
        url = f"{self.base_url}/companies/{company_id}/employees"
        all_employees = []
        offset = 0

        async with aiohttp.ClientSession() as session:
            while True:
                params = {
                    "limit": limit,
                    "offset": offset,
                    "with_no_payroll_calculation": str(with_no_payroll_calculation).lower()
                }
                data = await self.fetch(session, url, params)
                if isinstance(data, list):
                    employees = data
                else:
                    employees = data.get('employees', [])
                all_employees.extend(employees)
                if len(employees) < limit:
                    break
                offset += limit

        return all_employees

    async def get_employee_group_memberships(self, company_id, base_date, limit=100, offset=0):
        url = f"{self.base_url}/employee_group_memberships"
        all_memberships = []

        async with aiohttp.ClientSession() as session:
            while True:
                params = {
                    "company_id": company_id,
                    "base_date": base_date,
                    "limit": limit,
                    "offset": offset,
                    "with_no_payroll_calculation": "true"
                }
                data = await self.fetch(session, url, params)
                if isinstance(data, list):
                    memberships = data
                else:
                    memberships = data.get('employee_group_memberships', [])
                all_memberships.extend(memberships)
                if len(memberships) < limit:
                    break
                offset += limit

        return all_memberships

    async def get_employee_payroll_statements(self, company_id, year, month, limit=100, offset=0):
        url = f"{self.base_url}/salaries/employee_payroll_statements"
        all_statements = []

        async with aiohttp.ClientSession() as session:
            while True:
                params = {
                    "company_id": company_id,
                    "year": year,
                    "month": month,
                    "limit": limit,
                    "offset": offset
                }
                data = await self.fetch(session, url, params)
                if isinstance(data, list):
                    statements = data
                else:
                    statements = data.get('employee_payroll_statements', [])
                all_statements.extend(statements)
                if len(statements) < limit:
                    break
                offset += limit

        return all_statements

    async def get_employee_profile_custom_fields(self, company_id, employee_id, year, month):
        url = f"{self.base_url}/employees/{employee_id}/profile_custom_fields"
        params = {
            "company_id": company_id,
            "year": year,
            "month": month - 1
        }

        async with aiohttp.ClientSession() as session:
            data = await self.fetch(session, url, params)
            return data

    async def get_user_info(self):
        url = "https://api.freee.co.jp/api/1/users/me"
        async with aiohttp.ClientSession() as session:
            data = await self.fetch(session, url, {})
            return data