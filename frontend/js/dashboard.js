/**
 * Dashboard JavaScript
 * Handles dashboard functionality, KPIs, and real-time updates
 */

class Dashboard {
  constructor() {
    this.kpiData = {};
    this.transactionsData = [];
    this.lowStockData = [];
    this.pollInterval = null;
    this.lastUpdateTime = new Date().toISOString();

    this.init();
  }

  async init() {
    console.log("Initializing dashboard...");

    // Setup event listeners
    this.setupEventListeners();

    // Load initial data
    await this.loadDashboardData();

    // Setup polling for non-socket updates
    this.setupPolling();

    console.log("Dashboard initialized");
  }

  setupEventListeners() {
    // Real-time event listeners
    window.addEventListener("inventoryUpdate", (event) => {
      this.handleInventoryUpdate(event.detail);
    });

    window.addEventListener("transferUpdate", (event) => {
      this.handleTransferUpdate(event.detail);
    });

    // Socket connection events
    if (window.socket) {
      window.socket.on("connected", () => {
        this.refreshData();
      });
    }
  }

  async loadDashboardData() {
    try {
      // Load KPIs and recent transactions
      await Promise.all([this.loadKPIs(), this.loadLowStockAlerts()]);
    } catch (error) {
      console.error("Failed to load dashboard data:", error);
      Utils.showMessage("Failed to load dashboard data", "error");
    }
  }

  async loadKPIs() {
    try {
      this.kpiData = await Utils.apiCall("/reports/dashboard");
      this.updateKPIDisplay();
      this.updateTransactionsTable();
    } catch (error) {
      console.error("Failed to load KPIs:", error);
      this.displayKPIError();
    }
  }

  async loadLowStockAlerts() {
    try {
      this.lowStockData = await Utils.apiCall("/reports/low-stock");
      this.updateLowStockDisplay();
    } catch (error) {
      console.error("Failed to load low stock alerts:", error);
      this.displayLowStockError();
    }
  }

  updateKPIDisplay() {
    // Update KPI cards
    document.getElementById("totalProducts").textContent = Utils.formatNumber(
      this.kpiData.total_products || 0
    );
    document.getElementById("totalUnits").textContent = Utils.formatNumber(
      this.kpiData.total_units || 0
    );
    document.getElementById("lowStockCount").textContent = Utils.formatNumber(
      this.kpiData.low_stock_count || 0
    );
    document.getElementById("totalStores").textContent = Utils.formatNumber(
      this.kpiData.total_stores || 0
    );
  }

  updateTransactionsTable() {
    const tbody = document.getElementById("transactionsBody");
    if (!tbody) return;

    if (
      !this.kpiData.recent_transactions ||
      this.kpiData.recent_transactions.length === 0
    ) {
      tbody.innerHTML =
        '<tr><td colspan="6" class="no-data">No recent transactions</td></tr>';
      return;
    }

    tbody.innerHTML = "";
    this.kpiData.recent_transactions.forEach((transaction) => {
      const row = this.createTransactionRow(transaction);
      tbody.appendChild(row);
    });
  }

  createTransactionRow(transaction) {
    const row = document.createElement("tr");
    row.dataset.transactionId = transaction.id;

    // Add class based on transaction type
    const typeClass = transaction.type.toLowerCase();
    row.classList.add(`transaction-${typeClass}`);

    const typeIcon = this.getTransactionTypeIcon(transaction.type);
    const typeText = `${typeIcon} ${transaction.type}`;

    // Format quantity with before/after if available
    let quantityDisplay = Utils.formatNumber(transaction.quantity);
    
    // Check if we have quantity tracking data
    const hasPrevious = transaction.previous_quantity !== null && transaction.previous_quantity !== undefined;
    const hasNew = transaction.new_quantity !== null && transaction.new_quantity !== undefined;
    
    if (hasPrevious && hasNew) {
      const diff = transaction.new_quantity - transaction.previous_quantity;
      const diffText = diff > 0 ? `+${diff}` : `${diff}`;
      const arrowColor = diff > 0 ? '#4caf50' : '#f44336';
      quantityDisplay = `
        <div style="display: flex; flex-direction: column; gap: 2px;">
          <span style="font-weight: bold;">${Utils.formatNumber(Math.abs(diff))}</span>
          <span style="font-size: 0.85em; color: #666;">
            ${Utils.formatNumber(transaction.previous_quantity)} → ${Utils.formatNumber(transaction.new_quantity)}
            <span style="color: ${arrowColor}; font-weight: bold;">(${diffText})</span>
          </span>
        </div>
      `;
    } else {
      // Old transactions without quantity tracking - just show the quantity
      quantityDisplay = `<span style="font-weight: bold;">${Utils.formatNumber(transaction.quantity)}</span>`;
    }

    row.innerHTML = `
            <td>${Utils.formatDate(transaction.timestamp)}</td>
            <td>
                <strong>${transaction.product_name || "Unknown"}</strong><br>
                <small>SKU: ${transaction.product_sku || "N/A"}</small>
            </td>
            <td>${transaction.store_name || "Unknown"}</td>
            <td>${typeText}</td>
            <td>${quantityDisplay}</td>
            <td title="${transaction.note || ""}">${this.truncateText(
      transaction.note || "",
      30
    )}</td>
        `;

    return row;
  }

