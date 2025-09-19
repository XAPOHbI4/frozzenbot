/**
 * FrozenBot API TypeScript Type Definitions
 * Generated from OpenAPI specification
 *
 * These types provide full type safety for TypeScript/JavaScript clients
 * consuming the FrozenBot API.
 */

// ============================================================================
// Common Types
// ============================================================================

export interface ErrorResponse {
  error: string;
  message: string;
  details?: Record<string, any>;
}

export interface ValidationErrorDetail {
  field: string;
  message: string;
  code: string;
}

export interface ValidationErrorResponse {
  error: 'validation_error';
  message: string;
  details: ValidationErrorDetail[];
}

export interface PaginationMeta {
  total: number;
  page: number;
  pages: number;
  per_page: number;
}

export interface PaginatedResponse<T> extends PaginationMeta {
  items: T[];
}

export interface SuccessResponse {
  success: boolean;
  message: string;
}

// ============================================================================
// Authentication Types
// ============================================================================

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: 'bearer';
  expires_in: number;
}

export interface LoginResponse extends TokenResponse {
  refresh_token: string;
  user: User;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface TelegramInitData {
  init_data: string;
}

// ============================================================================
// User Types
// ============================================================================

export interface User {
  id: number;
  telegram_id: number;
  username?: string;
  first_name: string;
  last_name?: string;
  phone?: string;
  is_admin: boolean;
  is_active: boolean;
  full_name: string;
  created_at: string;
  updated_at: string;
}

export interface UserCreateRequest {
  telegram_id: number;
  username?: string;
  first_name: string;
  last_name?: string;
  phone?: string;
}

export interface UserUpdateRequest {
  username?: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  is_active?: boolean;
}

export type UserListResponse = PaginatedResponse<User>;

// ============================================================================
// Category Types
// ============================================================================

export interface Category {
  id: number;
  name: string;
  description?: string;
  image_url?: string;
  is_active: boolean;
  sort_order: number;
  products_count: number;
  created_at: string;
  updated_at: string;
}

export interface CategoryCreateRequest {
  name: string;
  description?: string;
  image_url?: string;
  is_active?: boolean;
  sort_order?: number;
}

export interface CategoryUpdateRequest {
  name?: string;
  description?: string;
  image_url?: string;
  is_active?: boolean;
  sort_order?: number;
}

export interface CategoryListResponse {
  items: Category[];
}

// ============================================================================
// Product Types
// ============================================================================

export interface Product {
  id: number;
  name: string;
  description?: string;
  price: number;
  formatted_price: string;
  image_url?: string;
  is_active: boolean;
  in_stock: boolean;
  weight?: number;
  formatted_weight: string;
  sort_order: number;
  category_id?: number;
  category?: Category;
  created_at: string;
  updated_at: string;
}

export interface ProductCreateRequest {
  name: string;
  description?: string;
  price: number;
  image_url?: string;
  is_active?: boolean;
  in_stock?: boolean;
  weight?: number;
  sort_order?: number;
  category_id?: number;
}

export interface ProductUpdateRequest {
  name?: string;
  description?: string;
  price?: number;
  image_url?: string;
  is_active?: boolean;
  in_stock?: boolean;
  weight?: number;
  sort_order?: number;
  category_id?: number;
}

export type ProductListResponse = PaginatedResponse<Product>;

// ============================================================================
// Cart Types
// ============================================================================

export interface CartItem {
  id: number;
  cart_id: number;
  product_id: number;
  quantity: number;
  product: Product;
  total_price: number;
  created_at: string;
  updated_at: string;
}

export interface Cart {
  id: number;
  user_id: number;
  items: CartItem[];
  total_amount: number;
  total_items: number;
  expires_at?: string;
  created_at: string;
  updated_at: string;
}

export interface EmptyCart {
  items: [];
  total_amount: 0;
  total_items: 0;
}

export interface CartItemCreateRequest {
  telegram_id: number;
  product_id: number;
  quantity: number;
}

export interface CartItemUpdateRequest {
  quantity: number;
}

// ============================================================================
// Order Types
// ============================================================================

export type OrderStatus =
  | 'pending'
  | 'confirmed'
  | 'preparing'
  | 'ready'
  | 'completed'
  | 'cancelled';

export interface OrderItem {
  id: number;
  order_id: number;
  product_id: number;
  quantity: number;
  price: number;
  formatted_price: string;
  total_price: number;
  formatted_total: string;
  product: Product;
}

export interface Order {
  id: number;
  user_id: number;
  status: OrderStatus;
  status_display: string;
  total_amount: number;
  formatted_total: string;
  customer_name: string;
  customer_phone: string;
  delivery_address?: string;
  notes?: string;
  payment_method: string;
  items: OrderItem[];
  user: User;
  created_at: string;
  updated_at: string;
}

export interface OrderCreateRequest {
  telegram_id: number;
  customer_name: string;
  customer_phone: string;
  delivery_address?: string;
  notes?: string;
  payment_method?: string;
}

export interface OrderStatusUpdateRequest {
  status: OrderStatus;
}

export type OrderListResponse = PaginatedResponse<Order>;

// ============================================================================
// Admin & Analytics Types
// ============================================================================

export interface PopularProduct {
  product: Product;
  orders_count: number;
  total_revenue: number;
}

export interface DashboardStats {
  total_orders: number;
  total_revenue: number;
  active_users: number;
  pending_orders: number;
  today_orders: number;
  today_revenue: number;
  popular_products: PopularProduct[];
  recent_orders: Order[];
}

export interface ChartDataPoint {
  date: string;
  revenue: number;
}

export interface OrderChartDataPoint {
  date: string;
  count: number;
}

export interface OrderAnalytics {
  period: string;
  total_orders: number;
  total_revenue: number;
  average_order_value: number;
  orders_by_status: Record<string, number>;
  revenue_chart: ChartDataPoint[];
  orders_chart: OrderChartDataPoint[];
}

export interface TopProduct {
  product: Product;
  orders_count: number;
  revenue: number;
}

export interface CategoryPerformance {
  category: Category;
  orders_count: number;
  revenue: number;
}

export interface InventoryStatus {
  total_products: number;
  active_products: number;
  out_of_stock: number;
}

export interface ProductAnalytics {
  period: string;
  top_products: TopProduct[];
  categories_performance: CategoryPerformance[];
  inventory_status: InventoryStatus;
}

// ============================================================================
// Notification Types
// ============================================================================

export type NotificationType = 'user' | 'broadcast';
export type ParseMode = 'HTML' | 'Markdown';

export interface NotificationRequest {
  type: NotificationType;
  telegram_id?: number;
  message: string;
  parse_mode?: ParseMode;
}

export interface BroadcastNotificationRequest {
  type: 'broadcast';
  message: string;
  parse_mode?: ParseMode;
  target_users?: 'all' | 'active' | 'admin';
}

export interface NotificationResponse {
  success: boolean;
  message: string;
  sent_count?: number;
  failed_count?: number;
}

export interface NotificationStatus {
  notification_id: string;
  status: string;
  telegram_id?: number;
  message: string;
  sent_at?: string;
  delivered_at?: string;
  error_message?: string;
}

// ============================================================================
// Payment Types
// ============================================================================

export type PaymentStatus = 'pending' | 'success' | 'failed' | 'refunded' | 'cancelled';
export type PaymentMethod = 'card' | 'cash' | 'transfer' | 'crypto';

export interface PaymentWebhookRequest {
  order_id: number;
  status: PaymentStatus;
  amount: number;
  transaction_id?: string;
  payment_method?: PaymentMethod;
  metadata?: Record<string, any>;
}

export interface PaymentCreateRequest {
  order_id: number;
  amount: number;
  payment_method: PaymentMethod;
  return_url?: string;
  cancel_url?: string;
}

export interface PaymentResponse {
  id: string;
  order_id: number;
  status: PaymentStatus;
  amount: number;
  payment_method: PaymentMethod;
  transaction_id?: string;
  payment_url?: string;
  expires_at?: string;
  created_at: string;
  updated_at: string;
}

export interface PaymentStatusResponse {
  order_id: number;
  status: PaymentStatus;
  amount: number;
  transaction_id?: string;
  payment_method: PaymentMethod;
  created_at: string;
  updated_at: string;
  paid_at?: string;
}

export interface RefundRequest {
  payment_id: string;
  amount?: number;
  reason?: string;
}

export interface RefundResponse {
  id: string;
  payment_id: string;
  order_id: number;
  status: string;
  amount: number;
  reason?: string;
  refund_id?: string;
  created_at: string;
  processed_at?: string;
}

// ============================================================================
// API Client Types
// ============================================================================

export interface ApiClientConfig {
  baseUrl: string;
  timeout?: number;
  headers?: Record<string, string>;
}

export interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean>;
  timeout?: number;
}

