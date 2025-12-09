/**
 * Store Inventory JavaScript
 * Handles store inventory management, stock updates, and transfers
 */

class StoreInventory {
  constructor() {
    this.selectedStoreId = null;
    this.inventoryData = [];
    this.currentJoinedStore = null;

    this.init();
  }

  async init() {
    console.log("Initializing store inventory...");

    // Setup event listeners
    this.setupEventListeners();

    // Populate store dropdown
    await this.populateStoreDropdown();

    console.log("Store inventory initialized");
  }

  setupEventListeners() {
    // Store selection change
    const storeSelect = document.getElementById("storeSelect");
    if (storeSelect) {
      storeSelect.addEventListener("change", (e) => {
        this.handleStoreChange(e.target.value);
      });
    }

    // Real-time event listeners
    window.addEventListener("inventoryUpdate", (event) => {
      this.handleInventoryUpdate(event.detail);
    });

    window.addEventListener("transferUpdate", (event) => {
      this.handleTransferUpdate(event.detail);
    });

    // Form submissions
    this.setupFormHandlers();

    // Search functionality
    this.setupSearch();
  }

  setupFormHandlers() {
    // Update stock form
    const updateForm = document.getElementById("updateStockForm");
    if (updateForm) {
      updateForm.addEventListener("submit", (e) => {
        e.preventDefault();
        this.handleStockUpdate();
      });
    }

    // Transfer stock form
    const transferForm = document.getElementById("transferStockForm");
    if (transferForm) {
      transferForm.addEventListener("submit", (e) => {
        e.preventDefault();
        this.handleStockTransfer();
      });
    }
  }

  setupSearch() {
    // Add search input if it doesn't exist
    const controlsSection = document.querySelector(".controls-section");
    if (controlsSection && !document.getElementById("inventorySearch")) {
      const searchDiv = document.createElement("div");
      searchDiv.className = "search-container";
      searchDiv.innerHTML = `
                <input type="text" id="inventorySearch" class="form-control" 
                       placeholder="Search products..." style="display: none;">
            `;
      controlsSection.appendChild(searchDiv);

      const searchInput = document.getElementById("inventorySearch");
      searchInput.addEventListener(
        "input",
        Utils.debounce(() => {
          this.filterInventoryTable(searchInput.value);
        }, 300)
      );
    }
  }

  async populateStoreDropdown() {
    const storeSelect = document.getElementById("storeSelect");
    if (!storeSelect) return;

    storeSelect.innerHTML = '<option value="">Select a store...</option>';

    DataManager.stores.forEach((store) => {
      const option = document.createElement("option");
      option.value = store.id;
      option.textContent = `${store.name} - ${store.location}`;
      storeSelect.appendChild(option);
    });
  }

  async handleStoreChange(storeId) {
    if (this.currentJoinedStore) {
      WebSocketManager.leaveStoreRoom(this.currentJoinedStore);
    }

    this.selectedStoreId = storeId ? parseInt(storeId) : null;

    if (this.selectedStoreId) {
      await this.loadInventory();
      WebSocketManager.joinStoreRoom(this.selectedStoreId);
      this.currentJoinedStore = this.selectedStoreId;

      // Show search input
      const searchInput = document.getElementById("inventorySearch");
      if (searchInput) {
        searchInput.style.display = "block";
      }
    } else {
      this.clearInventoryTable();
      const searchInput = document.getElementById("inventorySearch");
      if (searchInput) {
        searchInput.style.display = "none";
      }
    }

    // Update refresh button state
    const refreshBtn = document.getElementById("refreshBtn");
    if (refreshBtn) {
      refreshBtn.disabled = !this.selectedStoreId;
    }
  }

  async loadInventory() {
    if (!this.selectedStoreId) return;

    try {
      this.inventoryData = await Utils.apiCall(
        `/inventory?store_id=${this.selectedStoreId}`
      );
      this.updateInventoryDisplay();
      this.updateTitle();
    } catch (error) {
      console.error("Failed to load inventory:", error);
      Utils.showMessage("Failed to load inventory", "error");
      this.displayInventoryError();
    }
  }

  updateTitle() {
    const titleElement = document.getElementById("inventoryTitle");
    if (titleElement && this.selectedStoreId) {
      const store = DataManager.getStoreById(this.selectedStoreId);
      const storeName = store ? store.name : `Store ${this.selectedStoreId}`;
      titleElement.textContent = `Inventory for ${storeName}`;
    }
  }

  updateInventoryDisplay() {
    const tbody = document.getElementById("inventoryBody");
    if (!tbody) return;

    if (!this.inventoryData || this.inventoryData.length === 0) {
      tbody.innerHTML =
        '<tr><td colspan="6" class="no-data">No inventory items found for this store</td></tr>';
      return;
    }

    tbody.innerHTML = "";
    this.inventoryData.forEach((item) => {
      const row = this.createInventoryRow(item);
      tbody.appendChild(row);
    });
  }

