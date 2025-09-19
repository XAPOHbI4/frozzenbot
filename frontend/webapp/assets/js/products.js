// Products Display and Management
class ProductsManager {
    constructor() {
        this.products = [];
        this.categories = [];
        this.currentCategory = 'all';

        this.elements = {
            productsGrid: document.getElementById('products-grid'),
            emptyState: document.getElementById('empty-state'),
            categoriesFilter: document.querySelector('.categories-filter'),
            productModal: document.getElementById('product-modal'),
            closeProductBtn: document.getElementById('close-product'),
            productDetail: document.getElementById('product-detail')
        };

        this.init();
    }

    async init() {
        try {
            // Load categories and products
            await Promise.all([
                this.loadCategories(),
                this.loadProducts()
            ]);

            this.setupEventListeners();
            this.renderProducts();

        } catch (error) {
            console.error('Failed to initialize products:', error);
            this.showEmptyState();
        }
    }

    async loadCategories() {
        try {
            this.categories = await window.api.getCategories();
            this.renderCategoriesFilter();
        } catch (error) {
            console.error('Failed to load categories:', error);
        }
    }

    async loadProducts() {
        try {
            this.products = await window.api.getProducts();
        } catch (error) {
            console.error('Failed to load products:', error);
            this.products = [];
        }
    }

    setupEventListeners() {
        // Category filter buttons
        this.elements.categoriesFilter?.addEventListener('click', (e) => {
            if (e.target.classList.contains('category-btn')) {
                this.handleCategoryFilter(e.target);
            }
        });

        // Product modal close
        this.elements.closeProductBtn?.addEventListener('click', () => {
            this.hideProductModal();
        });

        // Close modal on backdrop click
        this.elements.productModal?.addEventListener('click', (e) => {
            if (e.target === this.elements.productModal) {
                this.hideProductModal();
            }
        });
    }

    renderCategoriesFilter() {
        if (!this.elements.categoriesFilter) return;

        // Clear existing buttons except "All"
        const allButton = this.elements.categoriesFilter.querySelector('[data-category="all"]');
        this.elements.categoriesFilter.innerHTML = '';

        // Add "All" button back
        if (allButton) {
            this.elements.categoriesFilter.appendChild(allButton);
        }

        // Add category buttons
        this.categories.forEach(category => {
            const button = document.createElement('button');
            button.className = 'category-btn';
            button.dataset.category = category.id;
            button.textContent = category.name;
            this.elements.categoriesFilter.appendChild(button);
        });
    }

    handleCategoryFilter(button) {
        // Update active state
        this.elements.categoriesFilter?.querySelectorAll('.category-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        button.classList.add('active');

        // Update current category and re-render
        this.currentCategory = button.dataset.category;
        this.renderProducts();
    }

    renderProducts() {
        if (!this.elements.productsGrid) return;

        // Filter products by category
        const filteredProducts = this.currentCategory === 'all'
            ? this.products
            : this.products.filter(product => product.category.id == this.currentCategory);

        // Clear grid
        this.elements.productsGrid.innerHTML = '';

        // Show empty state if no products
        if (filteredProducts.length === 0) {
            this.showEmptyState();
            return;
        }

        this.hideEmptyState();

        // Render product cards
        filteredProducts.forEach(product => {
            const productCard = this.createProductCard(product);
            this.elements.productsGrid.appendChild(productCard);
        });
    }

    createProductCard(product) {
        const card = document.createElement('div');
        card.className = 'product-card';

        card.innerHTML = `
            <div class="product-image">
                ${product.imageUrl ?
                    `<img src="${product.imageUrl}" alt="${product.name}" onerror="this.parentElement.innerHTML='${window.AppConfig.DEFAULT_PRODUCT_IMAGE}'">`
                    : window.AppConfig.DEFAULT_PRODUCT_IMAGE
                }
            </div>
            <div class="product-info">
                <h3 class="product-name">${product.name}</h3>
                <p class="product-description">${product.description}</p>
                <div class="product-footer">
                    <div>
                        <div class="product-price">${product.formattedPrice}</div>
                        ${product.formattedWeight ?
                            `<div class="product-weight">${product.formattedWeight}</div>`
                            : ''
                        }
                    </div>
                    <button class="add-to-cart-btn" data-product-id="${product.id}">
                        В корзину
                    </button>
                </div>
            </div>
        `;

        // Add event listeners
        const addToCartBtn = card.querySelector('.add-to-cart-btn');
        addToCartBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.handleAddToCart(product);
        });

        // Click on card to show details
        card.addEventListener('click', () => {
            this.showProductModal(product);
        });

        return card;
    }

    handleAddToCart(product) {
        window.cartService.addProduct(product, 1);

        // Visual feedback
        const button = document.querySelector(`[data-product-id="${product.id}"]`);
        if (button) {
            const originalText = button.textContent;
            button.textContent = '✓ Добавлено';
            button.style.background = 'var(--success)';

            setTimeout(() => {
                button.textContent = originalText;
                button.style.background = '';
            }, 1000);
        }
    }

    showProductModal(product) {
        if (!this.elements.productModal || !this.elements.productDetail) return;

        this.elements.productDetail.innerHTML = `
            <div class="product-detail-image">
                ${product.imageUrl ?
                    `<img src="${product.imageUrl}" alt="${product.name}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 12px;" onerror="this.parentElement.innerHTML='${window.AppConfig.DEFAULT_PRODUCT_IMAGE}'">`
                    : window.AppConfig.DEFAULT_PRODUCT_IMAGE
                }
            </div>
            <h2 class="product-detail-name">${product.name}</h2>
            <p class="product-detail-description">${product.description}</p>
            <div class="product-detail-price">${product.formattedPrice}</div>
            ${product.formattedWeight ?
                `<div class="product-detail-weight">${product.formattedWeight}</div>`
                : ''
            }
            <button class="add-to-cart-btn" style="width: 100%; padding: 16px;" onclick="window.productsManager.handleAddToCart(${JSON.stringify(product).replace(/"/g, '&quot;')}); window.productsManager.hideProductModal();">
                Добавить в корзину
            </button>
        `;

        this.elements.productModal.classList.add('show');
    }

    hideProductModal() {
        if (this.elements.productModal) {
            this.elements.productModal.classList.remove('show');
        }
    }

    showEmptyState() {
        if (this.elements.emptyState) {
            this.elements.emptyState.style.display = 'block';
        }
        if (this.elements.productsGrid) {
            this.elements.productsGrid.style.display = 'none';
        }
    }

    hideEmptyState() {
        if (this.elements.emptyState) {
            this.elements.emptyState.style.display = 'none';
        }
        if (this.elements.productsGrid) {
            this.elements.productsGrid.style.display = 'grid';
        }
    }

    // Public method to refresh products
    async refresh() {
        try {
            await this.loadProducts();
            this.renderProducts();
        } catch (error) {
            console.error('Failed to refresh products:', error);
        }
    }
}

// Initialize products manager
window.productsManager = new ProductsManager();