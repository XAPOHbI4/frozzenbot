// API Service for Backend Integration
class ApiService {
    constructor() {
        this.baseUrl = window.AppConfig.API_BASE_URL;
        this.endpoints = window.AppConfig.API_ENDPOINTS;
    }

    // Generic fetch wrapper with error handling
    async fetchApi(endpoint, options = {}) {
        const url = this.baseUrl + endpoint;

        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            ...options
        };

        try {
            const response = await fetch(url, defaultOptions);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // Get all products
    async getProducts() {
        try {
            const products = await this.fetchApi(this.endpoints.PRODUCTS);
            return products.map(product => ({
                id: product.id,
                name: product.name,
                description: product.description,
                price: product.price,
                formattedPrice: product.formatted_price,
                imageUrl: product.image_url,
                weight: product.weight,
                formattedWeight: product.formatted_weight,
                category: product.category
            }));
        } catch (error) {
            console.error('Failed to load products:', error);
            // Return fallback mock data for development
            return this.getMockProducts();
        }
    }

    // Get product by ID
    async getProduct(productId) {
        try {
            const product = await this.fetchApi(`${this.endpoints.PRODUCTS}${productId}`);
            return {
                id: product.id,
                name: product.name,
                description: product.description,
                price: product.price,
                formattedPrice: product.formatted_price,
                imageUrl: product.image_url,
                weight: product.weight,
                formattedWeight: product.formatted_weight,
                category: product.category
            };
        } catch (error) {
            console.error('Failed to load product:', error);
            return null;
        }
    }

    // Get all categories
    async getCategories() {
        try {
            return await this.fetchApi(this.endpoints.CATEGORIES);
        } catch (error) {
            console.error('Failed to load categories:', error);
            return [
                { id: 1, name: 'Готовые блюда', description: 'Замороженные готовые блюда' }
            ];
        }
    }

    // Get products by category
    async getProductsByCategory(categoryId) {
        try {
            return await this.fetchApi(`${this.endpoints.PRODUCTS}category/${categoryId}`);
        } catch (error) {
            console.error('Failed to load products by category:', error);
            return [];
        }
    }

    // Create order
    async createOrder(orderData) {
        try {
            return await this.fetchApi('/api/orders/', {
                method: 'POST',
                body: JSON.stringify(orderData)
            });
        } catch (error) {
            console.error('Failed to create order:', error);
            throw error;
        }
    }

    // Get order by ID
    async getOrder(orderId) {
        try {
            return await this.fetchApi(`/api/orders/${orderId}`);
        } catch (error) {
            console.error('Failed to get order:', error);
            throw error;
        }
    }

    // Get payment status
    async getPaymentStatus(orderId) {
        try {
            return await this.fetchApi(`/api/payments/${orderId}/status`);
        } catch (error) {
            console.error('Failed to get payment status:', error);
            throw error;
        }
    }

    // Get payment details
    async getPaymentDetails(paymentId) {
        try {
            return await this.fetchApi(`/api/payments/${paymentId}/details`);
        } catch (error) {
            console.error('Failed to get payment details:', error);
            throw error;
        }
    }

    // Send payment webhook (for testing)
    async sendPaymentWebhook(webhookData) {
        try {
            return await this.fetchApi('/api/payments/webhook', {
                method: 'POST',
                body: JSON.stringify(webhookData)
            });
        } catch (error) {
            console.error('Failed to send payment webhook:', error);
            throw error;
        }
    }

    // Mock data for development/fallback
    getMockProducts() {
        return [
            {
                id: 1,
                name: 'Плов с говядиной',
                description: 'Ароматный плов с нежной говядиной и специями. Готов к употреблению за 5 минут.',
                price: 450,
                formattedPrice: '450₽',
                imageUrl: null,
                weight: 400,
                formattedWeight: '400г',
                category: { id: 1, name: 'Готовые блюда' }
            },
            {
                id: 2,
                name: 'Паста Болоньезе',
                description: 'Классическая паста с мясным соусом болоньезе. Идеально для быстрого ужина.',
                price: 380,
                formattedPrice: '380₽',
                imageUrl: null,
                weight: 350,
                formattedWeight: '350г',
                category: { id: 1, name: 'Готовые блюда' }
            },
            {
                id: 3,
                name: 'Лазанья мясная',
                description: 'Многослойная лазанья с мясным фаршем, сыром и соусом бешамель.',
                price: 520,
                formattedPrice: '520₽',
                imageUrl: null,
                weight: 450,
                formattedWeight: '450г',
                category: { id: 1, name: 'Готовые блюда' }
            },
            {
                id: 4,
                name: 'Гуляш с картофелем',
                description: 'Сытный гуляш из говядины с молодым картофелем и овощами.',
                price: 420,
                formattedPrice: '420₽',
                imageUrl: null,
                weight: 400,
                formattedWeight: '400г',
                category: { id: 1, name: 'Готовые блюда' }
            },
            {
                id: 5,
                name: 'Курица в сливочном соусе',
                description: 'Нежная курица в ароматном сливочном соусе с травами.',
                price: 390,
                formattedPrice: '390₽',
                imageUrl: null,
                weight: 350,
                formattedWeight: '350г',
                category: { id: 1, name: 'Готовые блюда' }
            },
            {
                id: 6,
                name: 'Рагу овощное с мясом',
                description: 'Домашнее рагу с сезонными овощами и кусочками мяса.',
                price: 360,
                formattedPrice: '360₽',
                imageUrl: null,
                weight: 380,
                formattedWeight: '380г',
                category: { id: 1, name: 'Готовые блюда' }
            },
            {
                id: 7,
                name: 'Бефстроганов',
                description: 'Классический бефстроганов с грибами в сметанном соусе.',
                price: 480,
                formattedPrice: '480₽',
                imageUrl: null,
                weight: 400,
                formattedWeight: '400г',
                category: { id: 1, name: 'Готовые блюда' }
            },
            {
                id: 8,
                name: 'Солянка мясная',
                description: 'Густая солянка с копченостями, колбасой и солеными огурцами.',
                price: 350,
                formattedPrice: '350₽',
                imageUrl: null,
                weight: 400,
                formattedWeight: '400г',
                category: { id: 1, name: 'Готовые блюда' }
            }
        ];
    }
}

// Global API instance
window.api = new ApiService();