  createInventoryRow(item) {
    const row = document.createElement("tr");
    row.dataset.productId = item.product_id;
    row.dataset.storeId = item.store_id;

    // Determine status
    const status = this.getStockStatus(item.quantity, item.reorder_level);
    const statusClass = status.toLowerCase().replace(" ", "-");

    // Check permissions - only show action buttons if user has 'inventory' permission
    const currentUser = Auth.currentUser;
    const hasInventoryPermission = currentUser && (
      currentUser.role === 'admin' || 
      (currentUser.permissions && currentUser.permissions.includes('inventory'))
    );

    // Build actions HTML based on permissions
    let actionsHTML = '';
    if (hasInventoryPermission) {
      actionsHTML = `
        <button class="action-btn action-btn-update" onclick="showUpdateStockModal(${item.product_id}, ${item.store_id})">
          Update
        </button>
        <button class="action-btn action-btn-transfer" onclick="showTransferStockModal(${item.product_id}, ${item.store_id})">
          Transfer
        </button>
      `;
    } else {
      actionsHTML = '<span class="text-muted">View Only</span>';
    }

    row.innerHTML = `
            <td>${item.product_sku || "N/A"}</td>
            <td>
                <strong>${item.product_name || "Unknown Product"}</strong>
            </td>
            <td class="quantity-cell">${Utils.formatNumber(item.quantity)}</td>
            <td>${item.reorder_level}</td>
            <td class="status-${statusClass}">${status}</td>
            <td class="actions-cell">
                ${actionsHTML}
            </td>
        `;

    return row;
  }

  getStockStatus(quantity, reorderLevel) {
    if (quantity === 0) return "Out of Stock";
    if (quantity <= reorderLevel) return "Low Stock";
    return "OK";
  }

  filterInventoryTable(searchTerm) {
    const tbody = document.getElementById("inventoryBody");
    if (!tbody) return;

    const rows = tbody.querySelectorAll("tr");
    const term = searchTerm.toLowerCase();

    rows.forEach((row) => {
      const text = row.textContent.toLowerCase();
      row.style.display = text.includes(term) ? "" : "none";
    });
  }

  clearInventoryTable() {
    const tbody = document.getElementById("inventoryBody");
    if (tbody) {
      tbody.innerHTML =
        '<tr><td colspan="6" class="no-data">Please select a store to view inventory</td></tr>';
    }

    const titleElement = document.getElementById("inventoryTitle");
    if (titleElement) {
      titleElement.textContent = "Select a store to view inventory";
    }
  }

  displayInventoryError() {
    const tbody = document.getElementById("inventoryBody");
    if (tbody) {
      tbody.innerHTML =
        '<tr><td colspan="6" class="error-message">Failed to load inventory data</td></tr>';
    }
  }

  async handleStockUpdate() {
    const productId = document.getElementById("updateProductId").value;
    const storeId = document.getElementById("updateStoreId").value;
    const stockChange = parseInt(document.getElementById("stockChange").value);
    const reason = document.getElementById("updateReason").value;

    if (!stockChange || !reason.trim()) {
      Utils.showMessage("Please enter stock change and reason", "error");
      return;
    }

    try {
      const result = await Utils.apiCall("/inventory/update", {
        method: "POST",
        body: JSON.stringify({
          store_id: parseInt(storeId),
          product_id: parseInt(productId),
          delta: stockChange,
          reason: reason,
        }),
      });

      Utils.showMessage("Stock updated successfully", "success");
      this.closeUpdateModal();

      // Update local data
      this.updateLocalInventoryItem(parseInt(productId), result.new_quantity);
    } catch (error) {
      console.error("Stock update failed:", error);
      Utils.showMessage(error.message || "Failed to update stock", "error");
    }
  }

  async handleStockTransfer() {
    const productId = document.getElementById("transferProductId").value;
    const fromStoreId = document.getElementById("transferFromStore").value;
    const toStoreId = document.getElementById("transferToStore").value;
    const quantity = parseInt(
      document.getElementById("transferQuantity").value
    );
    const reason = document.getElementById("transferReason").value;

    if (!toStoreId || !quantity || !reason.trim()) {
      Utils.showMessage("Please fill all required fields", "error");
      return;
    }

    if (parseInt(fromStoreId) === parseInt(toStoreId)) {
      Utils.showMessage("Cannot transfer to the same store", "error");
      return;
    }

    try {
      const result = await Utils.apiCall("/inventory/transfer", {
        method: "POST",
        body: JSON.stringify({
          from_store: parseInt(fromStoreId),
          to_store: parseInt(toStoreId),
          product_id: parseInt(productId),
          quantity: quantity,
          reason: reason,
        }),
      });

      Utils.showMessage("Stock transferred successfully", "success");
      this.closeTransferModal();

      // Update local data for the from store
      if (parseInt(fromStoreId) === this.selectedStoreId) {
        this.updateLocalInventoryItem(
          parseInt(productId),
          result.from_store.new_quantity
        );
      }
    } catch (error) {
      console.error("Stock transfer failed:", error);
      Utils.showMessage(error.message || "Failed to transfer stock", "error");
    }
  }

