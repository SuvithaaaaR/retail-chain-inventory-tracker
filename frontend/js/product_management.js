/**
 * Product Management JavaScript
 * Handles product CRUD operations and management
 */

class ProductManagement {
  constructor() {
    this.productsData = [];
    this.filteredProducts = [];

    this.init();
  }

  async init() {
    console.log("Initializing product management...");

    // Setup event listeners
    this.setupEventListeners();

    // Load products
    await this.loadProducts();

    console.log("Product management initialized");
  }

  setupEventListeners() {
    // Search functionality
    const searchInput = document.getElementById("productSearch");
    if (searchInput) {
      searchInput.addEventListener(
        "input",
        Utils.debounce(() => {
          this.filterProducts(searchInput.value);
        }, 300)
      );
    }

    // Form submissions
    this.setupFormHandlers();

    // Real-time event listeners
    window.addEventListener("productUpdate", (event) => {
      this.handleProductUpdate(event.detail);
    });
  }

  setupFormHandlers() {
    // Add product form
    const addForm = document.getElementById("addProductForm");
    if (addForm) {
      addForm.addEventListener("submit", (e) => {
        e.preventDefault();
        this.handleAddProduct();
      });
    }

    // Edit product form
    const editForm = document.getElementById("editProductForm");
    if (editForm) {
      editForm.addEventListener("submit", (e) => {
        e.preventDefault();
        this.handleEditProduct();
      });
    }
  }

  async loadProducts() {
    try {
      this.productsData = await Utils.apiCall("/products");
      this.filteredProducts = [...this.productsData];
      this.updateProductsDisplay();
    } catch (error) {
      console.error("Failed to load products:", error);
      Utils.showMessage("Failed to load products", "error");
      this.displayProductsError();
    }
  }

  updateProductsDisplay() {
    const tbody = document.getElementById("productsBody");
    if (!tbody) return;

    if (!this.filteredProducts || this.filteredProducts.length === 0) {
      tbody.innerHTML =
        '<tr><td colspan="8" class="no-data">No products found</td></tr>';
      return;
    }

    tbody.innerHTML = "";
    this.filteredProducts.forEach((product) => {
      const row = this.createProductRow(product);
      tbody.appendChild(row);
    });
  }

  createProductRow(product) {
    const row = document.createElement("tr");
    row.dataset.productId = product.id;

    row.innerHTML = `
            <td><strong>${product.sku}</strong></td>
            <td>${product.name}</td>
            <td>${product.category}</td>
            <td>${product.reorder_level}</td>
            <td>${Utils.formatCurrency(product.unit_cost)}</td>
            <td>${Utils.formatCurrency(product.selling_price)}</td>
            <td>${Utils.formatDate(product.created_at)}</td>
            <td class="actions-cell">
                ${(() => {
                  // Check permissions for product management
                  try {
                    const perms =
                      (currentUser && currentUser.permissions) || [];
                    const isAdmin = currentUser && currentUser.role === "admin";
                    const canManage = isAdmin || perms.includes("products");

                    if (canManage) {
                      // Managers can edit, only admins can delete
                      let buttons = `<button class="action-btn action-btn-edit" onclick="showEditProductModal(${product.id})">Edit</button>`;
                      if (isAdmin) {
                        buttons += `<button class="action-btn action-btn-delete" onclick="showDeleteProductModal(${product.id})">Delete</button>`;
                      }
                      return buttons;
                    }
                  } catch (e) {
                    // fallback: show nothing
                  }
                  return "";
                })()}
            </td>
        `;

    return row;
  }

  filterProducts(searchTerm) {
    if (!searchTerm.trim()) {
      this.filteredProducts = [...this.productsData];
    } else {
      const term = searchTerm.toLowerCase();
      this.filteredProducts = this.productsData.filter(
        (product) =>
          product.name.toLowerCase().includes(term) ||
          product.sku.toLowerCase().includes(term) ||
          product.category.toLowerCase().includes(term)
      );
    }
    this.updateProductsDisplay();
  }

  async handleAddProduct() {
    const formData = {
      sku: document.getElementById("addSku").value.trim(),
      name: document.getElementById("addName").value.trim(),
      category: document.getElementById("addCategory").value.trim(),
      reorder_level: parseInt(document.getElementById("addReorderLevel").value),
      unit_cost: parseFloat(document.getElementById("addUnitCost").value),
      selling_price: parseFloat(
        document.getElementById("addSellingPrice").value
      ),
    };

    // Validation
    if (!formData.sku || !formData.name || !formData.category) {
      Utils.showMessage("Please fill in all required fields", "error");
      return;
    }

    if (
      formData.reorder_level < 0 ||
      formData.unit_cost < 0 ||
      formData.selling_price < 0
    ) {
      Utils.showMessage("Values cannot be negative", "error");
      return;
    }

    try {
      const newProduct = await Utils.apiCall("/products", {
        method: "POST",
        body: JSON.stringify(formData),
      });

      Utils.showMessage("Product added successfully", "success");
      this.closeAddProductModal();

      // Add to local data
      this.productsData.push(newProduct);
      DataManager.products.push(newProduct);
      this.filteredProducts = [...this.productsData];
      this.updateProductsDisplay();
    } catch (error) {
      console.error("Add product failed:", error);
      Utils.showMessage(error.message || "Failed to add product", "error");
    }
  }

