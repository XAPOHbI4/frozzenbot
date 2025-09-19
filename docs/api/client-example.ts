/**
 * Example API Client Implementation for FrozenBot API
 *
 * This file provides a complete, production-ready TypeScript client
 * for consuming the FrozenBot API with proper error handling,
 * authentication, and type safety.
 */

import {
  FrozenBotApiClient,
  ApiClientConfig,
  AuthenticatedRequestOptions,
  LoginRequest,
  LoginResponse,
  TokenResponse,
  RefreshRequest,
  User,
  UserCreateRequest,
  Product,
  ProductListResponse,
  ProductCreateRequest,
  ProductUpdateRequest,
  ProductFilters,
  Category,
  CategoryListResponse,
  CategoryCreateRequest,
  CategoryUpdateRequest,
  Cart,
  EmptyCart,
  CartItem,
  CartItemCreateRequest,
  CartItemUpdateRequest,
  Order,
  OrderListResponse,
  OrderCreateRequest,
  OrderStatusUpdateRequest,
  OrderFilters,
  DashboardStats,
  OrderAnalytics,
  ProductAnalytics,
  AnalyticsFilters,
  NotificationRequest,
  NotificationResponse,
  PaymentStatusResponse,
  ApiError,
  ErrorResponse,
  ValidationErrorResponse,
  TelegramUserId,
  defaultApiConfig,
  isApiError,
  isValidationError,
  API_ENDPOINTS
} from './types';

// ============================================================================
// API Client Implementation
// ============================================================================

export class FrozenBotApiClientImpl implements FrozenBotApiClient {
  private config: ApiClientConfig;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private telegramInitData: string | null = null;

  constructor(config: Partial<ApiClientConfig> = {}) {
    this.config = { ...defaultApiConfig, ...config };
  }

  // ========================================================================
  // Authentication Methods
  // ========================================================================

  setJwtTokens(accessToken: string, refreshToken: string) {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
  }

  setTelegramInitData(initData: string) {
    this.telegramInitData = initData;
  }

  clearAuth() {
    this.accessToken = null;
    this.refreshToken = null;
    this.telegramInitData = null;
  }

  // ========================================================================
  // Core Request Method
  // ========================================================================

