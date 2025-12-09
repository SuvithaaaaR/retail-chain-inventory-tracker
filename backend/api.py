"""
API Blueprint

This module defines all REST API endpoints for the Retail Chain Inventory Tracker.
Handles authentication, inventory operations, and reporting endpoints.
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime
from services.inventory_service import InventoryService
from models import db, User, Store, Product, InventoryItem, Transaction

api = Blueprint('api', __name__, url_prefix='/api')


def require_auth():
    """Decorator to require authentication for API endpoints"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    return None


def require_admin():
    """Require the current session user to be an admin"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    if session.get('role') != 'admin':
        return jsonify({'error': 'Admin privileges required'}), 403
    return None


@api.route('/auth/login', methods=['POST'])
def login():
    """Authenticate user and create session"""
    try:
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Username and password required'}), 400
        
        user = User.query.filter_by(username=data['username']).first()
        if user and user.check_password(data['password']):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return jsonify({
                'message': 'Login successful',
                'user': user.to_dict()
            })
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/auth/logout', methods=['POST'])
def logout():
    """Clear user session"""
    session.clear()
    return jsonify({'message': 'Logout successful'})


@api.route('/auth/status', methods=['GET'])
def auth_status():
    """Get current authentication status"""
    if 'user_id' in session:
        try:
            user = User.query.get(session['user_id'])
            return jsonify({
                'authenticated': True,
                'user': user.to_dict() if user else {
                    'user_id': session['user_id'],
                    'username': session.get('username'),
                    'role': session.get('role')
                }
            })
        except Exception:
            return jsonify({'authenticated': True, 'user_id': session['user_id']})
    else:
        return jsonify({'authenticated': False})


@api.route('/stores', methods=['GET'])
def get_stores():
    """Get all stores"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    try:
        service = InventoryService(user_id=session['user_id'])
        stores = service.get_stores()
        return jsonify([store.to_dict() for store in stores])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/users', methods=['GET'])
def list_users():
    """List all users (admin only)"""
    admin_error = require_admin()
    if admin_error:
        return admin_error

    try:
        users = User.query.all()
        return jsonify([u.to_dict() for u in users])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/users/<int:user_id>/permissions', methods=['PUT'])