  async handleEditProduct() {
    const productId = parseInt(document.getElementById("editProductId").value);
    const formData = {
      name: document.getElementById("editName").value.trim(),
      category: document.getElementById("editCategory").value.trim(),
      reorder_level: parseInt(
        document.getElementById("editReorderLevel").value
      ),
      unit_cost: parseFloat(document.getElementById("editUnitCost").value),
      selling_price: parseFloat(
        document.getElementById("editSellingPrice").value
      ),
    };

    // Validation
    if (!formData.name || !formData.category) {
      Utils.showMessage("Please fill in all required fields", "error");
      return;
    }

    if (
      formData.reorder_level < 0 ||
      formData.unit_cost < 0 ||
      formData.selling_price < 0
    ) {
      Utils.showMessage("Values cannot be negative", "error");
      return;
    }

    try {
      const updatedProduct = await Utils.apiCall(`/products/${productId}`, {
        method: "PUT",
        body: JSON.stringify(formData),
      });

      Utils.showMessage("Product updated successfully", "success");
      this.closeEditProductModal();

      // Update local data
      this.updateLocalProduct(productId, updatedProduct);
    } catch (error) {
      console.error("Edit product failed:", error);
      Utils.showMessage(error.message || "Failed to update product", "error");
    }
  }

  async handleDeleteProduct(productId) {
    try {
      await Utils.apiCall(`/products/${productId}`, {
        method: "DELETE",
      });

      Utils.showMessage("Product deleted successfully", "success");
      this.closeDeleteProductModal();

      // Remove from local data
      this.removeLocalProduct(productId);
    } catch (error) {
      console.error("Delete product failed:", error);
      Utils.showMessage(error.message || "Failed to delete product", "error");
    }
  }

  updateLocalProduct(productId, updatedProduct) {
    // Update in products data
    const index = this.productsData.findIndex((p) => p.id === productId);
    if (index !== -1) {
      this.productsData[index] = updatedProduct;
    }

    // Update in DataManager
    const dmIndex = DataManager.products.findIndex((p) => p.id === productId);
    if (dmIndex !== -1) {
      DataManager.products[dmIndex] = updatedProduct;
    }

    // Update filtered products and display
    this.filteredProducts = [...this.productsData];
    this.updateProductsDisplay();
  }

  removeLocalProduct(productId) {
    // Remove from products data
    this.productsData = this.productsData.filter((p) => p.id !== productId);

    // Remove from DataManager
    DataManager.products = DataManager.products.filter(
      (p) => p.id !== productId
    );

    // Update filtered products and display
    this.filteredProducts = [...this.productsData];
    this.updateProductsDisplay();
  }

  getProductById(productId) {
    return this.productsData.find((p) => p.id === productId);
  }

  handleProductUpdate(data) {
    console.log("Product Management: Handling product update", data);

    switch (data.action) {
      case "created":
        if (data.product_data) {
          this.productsData.push(data.product_data);
          DataManager.products.push(data.product_data);
          this.filteredProducts = [...this.productsData];
          this.updateProductsDisplay();
        }
        break;

      case "updated":
        if (data.product_data) {
          this.updateLocalProduct(data.product_id, data.product_data);
        }
        break;

      case "deleted":
        this.removeLocalProduct(data.product_id);
        break;
    }
  }

  displayProductsError() {
    const tbody = document.getElementById("productsBody");
    if (tbody) {
      tbody.innerHTML =
        '<tr><td colspan="8" class="error-message">Failed to load products</td></tr>';
    }
  }

  closeAddProductModal() {
    ModalManager.closeModal("addProductModal");
    document.getElementById("addProductForm").reset();
  }

  closeEditProductModal() {
    ModalManager.closeModal("editProductModal");
    document.getElementById("editProductForm").reset();
  }

  closeDeleteProductModal() {
    ModalManager.closeModal("deleteProductModal");
  }
}

// Global functions for button clicks
window.showAddProductModal = function () {
  document.getElementById("addProductForm").reset();
  ModalManager.openModal("addProductModal");
};

window.showEditProductModal = function (productId) {
  const product = window.productManagement.getProductById(productId);

  if (!product) {
    Utils.showMessage("Product not found", "error");
    return;
  }

  document.getElementById("editProductId").value = product.id;
  document.getElementById("editSku").textContent = product.sku;
  document.getElementById("editName").value = product.name;
  document.getElementById("editCategory").value = product.category;
  document.getElementById("editReorderLevel").value = product.reorder_level;
  document.getElementById("editUnitCost").value = product.unit_cost;
  document.getElementById("editSellingPrice").value = product.selling_price;

  ModalManager.openModal("editProductModal");
};

window.showDeleteProductModal = function (productId) {
  const product = window.productManagement.getProductById(productId);

  if (!product) {
    Utils.showMessage("Product not found", "error");
    return;
  }

  document.getElementById("deleteProductId").value = product.id;
  document.getElementById("deleteProductName").textContent = product.name;
  document.getElementById("deleteProductSku").textContent = product.sku;

  ModalManager.openModal("deleteProductModal");
};

window.confirmDeleteProduct = async function () {
  const productId = parseInt(document.getElementById("deleteProductId").value);
  await window.productManagement.handleDeleteProduct(productId);
};

window.closeAddProductModal = function () {
  window.productManagement.closeAddProductModal();
};

window.closeEditProductModal = function () {
  window.productManagement.closeEditProductModal();
};

window.closeDeleteProductModal = function () {
  window.productManagement.closeDeleteProductModal();
};

window.refreshProducts = async function () {
  if (window.productManagement) {
    await window.productManagement.loadProducts();
    Utils.showMessage("Products refreshed", "success");
  }
};

// Initialize product management when page loads
document.addEventListener("DOMContentLoaded", () => {
  // Wait for app initialization
  setTimeout(() => {
    if (Auth.requireAuth()) {
      window.productManagement = new ProductManagement();
    }
  }, 100);
});