  private async request<T>(
    endpoint: string,
    options: AuthenticatedRequestOptions = {}
  ): Promise<T> {
    const {
      params,
      token = this.accessToken,
      telegramInitData = this.telegramInitData,
      timeout = this.config.timeout,
      ...requestOptions
    } = options;

    // Build URL with query parameters
    let url = `${this.config.baseUrl}${endpoint}`;
    if (params) {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      });
      const queryString = searchParams.toString();
      if (queryString) {
        url += `?${queryString}`;
      }
    }

    // Prepare headers
    const headers: Record<string, string> = {
      ...this.config.headers,
      ...requestOptions.headers
    };

    // Add authentication headers
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    if (telegramInitData) {
      headers['X-Telegram-Init-Data'] = telegramInitData;
    }

    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = timeout ? setTimeout(() => controller.abort(), timeout) : null;

    try {
      const response = await fetch(url, {
        ...requestOptions,
        headers,
        signal: controller.signal
      });

      if (timeoutId) {
        clearTimeout(timeoutId);
      }

      // Handle authentication errors with token refresh
      if (response.status === 401 && token && this.refreshToken) {
        try {
          await this.handleTokenRefresh();
          // Retry request with new token
          return this.request<T>(endpoint, {
            ...options,
            token: this.accessToken
          });
        } catch (refreshError) {
          // Refresh failed, clear tokens and throw original error
          this.clearAuth();
          throw await this.createApiError(response);
        }
      }

      if (!response.ok) {
        throw await this.createApiError(response);
      }

      // Handle no-content responses
      if (response.status === 204) {
        return undefined as unknown as T;
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return response.json();
      }

      return response.text() as unknown as T;
    } catch (error) {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }

      if (error.name === 'AbortError') {
        throw new Error('Request timeout');
      }

      throw error;
    }
  }

  private async createApiError(response: Response): Promise<ApiError> {
    let errorData: ErrorResponse;

    try {
      errorData = await response.json();
    } catch {
      errorData = {
        error: 'unknown_error',
        message: `HTTP ${response.status}: ${response.statusText}`
      };
    }

    const error = new Error(errorData.message) as ApiError;
    error.status = response.status;
    error.error = errorData;
    return error;
  }

  private async handleTokenRefresh(): Promise<void> {
    if (!this.refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await fetch(`${this.config.baseUrl}${API_ENDPOINTS.REFRESH}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ refresh_token: this.refreshToken })
    });

    if (!response.ok) {
      throw new Error('Token refresh failed');
    }

    const tokenData: TokenResponse = await response.json();
    this.accessToken = tokenData.access_token;
  }

  // ========================================================================
  // Authentication API
  // ========================================================================

  async login(request: LoginRequest): Promise<LoginResponse> {
    const response = await this.request<LoginResponse>(API_ENDPOINTS.LOGIN, {
      method: 'POST',
      body: JSON.stringify(request)
    });

    // Store tokens for future requests
    this.setJwtTokens(response.access_token, response.refresh_token);

    return response;
  }

  async refresh(request: RefreshRequest): Promise<TokenResponse> {
    const response = await this.request<TokenResponse>(API_ENDPOINTS.REFRESH, {
      method: 'POST',
      body: JSON.stringify(request)
    });

    // Update access token
    this.accessToken = response.access_token;

    return response;
  }

  // ========================================================================
  // Users API
  // ========================================================================

  async getCurrentUser(): Promise<User> {
    return this.request<User>(API_ENDPOINTS.CURRENT_USER);
  }

  async createUser(request: UserCreateRequest): Promise<User> {
    return this.request<User>(API_ENDPOINTS.USERS, {
      method: 'POST',
      body: JSON.stringify(request)
    });
  }

  async getUserByTelegramId(telegramId: TelegramUserId): Promise<User> {
    return this.request<User>(`${API_ENDPOINTS.USERS}/${telegramId}`);
  }

  // ========================================================================
  // Products API
  // ========================================================================

  async getProducts(filters?: ProductFilters): Promise<ProductListResponse> {
    return this.request<ProductListResponse>(API_ENDPOINTS.PRODUCTS, {
      params: filters
    });
  }

  async getProduct(id: number): Promise<Product> {
    return this.request<Product>(API_ENDPOINTS.PRODUCT(id));
  }

  async createProduct(request: ProductCreateRequest): Promise<Product> {
    return this.request<Product>(API_ENDPOINTS.PRODUCTS, {
      method: 'POST',
      body: JSON.stringify(request)
    });
  }

  async updateProduct(id: number, request: ProductUpdateRequest): Promise<Product> {
    return this.request<Product>(API_ENDPOINTS.PRODUCT(id), {
      method: 'PUT',
      body: JSON.stringify(request)
    });
  }

  async deleteProduct(id: number): Promise<void> {
    return this.request<void>(API_ENDPOINTS.PRODUCT(id), {
      method: 'DELETE'
    });
  }

  // ========================================================================
  // Categories API
  // ========================================================================

  async getCategories(): Promise<CategoryListResponse> {
    return this.request<CategoryListResponse>(API_ENDPOINTS.CATEGORIES);
  }

  async createCategory(request: CategoryCreateRequest): Promise<Category> {
    return this.request<Category>(API_ENDPOINTS.CATEGORIES, {
      method: 'POST',
      body: JSON.stringify(request)
    });
  }

  async updateCategory(id: number, request: CategoryUpdateRequest): Promise<Category> {
    return this.request<Category>(API_ENDPOINTS.CATEGORY(id), {
      method: 'PUT',
      body: JSON.stringify(request)
    });
  }

  async deleteCategory(id: number): Promise<void> {
    return this.request<void>(API_ENDPOINTS.CATEGORY(id), {
      method: 'DELETE'
    });
  }

  // ========================================================================
  // Cart API
  // ========================================================================

  async getCart(telegramId: TelegramUserId): Promise<Cart | EmptyCart> {
    return this.request<Cart | EmptyCart>(API_ENDPOINTS.CART(telegramId));
  }

  async addCartItem(request: CartItemCreateRequest): Promise<CartItem> {
    return this.request<CartItem>(API_ENDPOINTS.CART_ITEMS, {
      method: 'POST',
      body: JSON.stringify(request)
    });
  }

  async updateCartItem(id: number, request: CartItemUpdateRequest): Promise<CartItem> {
    return this.request<CartItem>(API_ENDPOINTS.CART_ITEM(id), {
      method: 'PUT',
      body: JSON.stringify(request)
    });
  }

  async removeCartItem(id: number): Promise<void> {
    return this.request<void>(API_ENDPOINTS.CART_ITEM(id), {
      method: 'DELETE'
    });
  }

  // ========================================================================
  // Orders API
  // ========================================================================

  async getOrders(filters?: OrderFilters): Promise<OrderListResponse> {
    return this.request<OrderListResponse>(API_ENDPOINTS.ORDERS, {
      params: filters
    });
  }

  async getOrder(id: number): Promise<Order> {
    return this.request<Order>(API_ENDPOINTS.ORDER(id));
  }

  async createOrder(request: OrderCreateRequest): Promise<Order> {
    return this.request<Order>(API_ENDPOINTS.ORDERS, {
      method: 'POST',
      body: JSON.stringify(request)
    });
  }

  async updateOrderStatus(id: number, request: OrderStatusUpdateRequest): Promise<Order> {
    return this.request<Order>(API_ENDPOINTS.ORDER_STATUS(id), {
      method: 'PUT',
      body: JSON.stringify(request)
    });
  }

  // ========================================================================
  // Admin API
  // ========================================================================

  async getDashboardStats(): Promise<DashboardStats> {
    return this.request<DashboardStats>(API_ENDPOINTS.DASHBOARD_STATS);
  }

  async getOrderAnalytics(filters?: AnalyticsFilters): Promise<OrderAnalytics> {
    return this.request<OrderAnalytics>(API_ENDPOINTS.ORDER_ANALYTICS, {
      params: filters
    });
  }

  async getProductAnalytics(filters?: AnalyticsFilters): Promise<ProductAnalytics> {
    return this.request<ProductAnalytics>(API_ENDPOINTS.PRODUCT_ANALYTICS, {
      params: filters
    });
  }

  // ========================================================================
  // Notifications API
  // ========================================================================

  async sendNotification(request: NotificationRequest): Promise<NotificationResponse> {
    return this.request<NotificationResponse>(API_ENDPOINTS.SEND_NOTIFICATION, {
      method: 'POST',
      body: JSON.stringify(request)
    });
  }

  // ========================================================================
  // Payments API
  // ========================================================================

  async getPaymentStatus(orderId: number): Promise<PaymentStatusResponse> {
    return this.request<PaymentStatusResponse>(API_ENDPOINTS.PAYMENT_STATUS(orderId));
  }
}

// ============================================================================
// Error Handling Utilities
// ============================================================================

export class ApiErrorHandler {
  static handle(error: unknown): string {
    if (isApiError(error)) {
      return this.handleApiError(error);
    }

    if (error instanceof Error) {
      return error.message;
    }

    return 'An unexpected error occurred';
  }

  private static handleApiError(error: ApiError): string {
    const errorData = error.error;

    if (!errorData) {
      return `HTTP ${error.status}: ${error.message}`;
    }

    switch (errorData.error) {
      case 'validation_error':
        return this.handleValidationError(errorData as ValidationErrorResponse);
      case 'unauthorized':
        return 'Please log in to continue';
      case 'forbidden':
        return 'You do not have permission to perform this action';
      case 'not_found':
        return 'The requested resource was not found';
      case 'rate_limit_exceeded':
        const retryAfter = errorData.details?.retry_after || 60;
        return `Too many requests. Please try again in ${retryAfter} seconds`;
      case 'insufficient_stock':
        return 'Not enough items in stock';
      case 'minimum_order_not_met':
        const missing = errorData.details?.missing_amount;
        return missing
          ? `Order amount is below minimum. Add ${missing}₽ more to continue`
          : 'Order amount is below minimum required';
      default:
        return errorData.message || 'An error occurred';
    }
  }

  private static handleValidationError(error: ValidationErrorResponse): string {
    if (error.details && error.details.length > 0) {
      const firstError = error.details[0];
      return firstError.message;
    }
    return 'Validation failed';
  }

  static getFieldErrors(error: unknown): Record<string, string[]> {
    if (isValidationError(error)) {
      const fieldErrors: Record<string, string[]> = {};

      error.error.details.forEach(detail => {
        if (!fieldErrors[detail.field]) {
          fieldErrors[detail.field] = [];
        }
        fieldErrors[detail.field].push(detail.message);
      });

      return fieldErrors;
    }

    return {};
  }
}

// ============================================================================
// React Hooks (Optional)
// ============================================================================

export function createApiHooks(client: FrozenBotApiClient) {
  // This would typically be implemented with a state management library
  // like React Query, SWR, or Zustand. Here's a basic example:

  function useApi<T>(
    fetcher: () => Promise<T>,
    dependencies: any[] = []
  ) {
    const [data, setData] = React.useState<T | null>(null);
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState<ApiError | null>(null);

    const refetch = React.useCallback(async () => {
      setLoading(true);
      setError(null);

      try {
        const result = await fetcher();
        setData(result);
      } catch (err) {
        setError(err as ApiError);
      } finally {
        setLoading(false);
      }
    }, dependencies);

    React.useEffect(() => {
      refetch();
    }, [refetch]);

    return { data, loading, error, refetch };
  }

  return {
    useProducts: (filters?: ProductFilters) =>
      useApi(() => client.getProducts(filters), [filters]),

    useProduct: (id: number) =>
      useApi(() => client.getProduct(id), [id]),

    useCart: (telegramId: TelegramUserId) =>
      useApi(() => client.getCart(telegramId), [telegramId]),

    useOrders: (filters?: OrderFilters) =>
      useApi(() => client.getOrders(filters), [filters]),

    useDashboardStats: () =>
      useApi(() => client.getDashboardStats(), [])
  };
}

// ============================================================================
// Usage Examples
// ============================================================================

export async function exampleUsage() {
  const client = new FrozenBotApiClientImpl({
    baseUrl: 'http://localhost:8000'
  });

  try {
    // Admin login
    const loginResult = await client.login({
      username: 'admin',
      password: 'admin123'
    });
    console.log('Logged in as:', loginResult.user.username);

    // Get products
    const products = await client.getProducts({
      page: 1,
      limit: 10,
      is_active: true
    });
    console.log(`Found ${products.total} products`);

    // Create a new product (admin only)
    const newProduct = await client.createProduct({
      name: 'New Frozen Product',
      price: 250.0,
      category_id: 1,
      weight: 400
    });
    console.log('Created product:', newProduct.id);

    // Telegram WebApp usage
    client.setTelegramInitData('query_id=AAH...&user=%7B%22id%22...');

    const cart = await client.getCart(123456789);
    console.log('Cart total:', cart.total_amount);

    // Add item to cart
    const cartItem = await client.addCartItem({
      telegram_id: 123456789,
      product_id: newProduct.id,
      quantity: 2
    });
    console.log('Added to cart:', cartItem.id);

    // Create order
    const order = await client.createOrder({
      telegram_id: 123456789,
      customer_name: 'John Doe',
      customer_phone: '+1234567890',
      delivery_address: '123 Main St'
    });
    console.log('Created order:', order.id);

  } catch (error) {
    console.error('API Error:', ApiErrorHandler.handle(error));

    if (isValidationError(error)) {
      const fieldErrors = ApiErrorHandler.getFieldErrors(error);
      console.log('Field errors:', fieldErrors);
    }
  }
}

// Export the default client instance
export const apiClient = new FrozenBotApiClientImpl();