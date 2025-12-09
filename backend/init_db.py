"""
Database Initialization Script

This script creates the SQLite database and seeds it with sample data.
Run this script before starting the application for the first time.
"""

import os
import sys
from datetime import datetime, timezone

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, User, Store, Product, InventoryItem, Transaction
from services.inventory_service import InventoryService


def create_database():
    """Create all database tables"""
    print("Creating database tables...")
    with app.app_context():
        # Drop all tables and recreate (for clean setup)
        db.drop_all()
        db.create_all()
        print("✓ Database tables created successfully")


def seed_users():
    """Create sample users"""
    print("Creating sample users...")
    
    users_data = [
        {'username': 'admin', 'password': 'admin123', 'role': 'admin'},
        {'username': 'manager', 'password': 'manager123', 'role': 'manager'},
        {'username': 'user1', 'password': 'user123', 'role': 'user'},
        {'username': 'user2', 'password': 'user123', 'role': 'user'},
    ]
    
    # Define default permission sets per role
    default_permissions = {
        'admin': ['products', 'inventory', 'reports', 'transactions', 'manage_users'],
        'manager': ['products', 'inventory', 'reports', 'transactions'],
        'user': ['inventory_view']
    }

    for user_data in users_data:
        user = User(
            username=user_data['username'],
            role=user_data['role']
        )
        user.set_password(user_data['password'])
        # assign default permissions based on role
        perms = default_permissions.get(user_data['role'], [])
        user.set_permissions(perms)
        db.session.add(user)
    
    db.session.commit()
    print(f"✓ Created {len(users_data)} sample users")
    print("  Login credentials:")
    for user_data in users_data:
        print(f"    {user_data['username']} / {user_data['password']} ({user_data['role']})")


def seed_stores():
    """Create sample stores"""
    print("Creating sample stores...")
    
    stores_data = [
        {'name': 'Downtown Store', 'location': '123 Main St, Downtown'},
        {'name': 'Mall Store', 'location': '456 Shopping Mall, West Side'},
        {'name': 'Warehouse', 'location': '789 Industrial Blvd, North'},
        {'name': 'Online Fulfillment', 'location': 'Virtual - Online Orders'},
    ]
    
    for store_data in stores_data:
        store = Store(
            name=store_data['name'],
            location=store_data['location']
        )
        db.session.add(store)
    
    db.session.commit()
    print(f"✓ Created {len(stores_data)} sample stores")


def seed_products():
    """Create sample products"""
    print("Creating sample products...")
    
    products_data = [
        {
            'sku': 'LAPTOP001',
            'name': 'Gaming Laptop Pro',
            'category': 'Electronics',
            'reorder_level': 5,
            'unit_cost': 800.00,
            'selling_price': 1200.00
        },
        {
            'sku': 'PHONE001',
            'name': 'Smartphone X1',
            'category': 'Electronics',
            'reorder_level': 10,
            'unit_cost': 300.00,
            'selling_price': 500.00
        },
        {
            'sku': 'TABLET001',
            'name': 'Tablet Air',
            'category': 'Electronics',
            'reorder_level': 8,
            'unit_cost': 200.00,
            'selling_price': 350.00
        },
        {
            'sku': 'HEADPHONE001',
            'name': 'Wireless Headphones',
            'category': 'Audio',
            'reorder_level': 15,
            'unit_cost': 50.00,
            'selling_price': 100.00
        },
        {
            'sku': 'SPEAKER001',
            'name': 'Bluetooth Speaker',
            'category': 'Audio',
            'reorder_level': 12,
            'unit_cost': 30.00,
            'selling_price': 75.00
        },
        {
            'sku': 'CAMERA001',
            'name': 'Digital Camera Pro',
            'category': 'Photography',
            'reorder_level': 3,
            'unit_cost': 400.00,
            'selling_price': 700.00
        },
        {
            'sku': 'WATCH001',
            'name': 'Smart Watch',
            'category': 'Wearables',
            'reorder_level': 20,
            'unit_cost': 100.00,
            'selling_price': 200.00
        },
        {
            'sku': 'CHARGER001',
            'name': 'USB-C Charger',
            'category': 'Accessories',
            'reorder_level': 25,
            'unit_cost': 10.00,
            'selling_price': 25.00
        },
    ]
    
    for product_data in products_data:
        product = Product(**product_data)
        db.session.add(product)
    
    db.session.commit()
    print(f"✓ Created {len(products_data)} sample products")


