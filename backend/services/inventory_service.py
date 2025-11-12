"""
Inventory Service

This module contains the business logic for inventory management operations.
It provides OOP methods for adding products, updating stock, transferring stock,
and generating reports while maintaining transaction safety.
"""

from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from models import db, Store, Product, InventoryItem, Transaction
from sqlalchemy import and_, or_, func


class InventoryService:
    """
    Service class for inventory management operations.
    Handles all business logic related to inventory tracking and management.
    """
    
    def __init__(self, user_id=None):
        """Initialize the service with optional user context"""
        self.user_id = user_id
    
    def get_stores(self):
        """Get all stores"""
        return Store.query.all()
    
    def get_store_by_id(self, store_id):
        """Get a specific store by ID"""
        return Store.query.get(store_id)
    
    def get_products(self):
        """Get all products"""
        return Product.query.all()
    
    def get_product_by_id(self, product_id):
        """Get a specific product by ID"""
        return Product.query.get(product_id)
    
    def get_product_by_sku(self, sku):
        """Get a product by SKU"""
        return Product.query.filter_by(sku=sku).first()
    
    def add_product(self, sku, name, category, reorder_level=10, unit_cost=0.0, selling_price=0.0):
        """
        Add a new product to the system
        
        Args:
            sku (str): Stock Keeping Unit identifier
            name (str): Product name
            category (str): Product category
            reorder_level (int): Minimum stock level before reorder alert
            unit_cost (float): Cost per unit
            selling_price (float): Selling price per unit
            
        Returns:
            Product: The created product object
            
        Raises:
            ValueError: If product with SKU already exists
        """
        try:
            # Check if product with SKU already exists
            existing_product = self.get_product_by_sku(sku)
            if existing_product:
                raise ValueError(f"Product with SKU '{sku}' already exists")
            
            product = Product(
                sku=sku,
                name=name,
                category=category,
                reorder_level=reorder_level,
                unit_cost=unit_cost,
                selling_price=selling_price
            )
            
            db.session.add(product)
            db.session.commit()
            
            return product
            
        except IntegrityError:
            db.session.rollback()
            raise ValueError(f"Product with SKU '{sku}' already exists")
    
    def update_product(self, product_id, **kwargs):
        """
        Update product information
        
        Args:
            product_id (int): Product ID to update
            **kwargs: Fields to update
            
        Returns:
            Product: Updated product object
            
        Raises:
            ValueError: If product not found
        """
        product = self.get_product_by_id(product_id)
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")
        
        # Update allowed fields
        allowed_fields = ['name', 'category', 'reorder_level', 'unit_cost', 'selling_price']
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(product, field, value)
        
        try:
            db.session.commit()
            return product
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Failed to update product")
    
    def get_inventory_for_store(self, store_id):
        """
        Get all inventory items for a specific store
        
        Args:
            store_id (int): Store ID
            
        Returns:
            List[InventoryItem]: List of inventory items for the store
        """
        return InventoryItem.query.filter_by(store_id=store_id).all()
    
    def get_inventory_item(self, store_id, product_id):
        """
        Get specific inventory item for store and product
        
        Args:
            store_id (int): Store ID
            product_id (int): Product ID
            
        Returns:
            InventoryItem: The inventory item or None if not found
        """
        return InventoryItem.query.filter_by(
            store_id=store_id, 
            product_id=product_id
        ).first()
    
    def update_stock(self, store_id, product_id, delta, reason="Manual update"):
        """
        Update stock quantity for a product in a store
        
        Args:
            store_id (int): Store ID
            product_id (int): Product ID  
            delta (int): Change in quantity (positive for increase, negative for decrease)
            reason (str): Reason for the stock change
            
        Returns:
            dict: Result containing new quantity and transaction info
            
        Raises:
            ValueError: If insufficient stock or invalid parameters
        """
        try:
            # Validate inputs
            if not isinstance(delta, int) or delta == 0:
                raise ValueError("Delta must be a non-zero integer")
            
            store = self.get_store_by_id(store_id)
            product = self.get_product_by_id(product_id)
            
            if not store:
                raise ValueError(f"Store with ID {store_id} not found")
            if not product:
                raise ValueError(f"Product with ID {product_id} not found")
            
            # Get or create inventory item
            inventory_item = self.get_inventory_item(store_id, product_id)
            if not inventory_item:
                inventory_item = InventoryItem(
                    store_id=store_id,
                    product_id=product_id,
                    quantity=0
                )
                db.session.add(inventory_item)
            
            # Check for sufficient stock if decreasing
            new_quantity = inventory_item.quantity + delta
            if new_quantity < 0:
                raise ValueError(f"Insufficient stock. Current: {inventory_item.quantity}, Requested: {abs(delta)}")
            
            # Update quantity
            inventory_item.quantity = new_quantity
            inventory_item.last_updated = datetime.now(timezone.utc)
            
            # Create transaction record
            transaction_type = "IN" if delta > 0 else "OUT"
            transaction = Transaction(
                product_id=product_id,
                store_id=store_id,
                type=transaction_type,
                quantity=abs(delta),
                note=reason,
                user_id=self.user_id
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            return {
                'new_quantity': new_quantity,
                'transaction_id': transaction.id,
                'timestamp': transaction.timestamp.isoformat(),
                'inventory_item': inventory_item.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def transfer_stock(self, from_store_id, to_store_id, product_id, quantity, reason="Stock transfer"):
        """
        Transfer stock between stores
        
        Args:
            from_store_id (int): Source store ID
            to_store_id (int): Destination store ID
            product_id (int): Product ID
            quantity (int): Quantity to transfer (must be positive)
            reason (str): Reason for transfer
            
        Returns:
            dict: Result containing transaction details for both stores
            
        Raises:
            ValueError: If insufficient stock or invalid parameters
        """
        try:
            # Validate inputs
            if quantity <= 0:
                raise ValueError("Transfer quantity must be positive")
            
            if from_store_id == to_store_id:
                raise ValueError("Cannot transfer to the same store")
            
            from_store = self.get_store_by_id(from_store_id)
            to_store = self.get_store_by_id(to_store_id)
            product = self.get_product_by_id(product_id)
            
            if not from_store:
                raise ValueError(f"Source store with ID {from_store_id} not found")
            if not to_store:
                raise ValueError(f"Destination store with ID {to_store_id} not found")
            if not product:
                raise ValueError(f"Product with ID {product_id} not found")
            
            # Get source inventory item
            from_inventory = self.get_inventory_item(from_store_id, product_id)
            if not from_inventory or from_inventory.quantity < quantity:
                current_qty = from_inventory.quantity if from_inventory else 0
                raise ValueError(f"Insufficient stock at source store. Current: {current_qty}, Requested: {quantity}")
            
            # Get or create destination inventory item
            to_inventory = self.get_inventory_item(to_store_id, product_id)
            if not to_inventory:
                to_inventory = InventoryItem(
                    store_id=to_store_id,
                    product_id=product_id,
                    quantity=0
                )
                db.session.add(to_inventory)
            
            # Update quantities
            from_inventory.quantity -= quantity
            from_inventory.last_updated = datetime.now(timezone.utc)
            
            to_inventory.quantity += quantity
            to_inventory.last_updated = datetime.now(timezone.utc)
            
            # Create transaction records for both stores
            out_transaction = Transaction(
                product_id=product_id,
                store_id=from_store_id,
                type="TRANSFER",
                quantity=quantity,
                note=f"Transfer OUT to {to_store.name}: {reason}",
                related_store_id=to_store_id,
                user_id=self.user_id
            )
            
            in_transaction = Transaction(
                product_id=product_id,
                store_id=to_store_id,
                type="TRANSFER",
                quantity=quantity,
                note=f"Transfer IN from {from_store.name}: {reason}",
                related_store_id=from_store_id,
                user_id=self.user_id
            )
            
            db.session.add(out_transaction)
            db.session.add(in_transaction)
            db.session.commit()
            
            return {
                'from_store': {
                    'new_quantity': from_inventory.quantity,
                    'transaction_id': out_transaction.id,
                    'inventory_item': from_inventory.to_dict()
                },
                'to_store': {
                    'new_quantity': to_inventory.quantity,
                    'transaction_id': in_transaction.id,
                    'inventory_item': to_inventory.to_dict()
                },
                'timestamp': out_transaction.timestamp.isoformat()
            }
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def get_low_stock_items(self, store_id=None):
        """
        Get items with stock below reorder level
        
        Args:
            store_id (int, optional): Filter by specific store
            
        Returns:
            List[dict]: List of low stock items with details
        """
        query = db.session.query(InventoryItem, Product).join(Product).filter(
            InventoryItem.quantity <= Product.reorder_level
        )
        
        if store_id:
            query = query.filter(InventoryItem.store_id == store_id)
        
        results = query.all()
        
        low_stock_items = []
        for inventory_item, product in results:
            item_dict = inventory_item.to_dict()
            item_dict.update({
                'product_name': product.name,
                'product_sku': product.sku,
                'reorder_level': product.reorder_level,
                'shortage': product.reorder_level - inventory_item.quantity
            })
            low_stock_items.append(item_dict)
        
        return low_stock_items
    
    def get_recent_transactions(self, limit=50, store_id=None):
        """
        Get recent transactions
        
        Args:
            limit (int): Maximum number of transactions to return
            store_id (int, optional): Filter by specific store
            
        Returns:
            List[Transaction]: List of recent transactions
        """
        query = Transaction.query.order_by(Transaction.timestamp.desc())
        
        if store_id:
            query = query.filter(Transaction.store_id == store_id)
        
        return query.limit(limit).all()
    
    def generate_stock_report(self, start_date=None, end_date=None, store_id=None):
        """
        Generate aggregated stock movement report
        
        Args:
            start_date (datetime, optional): Start date for report
            end_date (datetime, optional): End date for report
            store_id (int, optional): Filter by specific store
            
        Returns:
            dict: Report data with totals and breakdowns
        """
        # Base query for transactions
        query = Transaction.query
        
        # Apply filters
        if start_date:
            query = query.filter(Transaction.timestamp >= start_date)
        if end_date:
            query = query.filter(Transaction.timestamp <= end_date)
        if store_id:
            query = query.filter(Transaction.store_id == store_id)
        
        transactions = query.all()
        
        # Calculate totals
        total_in = sum(t.quantity for t in transactions if t.type in ['IN', 'TRANSFER'] and t.store_id == store_id)
        total_out = sum(t.quantity for t in transactions if t.type == 'OUT')
        total_transfers_in = sum(t.quantity for t in transactions if t.type == 'TRANSFER' and t.store_id == store_id)
        total_transfers_out = sum(t.quantity for t in transactions if t.type == 'TRANSFER' and t.related_store_id)
        
        # Get current inventory summary
        inventory_query = db.session.query(
            InventoryItem.store_id,
            func.count(InventoryItem.id).label('total_products'),
            func.sum(InventoryItem.quantity).label('total_units')
        ).group_by(InventoryItem.store_id)
        
        if store_id:
            inventory_query = inventory_query.filter(InventoryItem.store_id == store_id)
        
        inventory_summary = inventory_query.all()
        
        return {
            'period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'totals': {
                'total_in': total_in,
                'total_out': total_out,
                'total_transfers_in': total_transfers_in,
                'total_transfers_out': total_transfers_out,
                'net_change': total_in - total_out
            },
            'transactions': [t.to_dict() for t in transactions],
            'inventory_summary': [
                {
                    'store_id': summary.store_id,
                    'total_products': summary.total_products,
                    'total_units': summary.total_units
                }
                for summary in inventory_summary
            ]
        }
    
    def get_dashboard_kpis(self):
        """
        Get key performance indicators for dashboard
        
        Returns:
            dict: KPI data including totals and alerts
        """
        # Total unique products
        total_products = Product.query.count()
        
        # Total inventory units across all stores
        total_units = db.session.query(func.sum(InventoryItem.quantity)).scalar() or 0
        
        # Low stock count
        low_stock_count = db.session.query(InventoryItem).join(Product).filter(
            InventoryItem.quantity <= Product.reorder_level
        ).count()
        
        # Total stores
        total_stores = Store.query.count()
        
        # Recent transactions (last 10)
        recent_transactions = self.get_recent_transactions(limit=10)
        
        return {
            'total_products': total_products,
            'total_units': total_units,
            'low_stock_count': low_stock_count,
            'total_stores': total_stores,
            'recent_transactions': [t.to_dict() for t in recent_transactions]
        }