export interface AuthenticatedRequestOptions extends RequestOptions {
  token?: string;
  telegramInitData?: string;
}

// ============================================================================
// Query Parameter Types
// ============================================================================

export interface ProductFilters {
  page?: number;
  limit?: number;
  category_id?: number;
  search?: string;
  in_stock?: boolean;
  is_active?: boolean;
}

export interface OrderFilters {
  page?: number;
  limit?: number;
  status?: OrderStatus;
  telegram_id?: number;
  date_from?: string;
  date_to?: string;
}

export interface AnalyticsFilters {
  period?: 'day' | 'week' | 'month' | 'year';
  date_from?: string;
  date_to?: string;
}

// ============================================================================
// API Response Wrappers
// ============================================================================

export type ApiResponse<T> = Promise<T>;
export type ApiError = Error & {
  status?: number;
  error?: ErrorResponse;
};

// ============================================================================
// Utility Types
// ============================================================================

export type Timestamp = string; // ISO 8601 format
export type Currency = number; // Amount in rubles
export type TelegramUserId = number;

// Create/Update type helpers
export type CreateRequest<T> = Omit<T, 'id' | 'created_at' | 'updated_at'>;
export type UpdateRequest<T> = Partial<Omit<T, 'id' | 'created_at' | 'updated_at'>>;

