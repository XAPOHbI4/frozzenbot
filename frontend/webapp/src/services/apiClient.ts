import {
  ApiResponse,
  Product,
  Category,
  Order,
  OrderCreateRequest,
  Cart,
  CartItem,
  CartItemCreateRequest,
  CartItemUpdateRequest,
  TelegramUser,
  WebAppConfig,
  LocalCart,
  LocalCartItem,
  OrderFormData,
} from '../types';

class WebAppApiClient {
  private baseURL: string;

  constructor(config: WebAppConfig) {
    this.baseURL = config.API_BASE_URL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const defaultHeaders = {
      'Content-Type': 'application/json',
    };

    // Add Telegram WebApp auth if available
    if (window.Telegram?.WebApp?.initData) {
      defaultHeaders['X-Telegram-Init-Data'] = window.Telegram.WebApp.initData;
    }

    const config: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Handle API response format
      if (data.data !== undefined) {
        return data.data as T;
      }

      return data as T;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Products
  async getProducts(): Promise<{ products: Product[] }> {
    return this.request<{ products: Product[] }>('/api/products/');
  }

  async getProduct(id: number): Promise<Product> {
    return this.request<Product>(`/api/products/${id}`);
  }

  // Categories
  async getCategories(): Promise<{ categories: Category[] }> {
    return this.request<{ categories: Category[] }>('/api/categories/');
  }

  // Orders
  async createOrder(orderData: OrderCreateRequest): Promise<Order> {
    return this.request<Order>('/api/orders/', {
      method: 'POST',
      body: JSON.stringify(orderData),
    });
  }

  async getOrder(id: number): Promise<Order> {
    return this.request<Order>(`/api/orders/${id}`);
  }

  // Cart operations (server-side if needed)
  async getCart(telegramId: number): Promise<Cart> {
    return this.request<Cart>(`/api/cart/${telegramId}`);
  }

  async addToCart(item: CartItemCreateRequest): Promise<CartItem> {
    return this.request<CartItem>('/api/cart/items', {
      method: 'POST',
      body: JSON.stringify(item),
    });
  }

  async updateCartItem(id: number, data: CartItemUpdateRequest): Promise<CartItem> {
    return this.request<CartItem>(`/api/cart/items/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async removeFromCart(id: number): Promise<void> {
    return this.request<void>(`/api/cart/items/${id}`, {
      method: 'DELETE',
    });
  }

  // User operations
  async getCurrentUser(): Promise<TelegramUser | null> {
    try {
      return this.request<TelegramUser>('/api/users/me');
    } catch (error) {
      return null;
    }
  }

  async registerUser(userData: any): Promise<TelegramUser> {
    return this.request<TelegramUser>('/api/users/', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  // Make request method public for payment service
  async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    return this.request<T>(endpoint, options);
  }
}

// Local cart management for WebApp
export class LocalCartManager {
  private storageKey: string;

  constructor(storageKey: string = 'frozen_food_cart') {
    this.storageKey = storageKey;
  }

  getCart(): LocalCart {
    try {
      const stored = localStorage.getItem(this.storageKey);
      if (stored) {
        const cart = JSON.parse(stored) as LocalCart;
        return cart;
      }
    } catch (error) {
      console.error('Error loading cart from storage:', error);
    }

    return {
      items: [],
      total: 0,
      count: 0,
      updatedAt: new Date().toISOString(),
    };
  }

  saveCart(cart: LocalCart): void {
    try {
      cart.updatedAt = new Date().toISOString();
      localStorage.setItem(this.storageKey, JSON.stringify(cart));
    } catch (error) {
      console.error('Error saving cart to storage:', error);
    }
  }

  addItem(product: Product, quantity: number = 1): LocalCart {
    const cart = this.getCart();
    const existingItemIndex = cart.items.findIndex(
      item => item.productId === product.id
    );

    if (existingItemIndex >= 0) {
      cart.items[existingItemIndex].quantity += quantity;
      cart.items[existingItemIndex].total =
        cart.items[existingItemIndex].quantity * cart.items[existingItemIndex].price;
    } else {
      const newItem: LocalCartItem = {
        id: Date.now(), // temporary ID
        productId: product.id,
        name: product.name,
        price: product.price,
        quantity,
        total: product.price * quantity,
        image: product.image_url,
      };
      cart.items.push(newItem);
    }

    this.updateCartTotals(cart);
    this.saveCart(cart);
    return cart;
  }

  updateItemQuantity(productId: number, quantity: number): LocalCart {
    const cart = this.getCart();
    const itemIndex = cart.items.findIndex(item => item.productId === productId);

    if (itemIndex >= 0) {
      if (quantity <= 0) {
        cart.items.splice(itemIndex, 1);
      } else {
        cart.items[itemIndex].quantity = quantity;
        cart.items[itemIndex].total = cart.items[itemIndex].price * quantity;
      }
    }

    this.updateCartTotals(cart);
    this.saveCart(cart);
    return cart;
  }

  removeItem(productId: number): LocalCart {
    const cart = this.getCart();
    cart.items = cart.items.filter(item => item.productId !== productId);

    this.updateCartTotals(cart);
    this.saveCart(cart);
    return cart;
  }

  clearCart(): LocalCart {
    const cart: LocalCart = {
      items: [],
      total: 0,
      count: 0,
      updatedAt: new Date().toISOString(),
    };

    this.saveCart(cart);
    return cart;
  }

  private updateCartTotals(cart: LocalCart): void {
    cart.total = cart.items.reduce((sum, item) => sum + item.total, 0);
    cart.count = cart.items.reduce((sum, item) => sum + item.quantity, 0);
  }

  // Convert local cart to order format
  convertToOrderItems(): Array<{ product_id: number; quantity: number; price: number }> {
    const cart = this.getCart();
    return cart.items.map(item => ({
      product_id: item.productId,
      quantity: item.quantity,
      price: item.price,
    }));
  }
}

export { WebAppApiClient };
export default WebAppApiClient;