def seed_inventory():
    """Create sample inventory with varying stock levels"""
    print("Creating sample inventory...")
    
    # Get all stores and products
    stores = Store.query.all()
    products = Product.query.all()
    
    # Sample inventory data (store_id, product_id, quantity)
    # Some items will be below reorder level to demonstrate low stock alerts
    inventory_data = [
        # Downtown Store (id: 1)
        (1, 1, 12),  # Gaming Laptop Pro
        (1, 2, 25),  # Smartphone X1
        (1, 3, 15),  # Tablet Air
        (1, 4, 3),   # Wireless Headphones (below reorder level)
        (1, 5, 8),   # Bluetooth Speaker
        (1, 6, 5),   # Digital Camera Pro
        (1, 7, 30),  # Smart Watch
        (1, 8, 50),  # USB-C Charger
        
        # Mall Store (id: 2)
        (2, 1, 8),   # Gaming Laptop Pro
        (2, 2, 18),  # Smartphone X1
        (2, 3, 22),  # Tablet Air
        (2, 4, 45),  # Wireless Headphones
        (2, 5, 20),  # Bluetooth Speaker
        (2, 6, 2),   # Digital Camera Pro (below reorder level)
        (2, 7, 35),  # Smart Watch
        (2, 8, 40),  # USB-C Charger
        
        # Warehouse (id: 3) - Higher quantities for restocking
        (3, 1, 50),  # Gaming Laptop Pro
        (3, 2, 100), # Smartphone X1
        (3, 3, 75),  # Tablet Air
        (3, 4, 80),  # Wireless Headphones
        (3, 5, 60),  # Bluetooth Speaker
        (3, 6, 25),  # Digital Camera Pro
        (3, 7, 120), # Smart Watch
        (3, 8, 200), # USB-C Charger
        
        # Online Fulfillment (id: 4)
        (4, 1, 15),  # Gaming Laptop Pro
        (4, 2, 30),  # Smartphone X1
        (4, 3, 5),   # Tablet Air (below reorder level)
        (4, 4, 20),  # Wireless Headphones
        (4, 5, 10),  # Bluetooth Speaker (below reorder level)
        (4, 6, 8),   # Digital Camera Pro
        (4, 7, 25),  # Smart Watch
        (4, 8, 60),  # USB-C Charger
    ]
    
    for store_id, product_id, quantity in inventory_data:
        inventory_item = InventoryItem(
            store_id=store_id,
            product_id=product_id,
            quantity=quantity
        )
        db.session.add(inventory_item)
    
    db.session.commit()
    print(f"✓ Created {len(inventory_data)} inventory items")


def seed_transactions():
    """Create sample transaction history"""
    print("Creating sample transaction history...")
    
    admin_user = User.query.filter_by(username='admin').first()
    
    # Sample transactions to show various activities
    transactions_data = [
        {
            'product_id': 1,
            'store_id': 1,
            'type': 'IN',
            'quantity': 10,
            'note': 'Initial stock',
            'user_id': admin_user.id
        },
        {
            'product_id': 2,
            'store_id': 2,
            'type': 'OUT',
            'quantity': 5,
            'note': 'Sale to customer',
            'user_id': admin_user.id
        },
        {
            'product_id': 4,
            'store_id': 1,
            'type': 'TRANSFER',
            'quantity': 10,
            'note': 'Transfer to Mall Store',
            'related_store_id': 2,
            'user_id': admin_user.id
        },
        {
            'product_id': 7,
            'store_id': 3,
            'type': 'IN',
            'quantity': 50,
            'note': 'Restocking from supplier',
            'user_id': admin_user.id
        },
        {
            'product_id': 8,
            'store_id': 4,
            'type': 'OUT',
            'quantity': 15,
            'note': 'Online order fulfillment',
            'user_id': admin_user.id
        },
    ]
    
    for transaction_data in transactions_data:
        transaction = Transaction(**transaction_data)
        db.session.add(transaction)
    
    db.session.commit()
    print(f"✓ Created {len(transactions_data)} sample transactions")


def print_summary():
    """Print a summary of created data"""
    print("\n" + "="*50)
    print("DATABASE INITIALIZATION COMPLETE")
    print("="*50)
    
    with app.app_context():
        user_count = User.query.count()
        store_count = Store.query.count()
        product_count = Product.query.count()
        inventory_count = InventoryItem.query.count()
        transaction_count = Transaction.query.count()
        
        print(f"Users created: {user_count}")
        print(f"Stores created: {store_count}")
        print(f"Products created: {product_count}")
        print(f"Inventory items created: {inventory_count}")
        print(f"Transactions created: {transaction_count}")
        
        # Show low stock items
        service = InventoryService()
        low_stock_items = service.get_low_stock_items()
        
        print(f"\nLow stock alerts: {len(low_stock_items)}")
        if low_stock_items:
            print("Items requiring attention:")
            for item in low_stock_items[:5]:  # Show first 5
                print(f"  - {item['product_name']} at {item['store_name']}: {item['quantity']} (reorder at {item['reorder_level']})")
        
        print(f"\nDatabase file created: database.db")
        print("You can now start the application with: python app.py")


def main():
    """Main initialization function"""
    print("Retail Chain Inventory Tracker - Database Initialization")
    print("="*60)
    
    try:
        with app.app_context():
            create_database()
            seed_users()
            seed_stores()
            seed_products()
            seed_inventory()
            seed_transactions()
            print_summary()
            
    except Exception as e:
        print(f"\n❌ Error during database initialization: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()