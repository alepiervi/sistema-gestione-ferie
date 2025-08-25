#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Sistema Gestione Ferie e Permessi
Tests all endpoints with proper authentication and validation
"""

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional

class LeaveManagementAPITester:
    def __init__(self, base_url="https://workleave-portal.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.employee_token = None
        self.employee_id = None
        self.test_request_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.session = requests.Session()
        
        # Test credentials
        self.admin_creds = {"username": "admin", "password": "admin123"}
        self.employee_creds = {"username": "mario.rossi", "password": "password123"}
        
        print(f"🚀 Starting API tests for: {self.api_url}")
        print("=" * 60)

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data: Optional[Dict] = None, headers: Optional[Dict] = None, 
                 auth_token: Optional[str] = None) -> tuple[bool, Dict]:
        """Run a single API test with detailed logging"""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        
        # Setup headers
        test_headers = {'Content-Type': 'application/json'}
        if headers:
            test_headers.update(headers)
        if auth_token:
            test_headers['Authorization'] = f'Bearer {auth_token}'

        self.tests_run += 1
        print(f"\n🔍 Test {self.tests_run}: {name}")
        print(f"   {method} {url}")
        
        try:
            # Make request
            if method == 'GET':
                response = self.session.get(url, headers=test_headers)
            elif method == 'POST':
                response = self.session.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = self.session.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=test_headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            # Check status
            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"   ✅ PASSED - Status: {response.status_code}")
                
                # Try to parse JSON response
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(response_data) <= 3:
                        print(f"   📄 Response: {response_data}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"   ❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   📄 Error: {error_data}")
                    return False, error_data
                except:
                    print(f"   📄 Error: {response.text[:200]}")
                    return False, {}

        except Exception as e:
            print(f"   ❌ FAILED - Exception: {str(e)}")
            return False, {}

    def test_root_endpoint(self) -> bool:
        """Test API root endpoint"""
        success, response = self.run_test(
            "API Root Endpoint",
            "GET", 
            "/",
            200
        )
        return success

    def test_admin_login(self) -> bool:
        """Test admin login and store token"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "/login",
            200,
            data=self.admin_creds
        )
        
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            print(f"   🔑 Admin token acquired")
            return True
        return False

    def test_employee_login(self) -> bool:
        """Test employee login and store token"""
        success, response = self.run_test(
            "Employee Login",
            "POST",
            "/login",
            200,
            data=self.employee_creds
        )
        
        if success and 'access_token' in response:
            self.employee_token = response['access_token']
            print(f"   🔑 Employee token acquired")
            return True
        return False

    def test_invalid_login(self) -> bool:
        """Test login with invalid credentials"""
        success, response = self.run_test(
            "Invalid Login",
            "POST",
            "/login",
            401,
            data={"username": "invalid", "password": "wrong"}
        )
        return success

    def test_admin_dashboard_stats(self) -> bool:
        """Test admin dashboard statistics"""
        if not self.admin_token:
            print("   ⚠️  Skipped - No admin token")
            return False
            
        success, response = self.run_test(
            "Admin Dashboard Stats",
            "GET",
            "/admin/dashboard",
            200,
            auth_token=self.admin_token
        )
        
        if success:
            expected_keys = ['pending_ferie', 'pending_permessi', 'pending_malattie', 'total_pending']
            if all(key in response for key in expected_keys):
                print(f"   📊 Stats: Ferie:{response['pending_ferie']}, Permessi:{response['pending_permessi']}, Malattie:{response['pending_malattie']}")
                return True
        return False

    def test_get_employees(self) -> bool:
        """Test getting employee list (admin only)"""
        if not self.admin_token:
            print("   ⚠️  Skipped - No admin token")
            return False
            
        success, response = self.run_test(
            "Get Employees List",
            "GET",
            "/admin/employees",
            200,
            auth_token=self.admin_token
        )
        
        if success and isinstance(response, list):
            print(f"   👥 Found {len(response)} employees")
            return True
        return False

    def test_create_employee(self) -> bool:
        """Test creating a new employee"""
        if not self.admin_token:
            print("   ⚠️  Skipped - No admin token")
            return False
            
        # Create unique employee data
        timestamp = datetime.now().strftime("%H%M%S")
        employee_data = {
            "username": f"test_emp_{timestamp}",
            "email": f"test{timestamp}@company.com",
            "password": "testpass123"
        }
        
        success, response = self.run_test(
            "Create New Employee",
            "POST",
            "/admin/employees",
            200,
            data=employee_data,
            auth_token=self.admin_token
        )
        
        if success and 'employee_id' in response:
            self.employee_id = response['employee_id']
            print(f"   👤 Created employee: {employee_data['username']}")
            return True
        return False

    def test_create_duplicate_employee(self) -> bool:
        """Test creating employee with duplicate username"""
        if not self.admin_token:
            print("   ⚠️  Skipped - No admin token")
            return False
            
        duplicate_data = {
            "username": "admin",  # This should already exist
            "email": "duplicate@company.com",
            "password": "testpass123"
        }
        
        success, response = self.run_test(
            "Create Duplicate Employee",
            "POST",
            "/admin/employees",
            400,
            data=duplicate_data,
            auth_token=self.admin_token
        )
        return success

    def test_create_vacation_request(self) -> bool:
        """Test creating a vacation request (employee)"""
        if not self.employee_token:
            print("   ⚠️  Skipped - No employee token")
            return False
            
        # Create vacation request for next week
        start_date = (date.today() + timedelta(days=7)).isoformat()
        end_date = (date.today() + timedelta(days=10)).isoformat()
        
        request_data = {
            "type": "ferie",
            "start_date": start_date,
            "end_date": end_date
        }
        
        success, response = self.run_test(
            "Create Vacation Request",
            "POST",
            "/requests",
            200,
            data=request_data,
            auth_token=self.employee_token
        )
        
        if success and 'request_id' in response:
            self.test_request_id = response['request_id']
            print(f"   📅 Created vacation request: {start_date} to {end_date}")
            return True
        return False

    def test_create_permission_request(self) -> bool:
        """Test creating a permission request (employee)"""
        if not self.employee_token:
            print("   ⚠️  Skipped - No employee token")
            return False
            
        # Create permission request for tomorrow
        permit_date = (date.today() + timedelta(days=1)).isoformat()
        
        request_data = {
            "type": "permesso",
            "permit_date": permit_date,
            "start_time": "09:00",
            "end_time": "12:00"
        }
        
        success, response = self.run_test(
            "Create Permission Request",
            "POST",
            "/requests",
            200,
            data=request_data,
            auth_token=self.employee_token
        )
        
        if success:
            print(f"   🕒 Created permission request: {permit_date} 09:00-12:00")
            return True
        return False

    def test_create_sick_leave_request(self) -> bool:
        """Test creating a sick leave request (employee)"""
        if not self.employee_token:
            print("   ⚠️  Skipped - No employee token")
            return False
            
        # Create sick leave request
        sick_date = date.today().isoformat()
        
        request_data = {
            "type": "malattia",
            "sick_start_date": sick_date,
            "sick_days": 3,
            "protocol_code": f"PROT{datetime.now().strftime('%Y%m%d%H%M')}"
        }
        
        success, response = self.run_test(
            "Create Sick Leave Request",
            "POST",
            "/requests",
            200,
            data=request_data,
            auth_token=self.employee_token
        )
        
        if success:
            print(f"   🏥 Created sick leave: {sick_date} for 3 days")
            return True
        return False

    def test_invalid_vacation_request(self) -> bool:
        """Test creating invalid vacation request (too many days)"""
        if not self.employee_token:
            print("   ⚠️  Skipped - No employee token")
            return False
            
        # Create vacation request for more than 15 days
        start_date = (date.today() + timedelta(days=7)).isoformat()
        end_date = (date.today() + timedelta(days=25)).isoformat()  # 18 days
        
        request_data = {
            "type": "ferie",
            "start_date": start_date,
            "end_date": end_date
        }
        
        success, response = self.run_test(
            "Invalid Vacation Request (>15 days)",
            "POST",
            "/requests",
            422,  # Validation error
            data=request_data,
            auth_token=self.employee_token
        )
        return success

    def test_get_employee_requests(self) -> bool:
        """Test getting employee's own requests"""
        if not self.employee_token:
            print("   ⚠️  Skipped - No employee token")
            return False
            
        success, response = self.run_test(
            "Get Employee Requests",
            "GET",
            "/requests",
            200,
            auth_token=self.employee_token
        )
        
        if success and isinstance(response, list):
            print(f"   📋 Employee has {len(response)} requests")
            return True
        return False

    def test_get_all_requests_admin(self) -> bool:
        """Test getting all requests (admin view)"""
        if not self.admin_token:
            print("   ⚠️  Skipped - No admin token")
            return False
            
        success, response = self.run_test(
            "Get All Requests (Admin)",
            "GET",
            "/requests",
            200,
            auth_token=self.admin_token
        )
        
        if success and isinstance(response, list):
            print(f"   📋 Total requests in system: {len(response)}")
            return True
        return False

    def test_approve_request(self) -> bool:
        """Test approving a request (admin)"""
        if not self.admin_token or not self.test_request_id:
            print("   ⚠️  Skipped - No admin token or request ID")
            return False
            
        approval_data = {
            "request_id": self.test_request_id,
            "action": "approve",
            "notes": "Approved by automated test"
        }
        
        success, response = self.run_test(
            "Approve Request",
            "PUT",
            f"/admin/requests/{self.test_request_id}",
            200,
            data=approval_data,
            auth_token=self.admin_token
        )
        
        if success:
            print(f"   ✅ Approved request: {self.test_request_id}")
            return True
        return False

    def test_unauthorized_access(self) -> bool:
        """Test accessing admin endpoints without proper auth"""
        success, response = self.run_test(
            "Unauthorized Admin Access",
            "GET",
            "/admin/dashboard",
            401  # Unauthorized
        )
        return success

    def test_employee_cannot_access_admin(self) -> bool:
        """Test that employee cannot access admin endpoints"""
        if not self.employee_token:
            print("   ⚠️  Skipped - No employee token")
            return False
            
        success, response = self.run_test(
            "Employee Access Admin Endpoint",
            "GET",
            "/admin/dashboard",
            403,  # Forbidden
            auth_token=self.employee_token
        )
        return success

    def test_change_password(self) -> bool:
        """Test changing password"""
        if not self.admin_token:
            print("   ⚠️  Skipped - No admin token")
            return False
            
        password_data = {
            "current_password": "admin123",
            "new_password": "newadmin123"
        }
        
        success, response = self.run_test(
            "Change Admin Password",
            "PUT",
            "/change-password",
            200,
            data=password_data,
            auth_token=self.admin_token
        )
        
        # Change it back for other tests
        if success:
            revert_data = {
                "current_password": "newadmin123",
                "new_password": "admin123"
            }
            self.run_test(
                "Revert Admin Password",
                "PUT",
                "/change-password",
                200,
                data=revert_data,
                auth_token=self.admin_token
            )
        
        return success

    def run_all_tests(self) -> int:
        """Run all API tests in sequence"""
        print("🧪 BACKEND API TESTING SUITE")
        print("=" * 60)
        
        # Basic connectivity tests
        if not self.test_root_endpoint():
            print("❌ API root endpoint failed - stopping tests")
            return 1
            
        # Authentication tests
        if not self.test_admin_login():
            print("❌ Admin login failed - stopping tests")
            return 1
            
        if not self.test_employee_login():
            print("❌ Employee login failed - some tests will be skipped")
            
        self.test_invalid_login()
        
        # Admin functionality tests
        self.test_admin_dashboard_stats()
        self.test_get_employees()
        self.test_create_employee()
        self.test_create_duplicate_employee()
        
        # Employee functionality tests
        self.test_create_vacation_request()
        self.test_create_permission_request()
        self.test_create_sick_leave_request()
        self.test_invalid_vacation_request()
        
        # Request management tests
        self.test_get_employee_requests()
        self.test_get_all_requests_admin()
        self.test_approve_request()
        
        # Security tests
        self.test_unauthorized_access()
        self.test_employee_cannot_access_admin()
        
        # Settings tests
        self.test_change_password()
        
        # Print final results
        print("\n" + "=" * 60)
        print("📊 FINAL RESULTS")
        print("=" * 60)
        print(f"✅ Tests passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Tests failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"📈 Success rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED!")
            return 0
        else:
            print("⚠️  Some tests failed - check logs above")
            return 1

def main():
    """Main test runner"""
    tester = LeaveManagementAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())