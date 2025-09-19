/**
 * Core Business Model Interfaces
 * Generated from OpenAPI specification for FrozenBot API
 */

// User Models
export interface User {
  id: number;
  telegram_id: number;
  username?: string | null;
  first_name: string;
  last_name?: string | null;
  phone?: string | null;
  is_admin: boolean;
  is_active: boolean;
  full_name: string; // readonly computed field
  created_at: string;
  updated_at: string;
}

export interface UserCreateRequest {
  telegram_id: number;
  username?: string | null;
  first_name: string;
  last_name?: string | null;
  phone?: string | null;
}

// Category Models
export interface Category {
  id: number;
  name: string;
  description?: string | null;
  image_url?: string | null;
  is_active: boolean;
  sort_order: number;
  products_count: number; // readonly computed field
  created_at: string;
  updated_at: string;
}

export interface CategoryCreateRequest {
  name: string;
  description?: string | null;
  image_url?: string | null;
  is_active?: boolean;
  sort_order?: number;
}

export interface CategoryUpdateRequest {
  name?: string;
  description?: string | null;
  image_url?: string | null;
  is_active?: boolean;
  sort_order?: number;
}

// Product Models
export interface Product {
  id: number;
  name: string;
  description?: string | null;
  price: number;
  formatted_price: string; // readonly computed field
  image_url?: string | null;
  is_active: boolean;
  in_stock: boolean;
  weight?: number | null; // in grams
  formatted_weight?: string; // readonly computed field
  sort_order: number;
  category_id?: number | null;
  category?: Category;
  created_at: string;
  updated_at: string;
}

export interface ProductCreateRequest {
  name: string;
  description?: string | null;
  price: number;
  image_url?: string | null;
  is_active?: boolean;
  in_stock?: boolean;
  weight?: number | null;
  sort_order?: number;
  category_id?: number | null;
}

export interface ProductUpdateRequest {
  name?: string;
  description?: string | null;
  price?: number;
  image_url?: string | null;
  is_active?: boolean;
  in_stock?: boolean;
  weight?: number | null;
  sort_order?: number;
  category_id?: number | null;
}

// Cart Models
export interface Cart {
  id: number;
  user_id: number;
  items: CartItem[];
  total_amount: number; // readonly computed field
  total_items: number; // readonly computed field
  expires_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface EmptyCart {
  items: [];
  total_amount: 0;
  total_items: 0;
}

export interface CartItem {
  id: number;
  cart_id: number;
  product_id: number;
  quantity: number;
  product: Product;
  total_price: number; // readonly computed field
  created_at: string;
  updated_at: string;
}

export interface CartItemCreateRequest {
  telegram_id: number;
  product_id: number;
  quantity: number;
}

export interface CartItemUpdateRequest {
  quantity: number;
}

// Order Models
export type OrderStatus =
  | 'pending'
  | 'confirmed'
  | 'preparing'
  | 'ready'
  | 'completed'
  | 'cancelled';

export interface Order {
  id: number;
  user_id: number;
  status: OrderStatus;
  status_display: string; // readonly computed field
  total_amount: number;
  formatted_total: string; // readonly computed field
  customer_name: string;
  customer_phone: string;
  delivery_address?: string | null;
  notes?: string | null;
  payment_method: string;
  items: OrderItem[];
  user: User;
  created_at: string;
  updated_at: string;
}

export interface OrderItem {
  id: number;
  order_id: number;
  product_id: number;
  quantity: number;
  price: number; // price at time of order
  formatted_price: string; // readonly computed field
  total_price: number; // readonly computed field
  formatted_total: string; // readonly computed field
  product: Product;
}

export interface OrderCreateRequest {
  telegram_id: number;
  customer_name: string;
  customer_phone: string;
  delivery_address?: string | null;
  notes?: string | null;
  payment_method?: string;
}

export interface OrderStatusUpdateRequest {
  status: OrderStatus;
}

// Analytics Models
export interface DashboardStats {
  total_orders: number;
  total_revenue: number;
  active_users: number;
  pending_orders: number;
  today_orders: number;
  today_revenue: number;
  popular_products: Array<{
    product: Product;
    orders_count: number;
    total_revenue: number;
  }>;
  recent_orders: Order[];
}

export interface OrderAnalytics {
  period: 'day' | 'week' | 'month' | 'year';
  total_orders: number;
  total_revenue: number;
  average_order_value: number;
  orders_by_status: Record<OrderStatus, number>;
  revenue_chart: Array<{
    date: string;
    revenue: number;
  }>;
  orders_chart: Array<{
    date: string;
    count: number;
  }>;
}

export interface ProductAnalytics {
  period: 'day' | 'week' | 'month' | 'year';
  top_products: Array<{
    product: Product;
    orders_count: number;
    revenue: number;
  }>;
  categories_performance: Array<{
    category: Category;
    orders_count: number;
    revenue: number;
  }>;
  inventory_status: {
    total_products: number;
    active_products: number;
    out_of_stock: number;
  };
}

// Payment Models
export type PaymentStatus = 'pending' | 'success' | 'failed' | 'refunded';

export interface PaymentWebhookRequest {
  order_id: number;
  status: 'success' | 'failed' | 'pending';
  amount: number;
  transaction_id?: string;
  payment_method?: string;
  metadata?: Record<string, any>;
}

export interface PaymentStatusResponse {
  order_id: number;
  status: PaymentStatus;
  amount: number;
  transaction_id?: string | null;
  payment_method: string;
  created_at: string;
  updated_at: string;
}

// Notification Models
export interface NotificationRequest {
  type: 'user' | 'broadcast';
  telegram_id?: number; // required for type=user
  message: string;
  parse_mode?: 'HTML' | 'Markdown';
}

export interface NotificationResponse {
  success: boolean;
  message: string;
  sent_count?: number; // for broadcast notifications
}