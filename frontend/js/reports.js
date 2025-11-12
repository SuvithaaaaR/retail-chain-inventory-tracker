/**
 * Reports JavaScript
 * Handles report generation, filtering, and data visualization
 */

class Reports {
  constructor() {
    this.currentReportData = null;
    this.currentLowStockData = null;
    this.currentFilters = {
      startDate: null,
      endDate: null,
      storeId: null,
    };

    this.init();
  }

  async init() {
    console.log("Initializing reports...");

    // Setup event listeners
    this.setupEventListeners();

    // Populate store dropdown
    this.populateStoreDropdown();

    // Set default date range (last 30 days)
    this.setDefaultDateRange();

    // Load initial inventory summary
    await this.loadInventorySummary();

    console.log("Reports initialized");
  }

  setupEventListeners() {
    // Filter form changes
    const filterInputs = document.querySelectorAll(
      "#reportFiltersForm input, #reportFiltersForm select"
    );
    filterInputs.forEach((input) => {
      input.addEventListener("change", () => {
        this.updateFilters();
      });
    });
  }

  populateStoreDropdown() {
    const storeSelect = document.getElementById("reportStoreSelect");
    if (!storeSelect) return;

    DataManager.populateStoreSelect(storeSelect, true);
  }

  setDefaultDateRange() {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);

    const startInput = document.getElementById("startDate");
    const endInput = document.getElementById("endDate");

    if (startInput) {
      startInput.value = startDate.toISOString().split("T")[0];
    }
    if (endInput) {
      endInput.value = endDate.toISOString().split("T")[0];
    }

