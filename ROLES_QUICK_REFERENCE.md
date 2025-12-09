# 3-Role System Quick Reference

## 🔑 Login Credentials

| Role        | Username | Password   | Access Level |
| ----------- | -------- | ---------- | ------------ |
| **Admin**   | admin    | admin123   | Full Access  |
| **Manager** | manager  | manager123 | Operations   |
| **Staff**   | staff    | staff123   | View Only    |

---

## 🎯 Role Capabilities

### 👤 Admin (Full Access)

**Permissions:** `products`, `inventory`, `reports`, `transactions`, `manage_users`

✅ **Can Do Everything:**

- Create, edit, delete products
- Update and transfer inventory
- View all reports and analytics
- View transaction history
- Manage user accounts

❌ **Restrictions:** None

---

### 👤 Manager (Operations)

**Permissions:** `products`, `inventory`, `reports`, `transactions`

✅ **Can Do:**

- Create and edit products
- Update and transfer inventory
- View all reports and analytics
- View transaction history

❌ **Cannot:**

- Delete products (admin only)
- Manage users (admin only)

---

### 👤 Staff (View Only)

**Permissions:** `inventory_view`

✅ **Can Do:**

- View inventory levels for all stores

❌ **Cannot:**

- Modify anything
- View reports or analytics
- View transaction history
- Access product management
- Manage users

---

## 🛠️ Quick Commands

```bash
# Initialize/Reset Database
python backend/init_db.py

# Start Server
python backend/app.py

# Test Permissions
python backend/scripts/test_permissions.py

# Test Login (in-process)
python backend/scripts/test_login.py
```

---

## 🔍 How to Verify Permissions

### Test Staff User (Should be blocked from everything)

1. Login as `staff/staff123`
2. Try to add a product → Button hidden
3. Try API: `POST /api/products` → 403 Forbidden ✅

### Test Manager User (Should not delete)

1. Login as `manager/manager123`
2. Can add/edit products → Works ✅
3. Try to delete product → Button hidden
4. Try API: `DELETE /api/products/1` → 403 Forbidden ✅

### Test Admin User (Should do everything)

1. Login as `admin/admin123`
2. All features visible ✅
3. User Management menu visible ✅
4. Can delete products ✅

---

## 📊 Permission Enforcement

**Two-Layer Security:**

1. **Frontend** - Hides buttons based on permissions (UX)
2. **Backend** - Validates permissions on API calls (Security)

**Staff cannot bypass** by:

- Using browser console
- Making direct API calls
- Manipulating frontend code

All requests return **403 Forbidden** if permission denied.

---

## 🎨 UI Behavior by Role

| Feature            | Admin       | Manager          | Staff     |
| ------------------ | ----------- | ---------------- | --------- |
| Dashboard          | Full access | Full access      | No access |
| Product Management | Full CRUD   | Create/Edit only | Hidden    |
| Store Inventory    | Full CRUD   | Full CRUD        | View only |
| Reports            | Full access | Full access      | Hidden    |
| User Management    | Visible     | Hidden           | Hidden    |

---

## 📄 Implementation Files

**Backend:**

- `backend/models.py` - User model with permissions
- `backend/init_db.py` - Seeds 3 users with permissions
- `backend/api.py` - Enforces permissions on endpoints

**Frontend:**

- `frontend/js/app.js` - Hides UI based on permissions
- `frontend/index.html` - Login page with credentials
- `frontend/*_management.html` - Pages with permission checks

**Documentation:**

- `PERMISSIONS_IMPLEMENTATION.md` - Complete technical guide
- `ROLES_QUICK_REFERENCE.md` - This file

---

## ✅ Status: COMPLETE

The 3-role system is fully implemented with:

- ✅ Database schema with permissions column
- ✅ 3 default users (admin, manager, staff)
- ✅ Frontend permission-based UI hiding
- ✅ Backend API permission validation
- ✅ Comprehensive test suite
- ✅ Production ready

**Security Level:** High - Double-layer enforcement prevents bypass
