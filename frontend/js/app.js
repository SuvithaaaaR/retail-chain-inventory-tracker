/**
 * Retail Chain Inventory Tracker - Main Application JavaScript
 * Shared utilities, authentication, and SocketIO connection management
 */

// Global configuration
const API_BASE = window.location.origin;
const config = {
  apiUrl: API_BASE + "/api",
  socketUrl: API_BASE,
};

// Global state
let socket = null;
let currentUser = null;
let isAuthenticated = false;

/**
 * Utility Functions
 */
class Utils {
  static formatDate(dateString) {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    return date.toLocaleDateString() + " " + date.toLocaleTimeString();
  }

  static formatCurrency(amount) {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount);
  }

  static formatNumber(num) {
    return new Intl.NumberFormat("en-US").format(num);
  }

  static showMessage(message, type = "info") {
    // Create message element
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${type}-message`;
    messageDiv.textContent = message;

    // Style the message
    messageDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            padding: 15px 20px;
            border-radius: 5px;
            color: white;
            font-weight: 500;
            max-width: 400px;
            animation: slideInRight 0.3s ease-out;
        `;

    // Set background color based on type
    switch (type) {
      case "success":
        messageDiv.style.backgroundColor = "#27ae60";
        break;
      case "error":
        messageDiv.style.backgroundColor = "#e74c3c";
        break;
      case "warning":
        messageDiv.style.backgroundColor = "#f39c12";
        break;
      default:
        messageDiv.style.backgroundColor = "#3498db";
    }

    // Add animation styles
    const style = document.createElement("style");
    style.textContent = `
            @keyframes slideInRight {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
    document.head.appendChild(style);

    // Add to page
    document.body.appendChild(messageDiv);

    // Remove after 5 seconds
    setTimeout(() => {
      if (messageDiv.parentNode) {
        messageDiv.remove();
      }
      if (style.parentNode) {
        style.remove();
      }
    }, 5000);
  }

  static async apiCall(endpoint, options = {}) {
    const url = config.apiUrl + endpoint;
    const defaultOptions = {
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
    };

    const finalOptions = { ...defaultOptions, ...options };

    try {
      const response = await fetch(url, finalOptions);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.error || `HTTP ${response.status}: ${response.statusText}`
        );
      }

      return await response.json();
    } catch (error) {
      console.error("API call failed:", error);
      throw error;
    }
  }

  static debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }
}

/**
 * Authentication Management
 */
class Auth {
  static async checkAuthStatus() {
    try {
      const data = await Utils.apiCall("/auth/status");
      isAuthenticated = data.authenticated;

      if (isAuthenticated) {
        // API returns a user object with permissions
        const user = data.user || {};
        currentUser = {
          id: user.id || data.user_id,
          username: user.username || data.username,
          role: user.role || data.role,
          permissions: user.permissions || []
        };
        localStorage.setItem("currentUser", JSON.stringify(currentUser));
        this.updateUserDisplay();
        return true;
      } else {
        localStorage.removeItem("currentUser");
        return false;
      }
    } catch (error) {
      console.error("Auth status check failed:", error);
      return false;
    }
  }

  static async logout() {
    try {
      await Utils.apiCall("/auth/logout", { method: "POST" });
      this.clearAuthData();
      window.location.href = "index.html";
    } catch (error) {
      console.error("Logout failed:", error);
      // Force logout even if API call fails
      this.clearAuthData();
      window.location.href = "index.html";
    }
  }

  static clearAuthData() {
    isAuthenticated = false;
    currentUser = null;
    localStorage.removeItem("currentUser");

    if (socket) {
      socket.disconnect();
      socket = null;
    }
  }

  static updateUserDisplay() {
    const userElement = document.getElementById("currentUser");
    if (userElement && currentUser) {
      userElement.textContent = `${currentUser.username} (${currentUser.role})`;
    }
    // Apply frontend visibility based on permissions
    Auth.applyPermissions();
  }

  static applyPermissions() {
    // Find all elements that declare a permission requirement via data-permission
    const elements = document.querySelectorAll('[data-permission]');
    if (!elements) return;

    const perms = (currentUser && currentUser.permissions) || [];
    elements.forEach((el) => {
      const req = el.getAttribute('data-permission');
      if (!req) return;

      // allow multiple permissions separated by comma; show if any match
      const required = req.split(',').map(s => s.trim().toLowerCase());
      const allowed = required.some(r => perms.includes(r) || r === 'all');

      // If user is admin role, show everything by default
      if (currentUser && currentUser.role === 'admin') {
        el.style.display = '';
      } else if (allowed) {
        el.style.display = '';
      } else {
        // hide element if no permission
        el.style.display = 'none';
      }
    });
  }

  static requireAuth() {
    if (!isAuthenticated) {
      window.location.href = "index.html";
      return false;
    }
    return true;
  }
}

/**
 * WebSocket Management
 */
class WebSocketManager {
  static async initializeSocket() {
    if (!isAuthenticated) {
      console.log("Not authenticated, skipping socket connection");
      return;
    }

    try {
      socket = io(config.socketUrl, {
        transports: ["websocket", "polling"],
        upgrade: true,
        rememberUpgrade: true,
      });

      socket.on("connect", () => {
        console.log("Socket connected:", socket.id);
        this.updateConnectionStatus(true);
        Utils.showMessage("Real-time connection established", "success");
      });

      socket.on("disconnect", (reason) => {
        console.log("Socket disconnected:", reason);
        this.updateConnectionStatus(false);
        Utils.showMessage("Real-time connection lost", "warning");
      });

      socket.on("connect_error", (error) => {
        console.error("Socket connection error:", error);
        this.updateConnectionStatus(false);
      });

      // Global event handlers
      socket.on("inventory_update", (data) => {
        console.log("Inventory update received:", data);
        window.dispatchEvent(
          new CustomEvent("inventoryUpdate", { detail: data })
        );
      });

      socket.on("transfer_update", (data) => {
        console.log("Transfer update received:", data);
        window.dispatchEvent(
          new CustomEvent("transferUpdate", { detail: data })
        );
      });

      socket.on("product_update", (data) => {
        console.log("Product update received:", data);
        window.dispatchEvent(
          new CustomEvent("productUpdate", { detail: data })
        );
      });

      return socket;
    } catch (error) {
      console.error("Socket initialization failed:", error);
      this.updateConnectionStatus(false);
    }
  }

  static updateConnectionStatus(connected) {
    const statusElements = document.querySelectorAll("#connectionStatus");
    statusElements.forEach((element) => {
      if (connected) {
        element.textContent = "🟢 Connected";
        element.className = "status-connected";
      } else {
        element.textContent = "🔴 Disconnected";
        element.className = "status-disconnected";
      }
    });
  }

  static joinStoreRoom(storeId) {
    if (socket && socket.connected) {
      socket.emit("join_store", { store_id: storeId });
    }
  }

  static leaveStoreRoom(storeId) {
    if (socket && socket.connected) {
      socket.emit("leave_store", { store_id: storeId });
    }
  }
}

/**
 * Data Management
 */
class DataManager {
  static stores = [];
  static products = [];

  static async loadStores() {
    try {
      this.stores = await Utils.apiCall("/stores");
      return this.stores;
    } catch (error) {
      console.error("Failed to load stores:", error);
      Utils.showMessage("Failed to load stores", "error");
      return [];
    }
  }

  static async loadProducts() {
    try {
      this.products = await Utils.apiCall("/products");
      return this.products;
    } catch (error) {
      console.error("Failed to load products:", error);
      Utils.showMessage("Failed to load products", "error");
      return [];
    }
  }

  static getStoreById(storeId) {
    return this.stores.find((store) => store.id === parseInt(storeId));
  }

  static getProductById(productId) {
    return this.products.find((product) => product.id === parseInt(productId));
  }

  static populateStoreSelect(selectElement, includeAll = false) {
    if (!selectElement) return;

    selectElement.innerHTML = "";

    if (includeAll) {
      const allOption = document.createElement("option");
      allOption.value = "";
      allOption.textContent = "All Stores";
      selectElement.appendChild(allOption);
    }

    this.stores.forEach((store) => {
      const option = document.createElement("option");
      option.value = store.id;
      option.textContent = `${store.name} - ${store.location}`;
      selectElement.appendChild(option);
    });
  }
}

/**
 * Modal Management
 */
class ModalManager {
  static openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.style.display = "block";
      document.body.style.overflow = "hidden";
    }
  }

  static closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.style.display = "none";
      document.body.style.overflow = "auto";
    }
  }

  static setupModalEvents() {
    // Close modals when clicking on close button or outside the modal
    document.addEventListener("click", (e) => {
      if (
        e.target.classList.contains("close") ||
        e.target.classList.contains("modal")
      ) {
        const modal = e.target.closest(".modal");
        if (modal) {
          modal.style.display = "none";
          document.body.style.overflow = "auto";
        }
      }
    });

    // Close modals when pressing Escape key
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        const openModals = document.querySelectorAll('.modal[style*="block"]');
        openModals.forEach((modal) => {
          modal.style.display = "none";
        });
        document.body.style.overflow = "auto";
      }
    });
  }
}

/**
 * Application Initialization
 */
async function initializeApp() {
  console.log("Initializing Retail Chain Inventory Tracker...");

  // Setup modal events
  ModalManager.setupModalEvents();

  // Check authentication status
  const authenticated = await Auth.checkAuthStatus();

  // If on login page and authenticated, redirect to dashboard
  if (
    window.location.pathname.includes("index.html") ||
    window.location.pathname === "/"
  ) {
    if (authenticated) {
      window.location.href = "dashboard.html";
      return;
    }
  } else {
    // If not on login page but not authenticated, redirect to login
    if (!authenticated) {
      window.location.href = "index.html";
      return;
    }

    // Load common data for authenticated users
    await Promise.all([DataManager.loadStores(), DataManager.loadProducts()]);

    // Initialize WebSocket connection
    await WebSocketManager.initializeSocket();
  }

  // Setup logout button
  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", (e) => {
      e.preventDefault();
      Auth.logout();
    });
  }

  console.log("App initialization complete");
}

// Initialize app when DOM is loaded
document.addEventListener("DOMContentLoaded", initializeApp);

// Global error handler
window.addEventListener("error", (e) => {
  console.error("Global error:", e.error);
  Utils.showMessage("An unexpected error occurred", "error");
});

// Handle unhandled promise rejections
window.addEventListener("unhandledrejection", (e) => {
  console.error("Unhandled promise rejection:", e.reason);
  Utils.showMessage("An unexpected error occurred", "error");
});

// Export utilities for use in other scripts
window.Utils = Utils;
window.Auth = Auth;
window.WebSocketManager = WebSocketManager;
window.DataManager = DataManager;
window.ModalManager = ModalManager;