    this.updateFilters();
  }

  updateFilters() {
    const startDate = document.getElementById("startDate").value;
    const endDate = document.getElementById("endDate").value;
    const storeId = document.getElementById("reportStoreSelect").value;

    this.currentFilters = {
      startDate: startDate || null,
      endDate: endDate || null,
      storeId: storeId || null,
    };

    this.updateReportPeriodDisplay();
  }

  updateReportPeriodDisplay() {
    const periodElement = document.getElementById("reportPeriod");
    if (!periodElement) return;

    let periodText = "";
    if (this.currentFilters.startDate || this.currentFilters.endDate) {
      const start = this.currentFilters.startDate
        ? new Date(this.currentFilters.startDate).toLocaleDateString()
        : "Beginning";
      const end = this.currentFilters.endDate
        ? new Date(this.currentFilters.endDate).toLocaleDateString()
        : "Now";
      periodText = `Period: ${start} - ${end}`;
    }

    if (this.currentFilters.storeId) {
      const store = DataManager.getStoreById(
        parseInt(this.currentFilters.storeId)
      );
      const storeName = store
        ? store.name
        : `Store ${this.currentFilters.storeId}`;
      periodText += periodText
        ? ` | Store: ${storeName}`
        : `Store: ${storeName}`;
    }

    periodElement.textContent = periodText || "All data";
  }

  async generateStockReport() {
    try {
      // Build query parameters
      const params = new URLSearchParams();
      if (this.currentFilters.startDate) {
        params.append(
          "start_date",
          this.currentFilters.startDate + "T00:00:00"
        );
      }
      if (this.currentFilters.endDate) {
        params.append("end_date", this.currentFilters.endDate + "T23:59:59");
      }
      if (this.currentFilters.storeId) {
        params.append("store_id", this.currentFilters.storeId);
      }

      const url = `/reports/stock${
        params.toString() ? "?" + params.toString() : ""
      }`;
      this.currentReportData = await Utils.apiCall(url);

      this.updateStockReportDisplay();
      Utils.showMessage("Stock report generated successfully", "success");
    } catch (error) {
      console.error("Failed to generate stock report:", error);
      Utils.showMessage("Failed to generate stock report", "error");
      this.displayStockReportError();
    }
  }

  updateStockReportDisplay() {
    if (!this.currentReportData) return;

    // Update summary cards
    this.updateSummaryCards();

    // Update transactions table
    this.updateStockReportTable();
  }

  updateSummaryCards() {
    const totals = this.currentReportData.totals || {};

    document.getElementById("totalStockIn").textContent = Utils.formatNumber(
      totals.total_in || 0
    );
    document.getElementById("totalStockOut").textContent = Utils.formatNumber(
      totals.total_out || 0
    );
    document.getElementById("netChange").textContent = Utils.formatNumber(
      totals.net_change || 0
    );
    document.getElementById("totalTransfers").textContent = Utils.formatNumber(
      (totals.total_transfers_in || 0) + (totals.total_transfers_out || 0)
    );

    // Color code net change
    const netChangeElement = document.getElementById("netChange");
    const netChange = totals.net_change || 0;
    if (netChange > 0) {
      netChangeElement.style.color = "#27ae60";
    } else if (netChange < 0) {
      netChangeElement.style.color = "#e74c3c";
    } else {
      netChangeElement.style.color = "#7f8c8d";
    }
  }

  updateStockReportTable() {
    const tbody = document.getElementById("stockReportBody");
    if (!tbody) return;

    const transactions = this.currentReportData.transactions || [];

    if (transactions.length === 0) {
      tbody.innerHTML =
        '<tr><td colspan="7" class="no-data">No transactions found for the selected period</td></tr>';
      return;
    }

    tbody.innerHTML = "";
    transactions.forEach((transaction) => {
      const row = this.createStockReportRow(transaction);
      tbody.appendChild(row);
    });
  }

  createStockReportRow(transaction) {
    const row = document.createElement("tr");

    const typeIcon = this.getTransactionTypeIcon(transaction.type);
    const typeText = `${typeIcon} ${transaction.type}`;

    row.innerHTML = `
            <td>${Utils.formatDate(transaction.timestamp)}</td>
            <td>
                <strong>${transaction.product_name || "Unknown"}</strong><br>
                <small>SKU: ${transaction.product_sku || "N/A"}</small>
            </td>
            <td>${transaction.store_name || "Unknown"}</td>
            <td>${typeText}</td>
            <td>${Utils.formatNumber(transaction.quantity)}</td>
            <td title="${transaction.note || ""}">${this.truncateText(
      transaction.note || "",
      40
    )}</td>
            <td>${transaction.user_name || "System"}</td>
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

  async generateLowStockReport() {
    try {
      const params = new URLSearchParams();
      if (this.currentFilters.storeId) {
        params.append("store_id", this.currentFilters.storeId);
      }

      const url = `/reports/low-stock${
        params.toString() ? "?" + params.toString() : ""
      }`;
      this.currentLowStockData = await Utils.apiCall(url);

      this.updateLowStockDisplay();
      Utils.showMessage("Low stock report generated successfully", "success");
    } catch (error) {
      console.error("Failed to generate low stock report:", error);
      Utils.showMessage("Failed to generate low stock report", "error");
      this.displayLowStockError();
    }
  }

  updateLowStockDisplay() {
    const container = document.getElementById("lowStockGrid");
    const summary = document.getElementById("lowStockSummary");

    if (!container || !this.currentLowStockData) return;

    // Update summary
    if (summary) {
      const count = this.currentLowStockData.length;
      const storeText = this.currentFilters.storeId
        ? ` in ${
            DataManager.getStoreById(parseInt(this.currentFilters.storeId))
              ?.name || "selected store"
          }`
        : " across all stores";
      summary.textContent = `${count} low stock alert${
        count !== 1 ? "s" : ""
      }${storeText}`;
    }

    if (this.currentLowStockData.length === 0) {
      container.innerHTML =
        '<div class="no-data">No low stock alerts found</div>';
      return;
    }

    container.innerHTML = "";
    this.currentLowStockData.forEach((item) => {
      const alertDiv = this.createLowStockAlert(item);
      container.appendChild(alertDiv);
    });
  }

  createLowStockAlert(item) {
    const alertDiv = document.createElement("div");
    alertDiv.className = "low-stock-item";

    const urgencyClass = item.quantity === 0 ? "critical" : "warning";
    alertDiv.classList.add(`alert-${urgencyClass}`);

    alertDiv.innerHTML = `
            <h4>⚠️ ${item.product_name}</h4>
            <div class="stock-info">
                <span><strong>Store:</strong> ${item.store_name}</span>
            </div>
            <div class="stock-info">
                <span><strong>Current:</strong> ${item.quantity}</span>
                <span><strong>Reorder:</strong> ${item.reorder_level}</span>
            </div>
            <div class="stock-info">
                <span><strong>SKU:</strong> ${item.product_sku}</span>
                <span class="shortage"><strong>Short:</strong> ${item.shortage} units</span>
            </div>
        `;

    return alertDiv;
  }

  async loadInventorySummary() {
    try {
      // Get stores and their inventory summary
      const stores = DataManager.stores;
      const summaryData = [];

      for (const store of stores) {
        try {
          const inventory = await Utils.apiCall(
            `/inventory?store_id=${store.id}`
          );
          const lowStock = await Utils.apiCall(
            `/reports/low-stock?store_id=${store.id}`
          );

          summaryData.push({
            store: store,
            totalProducts: inventory.length,
            totalUnits: inventory.reduce((sum, item) => sum + item.quantity, 0),
            lowStockItems: lowStock.length,
            lastUpdated: new Date().toISOString(),
          });
        } catch (error) {
          console.error(`Failed to load summary for store ${store.id}:`, error);
          summaryData.push({
            store: store,
            totalProducts: "Error",
            totalUnits: "Error",
            lowStockItems: "Error",
            lastUpdated: new Date().toISOString(),
          });
        }
      }

      this.updateInventorySummaryTable(summaryData);
    } catch (error) {
      console.error("Failed to load inventory summary:", error);
      this.displayInventorySummaryError();
    }
  }

  updateInventorySummaryTable(summaryData) {
    const tbody = document.getElementById("inventorySummaryBody");
    if (!tbody) return;

    if (!summaryData || summaryData.length === 0) {
      tbody.innerHTML =
        '<tr><td colspan="5" class="no-data">No inventory data available</td></tr>';
      return;
    }

    tbody.innerHTML = "";
    summaryData.forEach((summary) => {
      const row = this.createInventorySummaryRow(summary);
      tbody.appendChild(row);
    });
  }

  createInventorySummaryRow(summary) {
    const row = document.createElement("tr");

    row.innerHTML = `
            <td>
                <strong>${summary.store.name}</strong><br>
                <small>${summary.store.location}</small>
            </td>
            <td>${
              summary.totalProducts !== "Error"
                ? Utils.formatNumber(summary.totalProducts)
                : "Error"
            }</td>
            <td>${
              summary.totalUnits !== "Error"
                ? Utils.formatNumber(summary.totalUnits)
                : "Error"
            }</td>
            <td class="${
              summary.lowStockItems > 0 ? "status-warning" : "status-ok"
            }">
                ${
                  summary.lowStockItems !== "Error"
                    ? Utils.formatNumber(summary.lowStockItems)
                    : "Error"
                }
            </td>
            <td>${Utils.formatDate(summary.lastUpdated)}</td>
        `;

    return row;
  }

  async exportToCSV() {
    if (!this.currentReportData || !this.currentReportData.transactions) {
      Utils.showMessage(
        "No report data to export. Please generate a stock report first.",
        "warning"
      );
      return;
    }

    try {
      const csvContent = this.generateCSVContent();
      const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
      const link = document.createElement("a");

      if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute("href", url);
        link.setAttribute(
          "download",
          `stock_report_${new Date().toISOString().split("T")[0]}.csv`
        );
        link.style.visibility = "hidden";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        Utils.showMessage("Report exported to CSV successfully", "success");
      } else {
        Utils.showMessage("CSV export not supported in this browser", "error");
      }
    } catch (error) {
      console.error("CSV export failed:", error);
      Utils.showMessage("Failed to export CSV", "error");
    }
  }

  generateCSVContent() {
    const headers = [
      "Date/Time",
      "Product Name",
      "SKU",
      "Store",
      "Type",
      "Quantity",
      "Note",
      "User",
    ];
    const rows = [headers.join(",")];

    this.currentReportData.transactions.forEach((transaction) => {
      const row = [
        `"${Utils.formatDate(transaction.timestamp)}"`,
        `"${transaction.product_name || "Unknown"}"`,
        `"${transaction.product_sku || "N/A"}"`,
        `"${transaction.store_name || "Unknown"}"`,
        `"${transaction.type}"`,
        transaction.quantity,
        `"${(transaction.note || "").replace(/"/g, '""')}"`,
        `"${transaction.user_name || "System"}"`,
      ];
      rows.push(row.join(","));
    });

    return rows.join("\n");
  }

  displayStockReportError() {
    const tbody = document.getElementById("stockReportBody");
    if (tbody) {
      tbody.innerHTML =
        '<tr><td colspan="7" class="error-message">Failed to load stock report</td></tr>';
    }

    // Reset summary cards
    document.getElementById("totalStockIn").textContent = "Error";
    document.getElementById("totalStockOut").textContent = "Error";
    document.getElementById("netChange").textContent = "Error";
    document.getElementById("totalTransfers").textContent = "Error";
  }

  displayLowStockError() {
    const container = document.getElementById("lowStockGrid");
    if (container) {
      container.innerHTML =
        '<div class="error-message">Failed to load low stock report</div>';
    }
  }

  displayInventorySummaryError() {
    const tbody = document.getElementById("inventorySummaryBody");
    if (tbody) {
      tbody.innerHTML =
        '<tr><td colspan="5" class="error-message">Failed to load inventory summary</td></tr>';
    }
  }
}

// Global functions for button clicks
window.generateStockReport = async function () {
  if (window.reports) {
    await window.reports.generateStockReport();
  }
};

window.generateLowStockReport = async function () {
  if (window.reports) {
    await window.reports.generateLowStockReport();
  }
};

window.exportToCSV = async function () {
  if (window.reports) {
    await window.reports.exportToCSV();
  }
};

window.refreshReport = async function () {
  if (window.reports && window.reports.currentReportData) {
    await window.reports.generateStockReport();
    Utils.showMessage("Report refreshed", "success");
  }
};

window.refreshInventorySummary = async function () {
  if (window.reports) {
    await window.reports.loadInventorySummary();
    Utils.showMessage("Inventory summary refreshed", "success");
  }
};

// Initialize reports when page loads
document.addEventListener("DOMContentLoaded", () => {
  // Wait for app initialization
  setTimeout(() => {
    if (Auth.requireAuth()) {
      window.reports = new Reports();
    }
  }, 100);
});