  updateLocalInventoryItem(productId, newQuantity) {
    // Update in local data
    const item = this.inventoryData.find(
      (item) => item.product_id === productId
    );
    if (item) {
      item.quantity = newQuantity;
    }

    // Update in table
    const row = document.querySelector(`tr[data-product-id="${productId}"]`);
    if (row) {
      const quantityCell = row.querySelector(".quantity-cell");
      const statusCell = row.querySelector('[class*="status-"]');

      if (quantityCell) {
        quantityCell.textContent = Utils.formatNumber(newQuantity);
      }

      if (statusCell && item) {
        const status = this.getStockStatus(newQuantity, item.reorder_level);
        const statusClass = status.toLowerCase().replace(" ", "-");
        statusCell.className = `status-${statusClass}`;
        statusCell.textContent = status;
      }
    }
  }

  handleInventoryUpdate(data) {
    console.log("Store Inventory: Handling inventory update", data);

    // Only update if it's for the currently selected store
    if (data.store_id === this.selectedStoreId) {
      this.updateLocalInventoryItem(data.product_id, data.new_qty);

      const product = DataManager.getProductById(data.product_id);
      const productName = product ? product.name : `Product ${data.product_id}`;
      Utils.showMessage(
        `${productName} stock updated to ${data.new_qty}`,
        "info"
      );
    }
  }

  handleTransferUpdate(data) {
    console.log("Store Inventory: Handling transfer update", data);

    // Update if this store is involved in the transfer
    if (
      data.from_store_id === this.selectedStoreId ||
      data.to_store_id === this.selectedStoreId
    ) {
      // Refresh inventory to get accurate quantities
      this.loadInventory();
    }
  }

  closeUpdateModal() {
    ModalManager.closeModal("updateStockModal");
    document.getElementById("updateStockForm").reset();
  }

  closeTransferModal() {
    ModalManager.closeModal("transferStockModal");
    document.getElementById("transferStockForm").reset();
  }
}

// Global functions for button clicks
window.showUpdateStockModal = function (productId, storeId) {
  const item = window.storeInventory.inventoryData.find(
    (item) => item.product_id === productId && item.store_id === storeId
  );

  if (!item) {
    Utils.showMessage("Item not found", "error");
    return;
  }

  document.getElementById("updateProductId").value = productId;
  document.getElementById("updateStoreId").value = storeId;
  document.getElementById("updateProductName").textContent =
    item.product_name || "Unknown Product";
  document.getElementById("updateCurrentStock").textContent =
    Utils.formatNumber(item.quantity);
  document.getElementById("stockChange").value = "";
  document.getElementById("updateReason").value = "";

  ModalManager.openModal("updateStockModal");
};

window.showTransferStockModal = function (productId, storeId) {
  const item = window.storeInventory.inventoryData.find(
    (item) => item.product_id === productId && item.store_id === storeId
  );

  if (!item) {
    Utils.showMessage("Item not found", "error");
    return;
  }

  document.getElementById("transferProductId").value = productId;
  document.getElementById("transferFromStore").value = storeId;
  document.getElementById("transferProductName").textContent =
    item.product_name || "Unknown Product";

  const store = DataManager.getStoreById(storeId);
  document.getElementById("transferFromStoreName").textContent = store
    ? store.name
    : `Store ${storeId}`;
  document.getElementById("transferAvailableStock").textContent =
    Utils.formatNumber(item.quantity);

  // Populate destination store dropdown
  const transferToSelect = document.getElementById("transferToStore");
  transferToSelect.innerHTML =
    '<option value="">Select destination store</option>';

  DataManager.stores.forEach((store) => {
    if (store.id !== storeId) {
      const option = document.createElement("option");
      option.value = store.id;
      option.textContent = `${store.name} - ${store.location}`;
      transferToSelect.appendChild(option);
    }
  });

  document.getElementById("transferQuantity").value = "";
  document.getElementById("transferQuantity").max = item.quantity;
  document.getElementById("transferReason").value = "";

  ModalManager.openModal("transferStockModal");
};

window.closeUpdateModal = function () {
  window.storeInventory.closeUpdateModal();
};

window.closeTransferModal = function () {
  window.storeInventory.closeTransferModal();
};

window.refreshInventory = async function () {
  if (window.storeInventory && window.storeInventory.selectedStoreId) {
    await window.storeInventory.loadInventory();
    Utils.showMessage("Inventory refreshed", "success");
  }
};

// Initialize store inventory when page loads
document.addEventListener("DOMContentLoaded", () => {
  // Wait for app initialization
  setTimeout(() => {
    if (Auth.requireAuth()) {
      window.storeInventory = new StoreInventory();
    }
  }, 100);
});
