# Retail Chain Inventory Tracker

A complete, real-time inventory management system for retail chains with centralized tracking across multiple store locations. Built with Python Flask backend and vanilla JavaScript frontend, featuring WebSocket-based real-time updates.

## Features

### 🏪 Multi-Store Management

- Centralized inventory tracking across multiple store locations
- Real-time stock level monitoring
- Store-specific inventory views and management

### 📦 Product Management

- Complete product catalog with SKU, pricing, and categorization
- Configurable reorder levels for automated low-stock alerts
- Product lifecycle management (create, update, delete)

### 🔄 Real-Time Updates

- WebSocket-based real-time inventory updates
- Live notifications for stock changes and transfers
- Polling fallback for connection reliability

### 📊 Comprehensive Reporting

- Dashboard with key performance indicators (KPIs)
- Stock movement reports with date/store filtering
- Low stock alerts and recommendations
- CSV export functionality

### 🚀 Easy Deployment

- Single SQLite database file
- No external dependencies or cloud services
- Self-contained local deployment

## Technology Stack

### Backend

- **Python Flask** - Web framework
- **SQLAlchemy** - Database ORM
- **Flask-SocketIO** - Real-time WebSocket communication
- **SQLite** - Local file database
- **Eventlet** - Asynchronous server

### Frontend

- **HTML5/CSS3** - Modern responsive design
- **Vanilla JavaScript** - No framework dependencies
- **Socket.IO Client** - Real-time communication
- **CSS Grid/Flexbox** - Responsive layouts

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Modern web browser with JavaScript enabled

### Installation

1. **Clone or download the project**

   ```bash
   cd retail-chain-inventory-tracker
   ```

2. **Create and activate virtual environment**

   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Initialize the database**

   ```bash
   cd backend
   python init_db.py
   ```

5. **Start the backend server**

   ```bash
   python app.py
   ```

6. **Access the application**
   - Open your web browser
   - Navigate to `http://localhost:5000` (redirects to frontend)
   - Or directly open `frontend/index.html` in your browser

### Default Login Credentials

| Username | Password   | Role    |
| -------- | ---------- | ------- |
| admin    | admin123   | admin   |
| manager  | manager123 | manager |
| user1    | user123    | user    |
| user2    | user123    | user    |

## Application Structure

```
retail-chain-inventory-tracker/
├── backend/
│   ├── app.py                    # Main Flask application
│   ├── models.py                 # SQLAlchemy database models
│   ├── api.py                    # REST API endpoints
│   ├── socketio_events.py        # WebSocket event handlers
│   ├── init_db.py               # Database initialization script
│   ├── requirements.txt         # Python dependencies
│   ├── database.db              # SQLite database (created by init_db.py)
│   └── services/
│       └── inventory_service.py  # Business logic service
├── frontend/
│   ├── index.html               # Login page
│   ├── dashboard.html           # Main dashboard
│   ├── store_inventory.html     # Store inventory management
│   ├── product_management.html  # Product catalog management
│   ├── reports.html             # Reports and analytics
│   ├── css/
│   │   └── styles.css           # Application styles
│   └── js/
│       ├── app.js               # Shared utilities and WebSocket
│       ├── dashboard.js         # Dashboard functionality
│       ├── store_inventory.js   # Inventory management
│       ├── product_management.js # Product CRUD operations
│       └── reports.js           # Reporting and analytics
└── README.md                    # This file
```

## API Endpoints

### Authentication

- `POST /api/auth/login` - User authentication
- `POST /api/auth/logout` - User logout
- `GET /api/auth/status` - Check authentication status

### Stores

- `GET /api/stores` - List all stores

### Products

- `GET /api/products` - List all products
- `POST /api/products` - Create new product
- `PUT /api/products/{id}` - Update product
- `DELETE /api/products/{id}` - Delete product

### Inventory

- `GET /api/inventory?store_id={id}` - Get store inventory
- `POST /api/inventory/update` - Update stock levels
- `POST /api/inventory/transfer` - Transfer stock between stores

### Reports

- `GET /api/reports/dashboard` - Dashboard KPIs
- `GET /api/reports/low-stock` - Low stock alerts
- `GET /api/reports/stock` - Stock movement report
- `GET /api/transactions` - Recent transactions
- `GET /api/changes?since={timestamp}` - Recent changes (polling)

## WebSocket Events

### Client → Server

