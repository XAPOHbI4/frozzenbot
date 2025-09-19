// ==================== Core Entity Types ====================

// User Types (based on backend User model)
export enum UserRole {
  USER = "user",
  MANAGER = "manager",
  ADMIN = "admin"
}

export interface User {
  id: number;
  telegram_id: number;
  username?: string;
  first_name: string;
  last_name?: string;
  phone?: string;
  email?: string;
  role: UserRole;
  is_admin: boolean;
  is_active: boolean;
  last_login_at?: string;
  created_at: string;
  updated_at: string;
}

// Product Types (based on backend Product model)
export interface Product {
  id: number;
  name: string;
  description?: string;
  price: number;
  discount_price?: number;
  image_url?: string;
  is_active: boolean;
  is_available: boolean; // Alias for is_active for compatibility
  in_stock: boolean;
  weight?: number;
  sort_order: number;
  slug?: string;
  meta_title?: string;
  meta_description?: string;
  sku?: string;
  stock_quantity: number;
  min_stock_level: number;
  popularity_score: number;
  is_featured: boolean;
  calories_per_100g?: number;
  protein_per_100g?: number;
  fat_per_100g?: number;
  carbs_per_100g?: number;
  category_id?: number;
  category?: Category;
  created_at: string;
  updated_at: string;
}

// Category Types (based on backend Category model)
export interface Category {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

// Order Types (based on backend Order model)
export enum OrderStatus {
  PENDING = "pending",
  CONFIRMED = "confirmed",
  PREPARING = "preparing",
  READY = "ready",
  DELIVERING = "delivering",
  DELIVERED = "delivered",
  COMPLETED = "completed",
  CANCELLED = "cancelled",
  REFUNDED = "refunded",
  FAILED = "failed"
}

export enum OrderPriority {
  LOW = "low",
  NORMAL = "normal",
  HIGH = "high",
  VIP = "vip"
}

export interface OrderItem {
  id: number;
  order_id: number;
  product_id: number;
  quantity: number;
  price: number;
  product?: Product;
  total?: number; // Computed property: price * quantity
  created_at: string;
  updated_at: string;
}

export interface Order {
  id: number;
  user_id: number;
  status: OrderStatus;
  total_amount: number;
  customer_name: string;
  customer_phone: string;
  delivery_address?: string;
  notes?: string;
  payment_method: string;
  priority: OrderPriority;
  estimated_preparation_time?: number;
  estimated_delivery_time?: string;
  actual_preparation_start?: string;
  actual_preparation_end?: string;
  delivery_scheduled_at?: string;
  delivery_completed_at?: string;
  status_pending_at: string;
  status_confirmed_at?: string;
  status_preparing_at?: string;
  status_ready_at?: string;
  status_completed_at?: string;
  status_cancelled_at?: string;
  kitchen_notes?: string;
  requires_special_handling: boolean;
  delivery_type: string;
  delivery_instructions?: string;
  courier_assigned?: string;
  cancellation_reason?: string;
  cancelled_by_user_id?: number;
  refund_amount?: number;
  refund_reason?: string;
  preparation_duration?: number;
  total_duration?: number;
  user?: User;
  items?: OrderItem[];
  // Additional properties used in frontend components
  telegram_username?: string;
  telegram_user_id?: number;
  phone_number?: string;
  confirmed_at?: string;
  delivered_at?: string;
  created_at: string;
  updated_at: string;
}

// ==================== Form Data Types ====================

export interface LoginRequest {
  email?: string;
  username?: string;
  password: string;
}

export interface ProductFormData {
  name: string;
  description: string;
  price: number;
  category_id: number;
  image_url?: string;
  is_active: boolean;
  is_available: boolean; // Alias for is_active for compatibility
  stock_quantity: number;
  discount_price?: number;
  weight?: number;
  sku?: string;
  min_stock_level?: number;
  is_featured?: boolean;
  calories_per_100g?: number;
  protein_per_100g?: number;
  fat_per_100g?: number;
  carbs_per_100g?: number;
}

export interface CategoryFormData {
  name: string;
  description?: string;
  is_active: boolean;
}

export interface OrderStatusUpdate {
  status: OrderStatus;
  notes?: string;
  kitchen_notes?: string;
  estimated_preparation_time?: number;
}

// ==================== API Response Types ====================

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T = any> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface ErrorResponse {
  message: string;
  details?: string;
  code?: string;
}

export interface ValidationError {
  field: string;
  message: string;
}

// ==================== Dashboard & Analytics Types ====================

export interface DashboardStats {
  total_orders: number;
  total_revenue: number;
  pending_orders: number;
  total_products: number;
  low_stock_products: number;
  orders_today: number;
  revenue_today: number;
  orders_this_week: number;
  revenue_this_week: number;
  orders_this_month: number;
  revenue_this_month: number;
}

export interface RevenueData {
  date: string;
  revenue: number;
  orders: number;
}

export interface ProductSalesData {
  product_id: number;
  product_name: string;
  total_sold: number;
  total_revenue: number;
}

export interface OrdersByStatusData {
  status: OrderStatus;
  count: number;
}

// ==================== API Client Types ====================

export interface ProductCreateRequest extends ProductFormData {}
export interface ProductUpdateRequest extends Partial<ProductFormData> {}

export interface CategoryCreateRequest extends CategoryFormData {}
export interface CategoryUpdateRequest extends Partial<CategoryFormData> {}

export interface OrderCreateRequest {
  customer_name: string;
  customer_phone: string;
  delivery_address?: string;
  notes?: string;
  payment_method: string;
  delivery_type: string;
  items: Array<{
    product_id: number;
    quantity: number;
  }>;
}

export interface OrderStatusUpdateRequest extends OrderStatusUpdate {}

export interface UserCreateRequest {
  telegram_id: number;
  username?: string;
  first_name: string;
  last_name?: string;
  phone?: string;
  email?: string;
  role?: UserRole;
}

// ==================== Analytics Types ====================

export interface OrderAnalytics {
  total_orders: number;
  total_revenue: number;
  orders_by_status: { [key in OrderStatus]: number };
  revenue_by_period: Array<{
    date: string;
    revenue: number;
    orders: number;
  }>;
  average_order_value: number;
  popular_payment_methods: Array<{
    method: string;
    count: number;
    percentage: number;
  }>;
}

export interface ProductAnalytics {
  total_products: number;
  active_products: number;
  out_of_stock: number;
  low_stock: number;
  top_selling: Array<{
    product_id: number;
    product_name: string;
    total_sold: number;
    revenue: number;
  }>;
  category_distribution: Array<{
    category_id: number;
    category_name: string;
    product_count: number;
  }>;
}

// ==================== Admin Panel UI Types ====================

export interface FormErrors {
  [key: string]: string;
}

export interface SelectOption {
  value: string | number;
  label: string;
}

export interface TableColumn<T = any> {
  key: keyof T;
  label: string;
  sortable?: boolean;
  render?: (value: any, item: T) => React.ReactNode;
}

export interface SortConfig {
  key: string;
  direction: 'asc' | 'desc';
}

// Navigation Types
export interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: number;
}