// ============================================================================
// API Client Interface
// ============================================================================

export interface FrozenBotApiClient {
  // Authentication
  login(request: LoginRequest): ApiResponse<LoginResponse>;
  refresh(request: RefreshRequest): ApiResponse<TokenResponse>;

  // Users
  getCurrentUser(): ApiResponse<User>;
  createUser(request: UserCreateRequest): ApiResponse<User>;
  getUserByTelegramId(telegramId: TelegramUserId): ApiResponse<User>;

  // Products
  getProducts(filters?: ProductFilters): ApiResponse<ProductListResponse>;
  getProduct(id: number): ApiResponse<Product>;
  createProduct(request: ProductCreateRequest): ApiResponse<Product>;
  updateProduct(id: number, request: ProductUpdateRequest): ApiResponse<Product>;
  deleteProduct(id: number): ApiResponse<void>;

  // Categories
  getCategories(): ApiResponse<CategoryListResponse>;
  createCategory(request: CategoryCreateRequest): ApiResponse<Category>;
  updateCategory(id: number, request: CategoryUpdateRequest): ApiResponse<Category>;
  deleteCategory(id: number): ApiResponse<void>;

  // Cart
  getCart(telegramId: TelegramUserId): ApiResponse<Cart | EmptyCart>;
  addCartItem(request: CartItemCreateRequest): ApiResponse<CartItem>;
  updateCartItem(id: number, request: CartItemUpdateRequest): ApiResponse<CartItem>;
  removeCartItem(id: number): ApiResponse<void>;

  // Orders
  getOrders(filters?: OrderFilters): ApiResponse<OrderListResponse>;
  getOrder(id: number): ApiResponse<Order>;
  createOrder(request: OrderCreateRequest): ApiResponse<Order>;
  updateOrderStatus(id: number, request: OrderStatusUpdateRequest): ApiResponse<Order>;

  // Admin
  getDashboardStats(): ApiResponse<DashboardStats>;
  getOrderAnalytics(filters?: AnalyticsFilters): ApiResponse<OrderAnalytics>;
  getProductAnalytics(filters?: AnalyticsFilters): ApiResponse<ProductAnalytics>;

  // Notifications
  sendNotification(request: NotificationRequest): ApiResponse<NotificationResponse>;

  // Payments
  getPaymentStatus(orderId: number): ApiResponse<PaymentStatusResponse>;
}

// ============================================================================
// Hook Types (for React integration)
// ============================================================================

export interface UseApiResult<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
  refetch: () => void;
}

export interface UseMutationResult<TData, TVariables> {
  mutate: (variables: TVariables) => Promise<TData>;
  data: TData | null;
  loading: boolean;
  error: ApiError | null;
}

// ============================================================================
// Webhook Types
// ============================================================================

export interface WebhookPayload {
  event: string;
  data: Record<string, any>;
  timestamp: string;
  signature: string;
}

export interface OrderWebhookPayload extends WebhookPayload {
  event: 'order.created' | 'order.updated' | 'order.cancelled';
  data: {
    order: Order;
    previous_status?: OrderStatus;
  };
}

export interface PaymentWebhookPayload extends WebhookPayload {
  event: 'payment.succeeded' | 'payment.failed' | 'payment.refunded';
  data: PaymentWebhookRequest;
}