- `join_store` - Join store-specific room for updates
- `leave_store` - Leave store room
- `ping` - Connection health check

### Server → Client

- `inventory_update` - Real-time inventory changes
- `transfer_update` - Stock transfer notifications
- `product_update` - Product changes
- `connected` - Connection established
- `pong` - Ping response

## Sample API Usage

### Update Inventory

```bash
curl -X POST http://localhost:5000/api/inventory/update \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": 1,
    "product_id": 2,
    "delta": -5,
    "reason": "sold 5 units"
  }'
```

### Transfer Stock

```bash
curl -X POST http://localhost:5000/api/inventory/transfer \
  -H "Content-Type: application/json" \
  -d '{
    "from_store": 1,
    "to_store": 2,
    "product_id": 3,
    "quantity": 10,
    "reason": "restock transfer"
  }'
```

### Generate Report

```bash
curl "http://localhost:5000/api/reports/stock?start_date=2024-01-01&end_date=2024-12-31&store_id=1"
```

## Sample WebSocket Usage

```javascript
const socket = io("http://localhost:5000");

// Listen for inventory updates
socket.on("inventory_update", (data) => {
  console.log("Inventory updated:", data);
  // data: { product_id, store_id, new_qty, transaction_id, timestamp }
});

// Join store-specific updates
socket.emit("join_store", { store_id: 1 });
```

## Database Schema

### Tables

- **users** - Authentication and user management
- **stores** - Store locations and information
- **products** - Product catalog with SKUs and pricing
- **inventory_items** - Current stock levels per store/product
- **transactions** - Complete audit trail of all inventory movements

### Key Relationships

- `inventory_items` links stores and products with quantities
- `transactions` provides complete audit trail
- Foreign key constraints ensure data integrity

## Development

### Running in Development Mode

```bash
# Enable debug mode (already enabled in app.py)
export FLASK_ENV=development  # Linux/Mac
set FLASK_ENV=development     # Windows

python backend/app.py
```

### Adding New Features

1. **Backend**: Add API endpoints in `api.py` and business logic in `services/`
2. **Frontend**: Create new HTML pages and corresponding JavaScript modules
3. **Database**: Modify models in `models.py` and update `init_db.py`

### Code Organization

- **Object-Oriented Design**: Business logic separated into service classes
- **MVC Pattern**: Models, API routes, and frontend clearly separated
- **Real-time Updates**: WebSocket events properly namespaced and handled
- **Error Handling**: Comprehensive error handling and user feedback

## Troubleshooting

### Common Issues

**Database Issues**

```bash
# Recreate database
rm backend/database.db
python backend/init_db.py
```

**Port Already in Use**

```bash
# Find and kill process using port 5000
netstat -ano | findstr :5000  # Windows
lsof -ti:5000 | xargs kill     # Linux/Mac
```

**WebSocket Connection Issues**

- Ensure backend server is running on port 5000
- Check browser console for connection errors
- Verify firewall isn't blocking WebSocket connections

**Frontend Not Loading**

- Serve frontend files through HTTP server for CORS:

```bash
# Python 3
cd frontend
python -m http.server 8080

# Then access: http://localhost:8080
```

### Logs and Debugging

- Backend logs appear in terminal running `app.py`
- Frontend logs available in browser developer console
- WebSocket events logged to console in debug mode

## Production Deployment

### Security Considerations

- Change default secret key in `app.py`
- Use environment variables for configuration
- Implement proper authentication and authorization
- Use HTTPS in production
- Configure proper CORS settings

### Performance Optimization

- Consider PostgreSQL for larger deployments
- Implement connection pooling
- Add Redis for session storage and caching
- Use nginx for static file serving

### Backup Strategy

- Regular SQLite database backups
- Transaction log archiving
- Configuration file backups

## License

This project is provided as-is for educational and demonstration purposes. Feel free to modify and adapt for your specific needs.

## Support

For issues, questions, or feature requests:

1. Check the troubleshooting section above
2. Review the code comments and documentation
3. Examine browser developer console for frontend issues
4. Check backend terminal output for server-side issues

## Sample Data

The `init_db.py` script creates sample data including:

- 4 stores (Downtown, Mall, Warehouse, Online)
- 8 products across different categories
- Inventory distributed across stores with some low-stock scenarios
- Sample transaction history
- Multiple user accounts with different roles

This provides a complete working environment for testing and demonstration.
