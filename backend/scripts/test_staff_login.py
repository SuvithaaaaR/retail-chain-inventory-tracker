"""
Quick test to verify staff user can login and see correct permissions
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import User

def test_staff_user():
    print("=" * 60)
    print("Testing Staff User Login & Permissions")
    print("=" * 60)
    
    with app.app_context():
        # Check if staff user exists in database
        staff_user = User.query.filter_by(username='staff').first()
        
        if not staff_user:
            print("❌ ERROR: Staff user not found in database!")
            print("   Run 'python init_db.py' to create users")
            return
        
        print(f"\n✓ Staff user exists in database")
        print(f"  Username: {staff_user.username}")
        print(f"  Role: {staff_user.role}")
        print(f"  Permissions (raw): {staff_user.permissions}")
        print(f"  Permissions (parsed): {staff_user.get_permissions()}")
        
        # Test password
        if staff_user.check_password('staff123'):
            print(f"\n✓ Password verification works")
        else:
            print(f"\n❌ ERROR: Password 'staff123' does not match!")
            return
        
        # Test API login
        print(f"\n{'=' * 60}")
        print("Testing API Login")
        print(f"{'=' * 60}")
        
        with app.test_client() as client:
            response = client.post('/api/auth/login',
                json={'username': 'staff', 'password': 'staff123'},
                content_type='application/json')
            
            print(f"\nStatus Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_json()
                print(f"✓ Login successful!")
                print(f"\nResponse data:")
                print(f"  Message: {data.get('message')}")
                
                user_data = data.get('user', {})
                print(f"\nUser object:")
                print(f"  ID: {user_data.get('id')}")
                print(f"  Username: {user_data.get('username')}")
                print(f"  Role: {user_data.get('role')}")
                print(f"  Permissions: {user_data.get('permissions')}")
                
                # Verify permissions
                expected_perms = ['inventory_view']
                actual_perms = user_data.get('permissions', [])
                
                if set(actual_perms) == set(expected_perms):
                    print(f"\n✅ Permissions are CORRECT!")
                else:
                    print(f"\n❌ Permission mismatch!")
                    print(f"   Expected: {expected_perms}")
                    print(f"   Got: {actual_perms}")
                
                # Test accessing a restricted endpoint
                print(f"\n{'=' * 60}")
                print("Testing Restricted Access (should be denied)")
                print(f"{'=' * 60}")
                
                test_endpoints = [
                    ('GET', '/api/reports/dashboard', 'reports'),
                    ('GET', '/api/transactions', 'transactions'),
                    ('POST', '/api/products', 'products'),
                    ('POST', '/api/inventory/update', 'inventory'),
                    ('GET', '/api/users', 'manage_users'),
                ]
                
                for method, endpoint, permission in test_endpoints:
                    if method == 'GET':
                        resp = client.get(endpoint)
                    elif method == 'POST':
                        resp = client.post(endpoint, json={})
                    
                    if resp.status_code == 403:
                        print(f"  ✓ {method} {endpoint} → 403 Forbidden (correct)")
                    else:
                        print(f"  ❌ {method} {endpoint} → {resp.status_code} (should be 403)")
                
                # Test accessing allowed endpoint
                print(f"\n{'=' * 60}")
                print("Testing Allowed Access (should work)")
                print(f"{'=' * 60}")
                
                resp = client.get('/api/inventory?store_id=1')
                if resp.status_code == 200:
                    print(f"  ✓ GET /api/inventory → 200 OK (correct)")
                else:
                    print(f"  ❌ GET /api/inventory → {resp.status_code} (should be 200)")
                
            else:
                print(f"❌ Login failed!")
                error_data = response.get_json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
                print(f"\nFull response: {error_data}")

if __name__ == '__main__':
    test_staff_user()