// ============================================================================
// Business Logic Types
// ============================================================================

export interface BusinessConfig {
  min_order_amount: number;
  max_cart_items: number;
  cart_expiry_hours: number;
  supported_payment_methods: PaymentMethod[];
  delivery_areas: string[];
}

export interface OrderConstraints {
  min_amount: number;
  max_items_per_product: number;
  allowed_statuses_for_cancellation: OrderStatus[];
  allowed_status_transitions: Record<OrderStatus, OrderStatus[]>;
}

// ============================================================================
// Export Default Client Configuration
// ============================================================================

export const defaultApiConfig: ApiClientConfig = {
  baseUrl: process.env.NODE_ENV === 'production'
    ? 'https://api.frozenbot.com'
    : 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
};

// ============================================================================
// Type Guards
// ============================================================================

export function isApiError(error: any): error is ApiError {
  return error && typeof error.status === 'number' && error.error;
}

export function isValidationError(error: any): error is ValidationErrorResponse {
  return isApiError(error) && error.error?.error === 'validation_error';
}

export function isEmptyCart(cart: Cart | EmptyCart): cart is EmptyCart {
  return Array.isArray(cart.items) && cart.items.length === 0;
}

export function isOrder(data: any): data is Order {
  return data && typeof data.id === 'number' && typeof data.status === 'string';
}

export function isProduct(data: any): data is Product {
  return data && typeof data.id === 'number' && typeof data.name === 'string' && typeof data.price === 'number';
}

// ============================================================================
// Utility Functions
// ============================================================================

export function formatPrice(price: number): string {
  return `${Math.floor(price)}₽`;
}

export function formatWeight(weight?: number): string {
  if (!weight) return '';
  if (weight >= 1000) {
    return `${Math.floor(weight / 1000)}кг`;
  }
  return `${weight}г`;
}

export function getOrderStatusDisplay(status: OrderStatus): string {
  const statusMap: Record<OrderStatus, string> = {
    pending: 'Ожидает подтверждения',
    confirmed: 'Подтвержден',
    preparing: 'Готовится',
    ready: 'Готов к выдаче',
    completed: 'Выполнен',
    cancelled: 'Отменен'
  };
  return statusMap[status] || status;
}

export function calculateCartTotal(items: CartItem[]): number {
  return items.reduce((total, item) => total + item.total_price, 0);
}

export function isOrderCancellable(order: Order): boolean {
  return ['pending', 'confirmed'].includes(order.status);
}

export function isOrderModifiable(order: Order): boolean {
  return ['pending'].includes(order.status);
}

// ============================================================================
// Constants
// ============================================================================

export const ORDER_STATUSES: OrderStatus[] = [
  'pending',
  'confirmed',
  'preparing',
  'ready',
  'completed',
  'cancelled'
];

export const PAYMENT_METHODS: PaymentMethod[] = [
  'card',
  'cash',
  'transfer'
];

export const NOTIFICATION_TYPES: NotificationType[] = [
  'user',
  'broadcast'
];

export const PARSE_MODES: ParseMode[] = [
  'HTML',
  'Markdown'
];

export const API_ENDPOINTS = {
  // Auth
  LOGIN: '/auth/login',
  REFRESH: '/auth/refresh',

  // Users
  USERS: '/api/users',
  CURRENT_USER: '/api/users/me',

  // Products
  PRODUCTS: '/api/products',
  PRODUCT: (id: number) => `/api/products/${id}`,

  // Categories
  CATEGORIES: '/api/categories',
  CATEGORY: (id: number) => `/api/categories/${id}`,

  // Cart
  CART: (telegramId: TelegramUserId) => `/api/cart/${telegramId}`,
  CART_ITEMS: '/api/cart/items',
  CART_ITEM: (id: number) => `/api/cart/items/${id}`,

  // Orders
  ORDERS: '/api/orders',
  ORDER: (id: number) => `/api/orders/${id}`,
  ORDER_STATUS: (id: number) => `/api/orders/${id}/status`,

  // Admin
  DASHBOARD_STATS: '/api/admin/dashboard/stats',
  ORDER_ANALYTICS: '/api/admin/orders/stats',
  PRODUCT_ANALYTICS: '/api/admin/products/stats',

  // Notifications
  SEND_NOTIFICATION: '/api/notifications/send',

  // Payments
  PAYMENT_WEBHOOK: '/api/payments/webhook',
  PAYMENT_STATUS: (orderId: number) => `/api/payments/${orderId}/status`
} as const;