  getTransactionTypeIcon(type) {
    switch (type) {
      case "IN":
        return "📥";
      case "OUT":
        return "📤";
      case "TRANSFER":
        return "🔄";
      default:
        return "📋";
    }
  }

  truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + "...";
  }

  updateLowStockDisplay() {
    const container = document.getElementById("lowStockAlerts");
    if (!container) return;

    if (!this.lowStockData || this.lowStockData.length === 0) {
      container.innerHTML = '<div class="no-data">No low stock alerts</div>';
      return;
    }

    container.innerHTML = "";
    this.lowStockData.slice(0, 6).forEach((item) => {
      // Show max 6 items
      const alertDiv = this.createLowStockAlert(item);
      container.appendChild(alertDiv);
    });
  }

  createLowStockAlert(item) {
    const alertDiv = document.createElement("div");
    alertDiv.className = "alert-item";
    alertDiv.dataset.productId = item.product_id;
    alertDiv.dataset.storeId = item.store_id;
    alertDiv.dataset.currentQty = item.quantity;

    const urgencyClass = item.quantity === 0 ? "critical" : "warning";
    alertDiv.classList.add(`alert-${urgencyClass}`);

    alertDiv.innerHTML = `
            <h4>⚠️ ${item.product_name}</h4>
            <p><strong>Store:</strong> ${item.store_name}</p>
            <p><strong>Current Stock:</strong> <span class="current-qty">${item.quantity}</span></p>
            <p><strong>Reorder Level:</strong> ${item.reorder_level}</p>
            <p><strong>Shortage:</strong> <span class="shortage">${item.shortage} units</span></p>
            <div class="stock-change" style="display: none; margin-top: 8px; padding: 8px; background: #e3f2fd; border-radius: 4px; font-size: 0.9em;">
              <strong>Recent Change:</strong> <span class="change-text"></span>
            </div>
        `;

    return alertDiv;
  }

  handleInventoryUpdate(data) {
    console.log("Dashboard: Handling inventory update", data);

    // Show notification with previous and current quantity
    const product = DataManager.getProductById(data.product_id);
    const store = DataManager.getStoreById(data.store_id);
    const productName = product ? product.name : `Product ${data.product_id}`;
    const storeName = store ? store.name : `Store ${data.store_id}`;

    const previousQty = data.old_qty !== undefined ? data.old_qty : data.new_qty - data.delta;
    const changeText = data.new_qty > previousQty ? `+${data.new_qty - previousQty}` : `${data.new_qty - previousQty}`;

    Utils.showMessage(
      `Stock updated: ${productName} at ${storeName} - Previous: ${previousQty} → Current: ${data.new_qty} (${changeText})`,
      "info"
    );

    // Update low stock alert if it exists
    this.updateLowStockAlertDisplay(data.product_id, data.store_id, previousQty, data.new_qty);

    // Refresh data to get updated KPIs
    this.debounceRefresh();
  }

  handleTransferUpdate(data) {
    console.log("Dashboard: Handling transfer update", data);

    // Show notification with quantity changes
    const product = DataManager.getProductById(data.product_id);
    const fromStore = DataManager.getStoreById(data.from_store_id);
    const toStore = DataManager.getStoreById(data.to_store_id);

    const productName = product ? product.name : `Product ${data.product_id}`;
    const fromStoreName = fromStore
      ? fromStore.name
      : `Store ${data.from_store_id}`;
    const toStoreName = toStore ? toStore.name : `Store ${data.to_store_id}`;

    Utils.showMessage(
      `Transfer: ${data.quantity} ${productName} from ${fromStoreName} (${data.from_new_qty + data.quantity} → ${data.from_new_qty}) to ${toStoreName} (${data.to_new_qty - data.quantity} → ${data.to_new_qty})`,
      "info"
    );

    // Update low stock alerts for both stores
    if (data.from_new_qty !== undefined) {
      this.updateLowStockAlertDisplay(data.product_id, data.from_store_id, data.from_new_qty + data.quantity, data.from_new_qty);
    }
    if (data.to_new_qty !== undefined) {
      this.updateLowStockAlertDisplay(data.product_id, data.to_store_id, data.to_new_qty - data.quantity, data.to_new_qty);
    }

    // Refresh data to get updated KPIs
    this.debounceRefresh();
  }

  updateLowStockAlertDisplay(productId, storeId, previousQty, currentQty) {
    // Find the alert item for this product/store combination
    const alertItems = document.querySelectorAll('.alert-item');
    alertItems.forEach(item => {
      if (item.dataset.productId == productId && item.dataset.storeId == storeId) {
        // Update the current quantity display
        const currentQtySpan = item.querySelector('.current-qty');
        if (currentQtySpan) {
          currentQtySpan.textContent = currentQty;
          // Add animation
          currentQtySpan.style.animation = 'highlight 1s ease';
          setTimeout(() => {
            currentQtySpan.style.animation = '';
          }, 1000);
        }

        // Show the change notification
        const changeDiv = item.querySelector('.stock-change');
        const changeText = item.querySelector('.change-text');
        if (changeDiv && changeText) {
          const diff = currentQty - previousQty;
          const diffText = diff > 0 ? `+${diff}` : `${diff}`;
          const arrow = diff > 0 ? '↑' : '↓';
          const color = diff > 0 ? '#4caf50' : '#f44336';
          
          changeText.innerHTML = `${previousQty} → ${currentQty} <span style="color: ${color}; font-weight: bold;">(${arrow} ${diffText})</span>`;
          changeDiv.style.display = 'block';
          
          // Auto-hide after 10 seconds
          setTimeout(() => {
            changeDiv.style.display = 'none';
          }, 10000);
        }
      }
    });
  }

  // Debounced refresh to prevent too many API calls
  debounceRefresh = Utils.debounce(() => {
    this.refreshData();
  }, 2000);

  async refreshData() {
    try {
      await this.loadDashboardData();
    } catch (error) {
      console.error("Failed to refresh dashboard data:", error);
    }
  }

  setupPolling() {
    // Poll for updates every 30 seconds as fallback
    this.pollInterval = setInterval(async () => {
      if (!window.socket || !window.socket.connected) {
        try {
          const changes = await Utils.apiCall(
            `/changes?since=${this.lastUpdateTime}`
          );
          if (changes.changes && changes.changes.length > 0) {
            console.log("Polling: Found changes, refreshing dashboard");
            await this.refreshData();
          }
          this.lastUpdateTime = changes.timestamp;
        } catch (error) {
          console.error("Polling failed:", error);
        }
      }
    }, 30000);
  }

  displayKPIError() {
    document.getElementById("totalProducts").textContent = "Error";
    document.getElementById("totalUnits").textContent = "Error";
    document.getElementById("lowStockCount").textContent = "Error";
    document.getElementById("totalStores").textContent = "Error";

    const tbody = document.getElementById("transactionsBody");
    if (tbody) {
      tbody.innerHTML =
        '<tr><td colspan="6" class="error-message">Failed to load transactions</td></tr>';
    }
  }

  displayLowStockError() {
    const container = document.getElementById("lowStockAlerts");
    if (container) {
      container.innerHTML =
        '<div class="error-message">Failed to load low stock alerts</div>';
    }
  }

  destroy() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
    }
  }
}

// Global functions for button clicks
window.refreshLowStock = async function () {
  if (window.dashboard) {
    await window.dashboard.loadLowStockAlerts();
    Utils.showMessage("Low stock alerts refreshed", "success");
  }
};

// Initialize dashboard when page loads
document.addEventListener("DOMContentLoaded", () => {
  // Wait for app initialization
  setTimeout(() => {
    if (Auth.requireAuth()) {
      window.dashboard = new Dashboard();
    }
  }, 100);
});

// Cleanup on page unload
window.addEventListener("beforeunload", () => {
  if (window.dashboard) {
    window.dashboard.destroy();
  }
});
