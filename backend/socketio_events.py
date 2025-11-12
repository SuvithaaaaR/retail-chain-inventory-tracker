"""
SocketIO Event Handlers

This module handles WebSocket events for real-time inventory updates.
Manages client connections and broadcasts inventory changes to connected clients.
"""

from flask_socketio import emit, join_room, leave_room, rooms
from flask import session
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_socketio_events(socketio):
    """Initialize SocketIO event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        if 'user_id' not in session:
            logger.warning("Unauthenticated client attempted to connect")
            return False  # Reject connection
        
        logger.info(f"User {session['username']} connected")
        emit('connected', {
            'message': 'Connected to inventory tracker',
            'user': session['username']
        })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        if 'username' in session:
            logger.info(f"User {session['username']} disconnected")
    
    @socketio.on('join_store')
    def handle_join_store(data):
        """Join a store room for store-specific updates"""
        if 'user_id' not in session:
            emit('error', {'message': 'Authentication required'})
            return
        
        store_id = data.get('store_id')
        if not store_id:
            emit('error', {'message': 'Store ID required'})
            return
        
        room = f"store_{store_id}"
        join_room(room)
        logger.info(f"User {session['username']} joined store room {room}")
        emit('joined_store', {
            'store_id': store_id,
            'message': f'Joined store {store_id} updates'
        })
    
    @socketio.on('leave_store')
    def handle_leave_store(data):
        """Leave a store room"""
        if 'user_id' not in session:
            return
        
        store_id = data.get('store_id')
        if not store_id:
            return
        
        room = f"store_{store_id}"
        leave_room(room)
        logger.info(f"User {session['username']} left store room {room}")
        emit('left_store', {
            'store_id': store_id,
            'message': f'Left store {store_id} updates'
        })
    
    @socketio.on('ping')
    def handle_ping():
        """Handle ping for connection testing"""
        emit('pong', {'timestamp': str(datetime.now())})


def broadcast_inventory_update(socketio, product_id, store_id, new_qty, transaction_id, timestamp):
    """
    Broadcast inventory update to connected clients
    
    Args:
        socketio: SocketIO instance
        product_id (int): Product ID that was updated
        store_id (int): Store ID where update occurred
        new_qty (int): New quantity after update
        transaction_id (int): Transaction ID for the update
        timestamp (str): ISO timestamp of the update
    """
    update_data = {
        'product_id': product_id,
        'store_id': store_id,
        'new_qty': new_qty,
        'transaction_id': transaction_id,
        'timestamp': timestamp,
        'type': 'inventory_update'
    }
    
    # Broadcast to all connected clients
    socketio.emit('inventory_update', update_data)
    
    # Also broadcast to store-specific room
    store_room = f"store_{store_id}"
    socketio.emit('store_inventory_update', update_data, room=store_room)
    
    logger.info(f"Broadcasted inventory update: Product {product_id}, Store {store_id}, Qty {new_qty}")


def broadcast_transfer_update(socketio, from_store_id, to_store_id, product_id, quantity, transaction_data, timestamp):
    """
    Broadcast transfer update to connected clients
    
    Args:
        socketio: SocketIO instance
        from_store_id (int): Source store ID
        to_store_id (int): Destination store ID
        product_id (int): Product ID being transferred
        quantity (int): Quantity transferred
        transaction_data (dict): Transaction details
        timestamp (str): ISO timestamp of the transfer
    """
    transfer_data = {
        'from_store_id': from_store_id,
        'to_store_id': to_store_id,
        'product_id': product_id,
        'quantity': quantity,
        'transaction_data': transaction_data,
        'timestamp': timestamp,
        'type': 'transfer_update'
    }
    
    # Broadcast to all connected clients
    socketio.emit('transfer_update', transfer_data)
    
    # Broadcast to both store-specific rooms
    from_store_room = f"store_{from_store_id}"
    to_store_room = f"store_{to_store_id}"
    
    socketio.emit('store_transfer_update', transfer_data, room=from_store_room)
    socketio.emit('store_transfer_update', transfer_data, room=to_store_room)
    
    logger.info(f"Broadcasted transfer update: Product {product_id}, {from_store_id} -> {to_store_id}, Qty {quantity}")


def broadcast_product_update(socketio, product_id, action, product_data=None):
    """
    Broadcast product changes (create, update, delete) to connected clients
    
    Args:
        socketio: SocketIO instance
        product_id (int): Product ID
        action (str): Action performed ('created', 'updated', 'deleted')
        product_data (dict, optional): Product data for create/update actions
    """
    update_data = {
        'product_id': product_id,
        'action': action,
        'product_data': product_data,
        'timestamp': str(datetime.now()),
        'type': 'product_update'
    }
    
    socketio.emit('product_update', update_data)
    logger.info(f"Broadcasted product update: Product {product_id}, Action {action}")


from datetime import datetime