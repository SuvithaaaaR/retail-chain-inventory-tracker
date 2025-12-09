"""
Test script to verify 3-role permission enforcement
Tests that staff role can only view, not modify
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import User
import json

def test_permissions():
    """Test permission enforcement for all 3 roles"""
    print("=" * 60)
    print("Testing 3-Role Permission Enforcement")
    print("=" * 60)
    
    with app.test_client() as client:
        # Test results
        results = {
            'admin': {'passed': 0, 'failed': 0},
            'manager': {'passed': 0, 'failed': 0},
            'staff': {'passed': 0, 'failed': 0}
        }
        
        # Define test cases
        test_cases = [
            {
                'role': 'admin',
                'username': 'admin',
                'password': 'admin123',
                'expected_permissions': ['products', 'inventory', 'reports', 'transactions', 'manage_users'],
                'should_succeed': {
                    'POST /api/products': True,
                    'PUT /api/products/1': True,
                    'DELETE /api/products/1': True,
                    'POST /api/inventory/update': True,
                    'POST /api/inventory/transfer': True,
                    'GET /api/reports/dashboard': True,
                    'GET /api/transactions': True,
                    'GET /api/users': True,
                }
            },
            {
                'role': 'manager',
                'username': 'manager',
                'password': 'manager123',
                'expected_permissions': ['products', 'inventory', 'reports', 'transactions'],
                'should_succeed': {
                    'POST /api/products': True,
                    'PUT /api/products/1': True,
                    'DELETE /api/products/1': False,  # Only admin can delete
                    'POST /api/inventory/update': True,
                    'POST /api/inventory/transfer': True,
                    'GET /api/reports/dashboard': True,
                    'GET /api/transactions': True,
                    'GET /api/users': False,  # Only admin
                }
            },
            {
                'role': 'staff',
                'username': 'staff',
                'password': 'staff123',
                'expected_permissions': ['inventory_view'],
                'should_succeed': {
                    'POST /api/products': False,
                    'PUT /api/products/1': False,
                    'DELETE /api/products/1': False,
                    'POST /api/inventory/update': False,
                    'POST /api/inventory/transfer': False,
                    'GET /api/reports/dashboard': False,
                    'GET /api/transactions': False,
                    'GET /api/users': False,
                }
            }
        ]
        
        for test_case in test_cases:
            role = test_case['role']
            print(f"\n{'=' * 60}")
            print(f"Testing {role.upper()} Role")
            print(f"{'=' * 60}")
            
            # Login
            login_response = client.post('/api/auth/login', 
                json={
                    'username': test_case['username'],
                    'password': test_case['password']
                })
            
            if login_response.status_code != 200:
                print(f"❌ Login failed for {role}")
                continue
            
            response_data = login_response.get_json()
            user_data = response_data.get('user', {})
            print(f"✓ Logged in as {role}")
            print(f"  Permissions: {', '.join(user_data.get('permissions', []))}")
            
            # Verify permissions match expected
            if set(user_data.get('permissions', [])) == set(test_case['expected_permissions']):
                print(f"✓ Permissions verified correctly")
                results[role]['passed'] += 1
            else:
                print(f"❌ Permission mismatch!")
                print(f"   Expected: {test_case['expected_permissions']}")
                print(f"   Got: {user_data.get('permissions', [])}")
                results[role]['failed'] += 1
            
            # Test each endpoint
            print(f"\nTesting API endpoints:")
            test_number = 0
            for endpoint, should_succeed in test_case['should_succeed'].items():
                test_number += 1
                method, path = endpoint.split(' ')
                
                # Prepare request data with unique identifiers per role
                data = None
                if method == 'POST' and '/products' in path:
                    data = {
                        'sku': f'TEST-{role.upper()}-{test_number}',
                        'name': f'Test Product {role}',
                        'category': 'Test'
                    }
                elif method == 'PUT' and '/products' in path:
                    data = {'name': f'Updated by {role}'}
                elif method == 'DELETE' and '/products' in path:
                    # Use a product ID that exists (2 or 3, since 1 might be modified)
                    path = '/api/products/2'
                elif method == 'POST' and '/inventory/update' in path:
                    data = {
                        'store_id': 1,
                        'product_id': 3,  # Use different product
                        'delta': 10,
                        'reason': f'Test by {role}'
                    }
                elif method == 'POST' and '/inventory/transfer' in path:
                    data = {
                        'from_store': 1,
                        'to_store': 2,
                        'product_id': 4,  # Use different product
                        'quantity': 5
                    }
                
                # Make request
                if method == 'GET':
                    response = client.get(path)
                elif method == 'POST':
                    response = client.post(path, json=data)
                elif method == 'PUT':
                    response = client.put(path, json=data)
                elif method == 'DELETE':
                    response = client.delete(path)
                
                # Check result
                success = response.status_code in [200, 201]
                forbidden = response.status_code == 403
                
                if should_succeed:
                    if success:
                        print(f"  ✓ {endpoint}: Allowed (as expected)")
                        results[role]['passed'] += 1
                    else:
                        print(f"  ❌ {endpoint}: Denied (should be allowed) - Status {response.status_code}")
                        results[role]['failed'] += 1
                else:
                    if forbidden or not success:
                        print(f"  ✓ {endpoint}: Denied (as expected)")
                        results[role]['passed'] += 1
                    else:
                        print(f"  ❌ {endpoint}: Allowed (should be denied) - Status {response.status_code}")
                        results[role]['failed'] += 1
            
            # Logout
            client.post('/api/auth/logout')
        
        # Summary
        print(f"\n{'=' * 60}")
        print("TEST SUMMARY")
        print(f"{'=' * 60}")
        
        total_passed = 0
        total_failed = 0
        
        for role, counts in results.items():
            passed = counts['passed']
            failed = counts['failed']
            total = passed + failed
            total_passed += passed
            total_failed += failed
            
            print(f"{role.upper()}: {passed}/{total} tests passed")
        
        print(f"\nOVERALL: {total_passed}/{total_passed + total_failed} tests passed")
        
        if total_failed == 0:
            print("\n✅ ALL TESTS PASSED - 3-Role permission system is fully enforced!")
        else:
            print(f"\n⚠️  {total_failed} tests failed - Review permission enforcement")

if __name__ == '__main__':
    test_permissions()