def update_user_permissions(user_id):
    """Update a user's permissions (admin only)

    Request JSON: { 'permissions': ['products','inventory'] }
    """
    admin_error = require_admin()
    if admin_error:
        return admin_error

    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()
        if not data or 'permissions' not in data:
            return jsonify({'error': 'permissions field required'}), 400

        perms = data.get('permissions')
        user.set_permissions(perms)
        db.session.commit()
        return jsonify(user.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api.route('/products', methods=['GET', 'POST'])
def handle_products():
    """Get all products or create a new product"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    service = InventoryService(user_id=session['user_id'])
    
    if request.method == 'GET':
        try:
            products = service.get_products()
            return jsonify([product.to_dict() for product in products])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'JSON data required'}), 400
            
            required_fields = ['sku', 'name', 'category']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            
            product = service.add_product(
                sku=data['sku'],
                name=data['name'],
                category=data['category'],
                reorder_level=data.get('reorder_level', 10),
                unit_cost=data.get('unit_cost', 0.0),
                selling_price=data.get('selling_price', 0.0)
            )
            
            return jsonify(product.to_dict()), 201
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@api.route('/products/<int:product_id>', methods=['PUT', 'DELETE'])
def handle_product(product_id):
    """Update or delete a specific product"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    service = InventoryService(user_id=session['user_id'])
    
    if request.method == 'PUT':
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'JSON data required'}), 400
            
            product = service.update_product(product_id, **data)
            return jsonify(product.to_dict())
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            product = service.get_product_by_id(product_id)
            if not product:
                return jsonify({'error': 'Product not found'}), 404
            
            db.session.delete(product)
            db.session.commit()
            return jsonify({'message': 'Product deleted successfully'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500


@api.route('/inventory', methods=['GET'])
def get_inventory():
    """Get inventory for a specific store or all stores"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    try:
        store_id = request.args.get('store_id', type=int)
        service = InventoryService(user_id=session['user_id'])
        
        if store_id:
            inventory_items = service.get_inventory_for_store(store_id)
        else:
            inventory_items = InventoryItem.query.all()
        
        return jsonify([item.to_dict() for item in inventory_items])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/inventory/update', methods=['POST'])
def update_inventory():
    """Update inventory quantity for a product in a store"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON data required'}), 400
        
        required_fields = ['store_id', 'product_id', 'delta']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        service = InventoryService(user_id=session['user_id'])
        result = service.update_stock(
            store_id=data['store_id'],
            product_id=data['product_id'],
            delta=data['delta'],
            reason=data.get('reason', 'Manual update')
        )
        
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/inventory/transfer', methods=['POST'])
def transfer_inventory():
    """Transfer inventory between stores"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON data required'}), 400
        
        required_fields = ['from_store', 'to_store', 'product_id', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        service = InventoryService(user_id=session['user_id'])
        result = service.transfer_stock(
            from_store_id=data['from_store'],
            to_store_id=data['to_store'],
            product_id=data['product_id'],
            quantity=data['quantity'],
            reason=data.get('reason', 'Stock transfer')
        )
        
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/reports/dashboard', methods=['GET'])
def get_dashboard_kpis():
    """Get dashboard KPIs and metrics"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    try:
        service = InventoryService(user_id=session['user_id'])
        kpis = service.get_dashboard_kpis()
        return jsonify(kpis)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/reports/low-stock', methods=['GET'])
def get_low_stock():
    """Get items with low stock levels"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    try:
        store_id = request.args.get('store_id', type=int)
        service = InventoryService(user_id=session['user_id'])
        low_stock_items = service.get_low_stock_items(store_id=store_id)
        return jsonify(low_stock_items)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/reports/stock', methods=['GET'])
def get_stock_report():
    """Generate stock movement report"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    try:
        # Parse date parameters
        start_date = None
        end_date = None
        
        if request.args.get('start_date'):
            start_date = datetime.fromisoformat(request.args.get('start_date'))
        if request.args.get('end_date'):
            end_date = datetime.fromisoformat(request.args.get('end_date'))
        
        store_id = request.args.get('store_id', type=int)
        
        service = InventoryService(user_id=session['user_id'])
        report = service.generate_stock_report(
            start_date=start_date,
            end_date=end_date,
            store_id=store_id
        )
        
        return jsonify(report)
        
    except ValueError as e:
        return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/transactions', methods=['GET'])
def get_transactions():
    """Get recent transactions"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    try:
        limit = request.args.get('limit', 50, type=int)
        store_id = request.args.get('store_id', type=int)
        
        service = InventoryService(user_id=session['user_id'])
        transactions = service.get_recent_transactions(limit=limit, store_id=store_id)
        
        return jsonify([transaction.to_dict() for transaction in transactions])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/changes', methods=['GET'])
def get_changes():
    """Get recent inventory changes for polling fallback"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    try:
        since_param = request.args.get('since')
        if not since_param:
            return jsonify({'error': 'since parameter required'}), 400
        
        since_timestamp = datetime.fromisoformat(since_param)
        
        # Get transactions since the specified timestamp
        transactions = Transaction.query.filter(
            Transaction.timestamp > since_timestamp
        ).order_by(Transaction.timestamp.desc()).limit(100).all()
        
        changes = []
        for transaction in transactions:
            # Get current inventory item to include current quantity
            inventory_item = InventoryItem.query.filter_by(
                store_id=transaction.store_id,
                product_id=transaction.product_id
            ).first()
            
            change = {
                'transaction': transaction.to_dict(),
                'current_quantity': inventory_item.quantity if inventory_item else 0
            }
            changes.append(change)
        
        return jsonify({
            'changes': changes,
            'timestamp': datetime.now().isoformat()
        })
        
    except ValueError as e:
        return jsonify({'error': f'Invalid timestamp format: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500