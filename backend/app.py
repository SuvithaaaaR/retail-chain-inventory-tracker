"""
Flask Application

Main application file for the Retail Chain Inventory Tracker.
Configures Flask, SQLAlchemy, SocketIO, and registers blueprints.
"""

import os
from flask import Flask, session, request, jsonify, send_from_directory, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from datetime import datetime
import logging

# Import models and components
from models import db, User, Store, Product, InventoryItem, Transaction
from api import api
from socketio_events import init_socketio_events, broadcast_inventory_update, broadcast_transfer_update
from services.inventory_service import InventoryService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
_db_path = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
# Use absolute path for SQLite DB to avoid multiple DB files when launching from different CWDs
_db_path_abs = os.path.abspath(_db_path)
# SQLAlchemy expects a forward-slash path for sqlite URI on Windows
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{_db_path_abs.replace('\\', '/')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
# Use threading async mode on Windows to avoid eventlet greendns/import issues
# Eventlet can cause import hangs on some Windows setups; threading is fine for
# development and testing here.
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True, async_mode='threading')

# Register blueprints
app.register_blueprint(api)

# Initialize SocketIO events
init_socketio_events(socketio)


@app.route('/')
def index():
    """Serve the main application login page"""
    try:
        frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
        index_path = os.path.join(frontend_dir, 'index.html')
        logger.info(f"Serving index.html from: {index_path}")
        logger.info(f"File exists: {os.path.exists(index_path)}")
        return send_file(index_path)
    except Exception as e:
        logger.error(f"Error serving index.html: {e}")
        return f"Error: {str(e)}", 500

@app.route('/debug')
def debug():
    """Debug route to test server"""
    return """
    <html>
    <head><title>Debug</title></head>
    <body>
        <h1>Server is working!</h1>
        <p>If you see this, the Flask server is running correctly.</p>
        <a href="/">Go to main app</a>
    </body>
    </html>
    """

@app.route('/css/<path:filename>')
def serve_css(filename):
    """Serve CSS files"""
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
    return send_file(os.path.join(frontend_dir, 'css', filename))

@app.route('/js/<path:filename>')
def serve_js(filename):
    """Serve JavaScript files"""
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
    return send_file(os.path.join(frontend_dir, 'js', filename))

@app.route('/<filename>.html')
def serve_html(filename):
    """Serve HTML files"""
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
    return send_file(os.path.join(frontend_dir, f'{filename}.html'))

@app.route('/api_info')
def api_info():
    """Show API documentation"""
    return """
    <html>
    <head>
        <title>Retail Chain Inventory Tracker API</title>
    </head>
    <body>
        <h1>Retail Chain Inventory Tracker API</h1>
        <p>This is the backend API server. Please use the frontend application to interact with the system.</p>
        <h3>Available Endpoints:</h3>
        <ul>
            <li>POST /api/auth/login - Login</li>
            <li>POST /api/auth/logout - Logout</li>
            <li>GET /api/auth/status - Check authentication status</li>
            <li>GET /api/stores - Get all stores</li>
            <li>GET /api/products - Get all products</li>
            <li>POST /api/products - Create new product</li>
            <li>GET /api/inventory - Get inventory (optional ?store_id=X)</li>
            <li>POST /api/inventory/update - Update inventory</li>
            <li>POST /api/inventory/transfer - Transfer between stores</li>
            <li>GET /api/reports/dashboard - Get dashboard KPIs</li>
            <li>GET /api/reports/low-stock - Get low stock items</li>
            <li>GET /api/reports/stock - Get stock movement report</li>
            <li>GET /api/transactions - Get recent transactions</li>
            <li>GET /api/changes - Get recent changes (polling)</li>
        </ul>
        <h3>WebSocket Events:</h3>
        <ul>
            <li>inventory_update - Real-time inventory changes</li>
            <li>transfer_update - Real-time transfer notifications</li>
            <li>product_update - Real-time product changes</li>
        </ul>
        <p><a href="/">Go to Application</a></p>
    </body>
    </html>
    """


@app.route('/login', methods=['POST'])
def login():
    """Legacy login endpoint for form-based login"""
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict()
        })
    else:
        return jsonify({'error': 'Invalid credentials'}), 401


# Enhanced API endpoints with SocketIO integration
@app.route('/api/inventory/update', methods=['POST'])
def api_update_inventory():
    """Update inventory with real-time broadcasting"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
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
        
        # Broadcast the update via SocketIO
        broadcast_inventory_update(
            socketio=socketio,
            product_id=data['product_id'],
            store_id=data['store_id'],
            new_qty=result['new_quantity'],
            transaction_id=result['transaction_id'],
            timestamp=result['timestamp']
        )
        
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error updating inventory: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/inventory/transfer', methods=['POST'])
def api_transfer_inventory():
    """Transfer inventory with real-time broadcasting"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
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
        
        # Broadcast the transfer update via SocketIO
        broadcast_transfer_update(
            socketio=socketio,
            from_store_id=data['from_store'],
            to_store_id=data['to_store'],
            product_id=data['product_id'],
            quantity=data['quantity'],
            transaction_data=result,
            timestamp=result['timestamp']
        )
        
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error transferring inventory: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500


@app.before_request
def log_request():
    """Log incoming requests"""
    if request.endpoint and not request.endpoint.startswith('static'):
        logger.info(f"{request.method} {request.path} from {request.remote_addr}")


@app.after_request
def after_request(response):
    """Add CORS headers and log response"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    
    # Log response status for non-static requests
    if request.endpoint and not request.endpoint.startswith('static'):
        logger.info(f"Response: {response.status_code}")
    
    return response


if __name__ == '__main__':
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
        logger.info("Database tables created/verified")
    
    # Run the application with SocketIO
    logger.info("Starting Retail Chain Inventory Tracker server...")
    logger.info("Server will be available at http://localhost:5000")
    logger.info("Frontend files should be served separately or from the frontend directory")
    
    # For local testing we disable the Flask reloader/debugger to avoid
    # the double-start behavior which can cause the server to exit in this
    # environment. Use a production-ready server for deployment.
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=False,
        allow_unsafe_werkzeug=True
    )