/**
 * API Request/Response Type Definitions
 * Generated from OpenAPI specification for FrozenBot API
 */

import {
  User,
  UserCreateRequest,
  Product,
  ProductCreateRequest,
  ProductUpdateRequest,
  Category,
  CategoryCreateRequest,
  CategoryUpdateRequest,
  Cart,
  EmptyCart,
  CartItem,
  CartItemCreateRequest,
  CartItemUpdateRequest,
  Order,
  OrderCreateRequest,
  OrderStatusUpdateRequest,
  DashboardStats,
  OrderAnalytics,
  ProductAnalytics,
  NotificationRequest,
  NotificationResponse,
  PaymentWebhookRequest,
  PaymentStatusResponse,
} from './models';

// Generic API Response Types
export interface ApiResponse<T = any> {
  success?: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export interface ErrorResponse {
  error: string;
  message: string;
  details?: Record<string, any>;
}

export interface ValidationError {
  error: 'validation_error';
  message: string;
  details: Array<{
    field: string;
    message: string;
    code: string;
  }>;
}

// Pagination Types
export interface PaginationParams {
  page?: number;
  limit?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pages: number;
  per_page: number;
}

// Product API Types
export interface ProductListParams extends PaginationParams {
  category_id?: number;
  search?: string;
  in_stock?: boolean;
  is_active?: boolean;
}

export type ProductListResponse = PaginatedResponse<Product>;

// Order API Types
export interface OrderListParams extends PaginationParams {
  status?: string;
  telegram_id?: number;
  date_from?: string;
  date_to?: string;
}

export type OrderListResponse = PaginatedResponse<Order>;

// Analytics API Types
export interface OrderAnalyticsParams {
  period?: 'day' | 'week' | 'month' | 'year';
  date_from?: string;
  date_to?: string;
}

export interface ProductAnalyticsParams {
  period?: 'day' | 'week' | 'month' | 'year';
}

// Cart API Types
export type CartResponse = Cart | EmptyCart;

// Authentication API Types (separate file will import these)
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

// API Endpoint Configurations
export interface ApiEndpoints {
  // Authentication
  LOGIN: string;
  REFRESH: string;

  // Users
  USERS_ME: string;
  USERS_CREATE: string;
  USERS_BY_TELEGRAM_ID: (telegram_id: number) => string;

  // Products
  PRODUCTS: string;
  PRODUCTS_BY_ID: (id: number) => string;

  // Categories
  CATEGORIES: string;
  CATEGORIES_BY_ID: (id: number) => string;

  // Cart
  CART_BY_TELEGRAM_ID: (telegram_id: number) => string;
  CART_ITEMS: string;
  CART_ITEMS_BY_ID: (id: number) => string;

  // Orders
  ORDERS: string;
  ORDERS_BY_ID: (id: number) => string;
  ORDERS_STATUS_UPDATE: (id: number) => string;

  // Admin
  ADMIN_DASHBOARD_STATS: string;
  ADMIN_ORDERS_STATS: string;
  ADMIN_PRODUCTS_STATS: string;

  // Notifications
  NOTIFICATIONS_SEND: string;

  // Payments
  PAYMENTS_WEBHOOK: string;
  PAYMENTS_STATUS: (order_id: number) => string;
}

// HTTP Method Types
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

// Request Configuration Types
export interface RequestConfig {
  method: HttpMethod;
  url: string;
  data?: any;
  params?: Record<string, any>;
  headers?: Record<string, string>;
}

// Response Types for specific endpoints
export interface ApiResponses {
  // Authentication
  '/auth/login': {
    POST: {
      request: LoginRequest;
      response: LoginResponse;
    };
  };

  '/auth/refresh': {
    POST: {
      request: RefreshRequest;
      response: TokenResponse;
    };
  };

  // Users
  '/api/users/me': {
    GET: {
      response: User;
    };
  };

  '/api/users/': {
    POST: {
      request: UserCreateRequest;
      response: User;
    };
  };

  // Products
  '/api/products/': {
    GET: {
      params: ProductListParams;
      response: ProductListResponse;
    };
    POST: {
      request: ProductCreateRequest;
      response: Product;
    };
  };

  '/api/products/{id}': {
    GET: {
      response: Product;
    };
    PUT: {
      request: ProductUpdateRequest;
      response: Product;
    };
    DELETE: {
      response: null;
    };
  };

  // Categories
  '/api/categories/': {
    GET: {
      response: Category[];
    };
    POST: {
      request: CategoryCreateRequest;
      response: Category;
    };
  };

  '/api/categories/{id}': {
    PUT: {
      request: CategoryUpdateRequest;
      response: Category;
    };
    DELETE: {
      response: null;
    };
  };

  // Cart
  '/api/cart/{telegram_id}': {
    GET: {
      response: CartResponse;
    };
  };

  '/api/cart/items': {
    POST: {
      request: CartItemCreateRequest;
      response: CartItem;
    };
  };

  '/api/cart/items/{id}': {
    PUT: {
      request: CartItemUpdateRequest;
      response: CartItem;
    };
    DELETE: {
      response: null;
    };
  };

  // Orders
  '/api/orders/': {
    GET: {
      params: OrderListParams;
      response: OrderListResponse;
    };
    POST: {
      request: OrderCreateRequest;
      response: Order;
    };
  };

  '/api/orders/{id}': {
    GET: {
      response: Order;
    };
  };

  '/api/orders/{id}/status': {
    PUT: {
      request: OrderStatusUpdateRequest;
      response: Order;
    };
  };

  // Admin
  '/api/admin/dashboard/stats': {
    GET: {
      response: DashboardStats;
    };
  };

  '/api/admin/orders/stats': {
    GET: {
      params: OrderAnalyticsParams;
      response: OrderAnalytics;
    };
  };

  '/api/admin/products/stats': {
    GET: {
      params: ProductAnalyticsParams;
      response: ProductAnalytics;
    };
  };

  // Notifications
  '/api/notifications/send': {
    POST: {
      request: NotificationRequest;
      response: NotificationResponse;
    };
  };

  // Payments
  '/api/payments/webhook': {
    POST: {
      request: PaymentWebhookRequest;
      response: null;
    };
  };

  '/api/payments/{order_id}/status': {
    GET: {
      response: PaymentStatusResponse;
    };
  };
}

// Utility type to extract request type for an endpoint
export type ExtractRequest<
  T extends keyof ApiResponses,
  M extends keyof ApiResponses[T]
> = ApiResponses[T][M] extends { request: infer R } ? R : never;

// Utility type to extract response type for an endpoint
export type ExtractResponse<
  T extends keyof ApiResponses,
  M extends keyof ApiResponses[T]
> = ApiResponses[T][M] extends { response: infer R } ? R : never;

// Utility type to extract params type for an endpoint
export type ExtractParams<
  T extends keyof ApiResponses,
  M extends keyof ApiResponses[T]
> = ApiResponses[T][M] extends { params: infer P } ? P : never;