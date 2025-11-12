"""
SQLAlchemy models for the Retail Chain Inventory Tracker

This module defines the database schema using SQLAlchemy ORM.
Models include User, Store, Product, InventoryItem, and Transaction.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # user, admin, manager
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def set_password(self, password):
        """Hash and set the password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Store(db.Model):
    """Store model representing different store locations"""
    __tablename__ = 'stores'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    inventory_items = db.relationship('InventoryItem', backref='store', lazy=True, cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', foreign_keys='Transaction.store_id', backref='store', lazy=True)
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Product(db.Model):
    """Product model representing items in inventory"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    reorder_level = db.Column(db.Integer, nullable=False, default=10)
    unit_cost = db.Column(db.Float, nullable=False, default=0.0)
    selling_price = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    inventory_items = db.relationship('InventoryItem', backref='product', lazy=True, cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='product', lazy=True)
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'sku': self.sku,
            'name': self.name,
            'category': self.category,
            'reorder_level': self.reorder_level,
            'unit_cost': self.unit_cost,
            'selling_price': self.selling_price,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class InventoryItem(db.Model):
    """Inventory item linking stores and products with quantities"""
    __tablename__ = 'inventory_items'
    
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Unique constraint to prevent duplicate store-product combinations
    __table_args__ = (db.UniqueConstraint('store_id', 'product_id', name='unique_store_product'),)
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'store_id': self.store_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'store_name': self.store.name if self.store else None,
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'reorder_level': self.product.reorder_level if self.product else None
        }


class Transaction(db.Model):
    """Transaction model for tracking inventory movements"""
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # IN, OUT, TRANSFER
    quantity = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    note = db.Column(db.Text)
    related_store_id = db.Column(db.Integer, db.ForeignKey('stores.id'))  # For transfers
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationship to related store for transfers
    related_store = db.relationship('Store', foreign_keys=[related_store_id])
    user = db.relationship('User', backref='transactions')
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'store_id': self.store_id,
            'type': self.type,
            'quantity': self.quantity,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'note': self.note,
            'related_store_id': self.related_store_id,
            'user_id': self.user_id,
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'store_name': self.store.name if self.store else None,
            'related_store_name': self.related_store.name if self.related_store else None,
            'user_name': self.user.username if self.user else None
        }