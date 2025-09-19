import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import {
  ApiResponse,
  PaginatedResponse,
  Product,
  ProductCreateRequest,
  ProductUpdateRequest,
  Category,
  CategoryCreateRequest,
  CategoryUpdateRequest,
  Order,
  OrderStatusUpdateRequest,
  User,
  DashboardStats,
  OrderAnalytics,
  ProductAnalytics,
  AuthResponse,
  LoginRequest,
} from '../types';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: '/api',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for auth
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('access_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Generic API methods
  private async get<T>(url: string): Promise<T> {
    const response = await this.client.get<ApiResponse<T>>(url);
    return response.data.data as T;
  }

  private async post<T>(url: string, data: any): Promise<T> {
    const response = await this.client.post<ApiResponse<T>>(url, data);
    return response.data.data as T;
  }

  private async put<T>(url: string, data: any): Promise<T> {
    const response = await this.client.put<ApiResponse<T>>(url, data);
    return response.data.data as T;
  }

  private async delete<T>(url: string): Promise<T> {
    const response = await this.client.delete<ApiResponse<T>>(url);
    return response.data.data as T;
  }

  // Authentication
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/auth/login', credentials);
    return response.data;
  }

  async refreshToken(): Promise<AuthResponse> {
    return this.post<AuthResponse>('/auth/refresh', {});
  }

  async getCurrentUser(): Promise<User> {
    return this.get<User>('/users/me');
  }

  // Products
  async getProducts(params?: {
    page?: number;
    per_page?: number;
    search?: string;
    category_id?: number;
    is_available?: boolean;
  }): Promise<PaginatedResponse<Product>> {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }
    return this.get<PaginatedResponse<Product>>(`/products?${queryParams}`);
  }

  async getProduct(id: number): Promise<Product> {
    return this.get<Product>(`/products/${id}`);
  }

  async createProduct(data: ProductCreateRequest): Promise<Product> {
    return this.post<Product>('/products', data);
  }

  async updateProduct(id: number, data: ProductUpdateRequest): Promise<Product> {
    return this.put<Product>(`/products/${id}`, data);
  }

  async deleteProduct(id: number): Promise<void> {
    return this.delete<void>(`/products/${id}`);
  }

  // Categories
  async getCategories(): Promise<Category[]> {
    return this.get<Category[]>('/categories');
  }

  async createCategory(data: CategoryCreateRequest): Promise<Category> {
    return this.post<Category>('/categories', data);
  }

  async updateCategory(id: number, data: CategoryUpdateRequest): Promise<Category> {
    return this.put<Category>(`/categories/${id}`, data);
  }

  async deleteCategory(id: number): Promise<void> {
    return this.delete<void>(`/categories/${id}`);
  }

  // Orders
  async getOrders(params?: {
    page?: number;
    per_page?: number;
    status?: string;
    telegram_id?: number;
  }): Promise<PaginatedResponse<Order>> {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }
    return this.get<PaginatedResponse<Order>>(`/orders?${queryParams}`);
  }

  async getOrder(id: number): Promise<Order> {
    return this.get<Order>(`/orders/${id}`);
  }

  async updateOrderStatus(id: number, data: OrderStatusUpdateRequest): Promise<Order> {
    return this.put<Order>(`/orders/${id}/status`, data);
  }

  // Admin Analytics
  async getDashboardStats(): Promise<DashboardStats> {
    return this.get<DashboardStats>('/admin/dashboard/stats');
  }

  async getOrderAnalytics(params?: {
    start_date?: string;
    end_date?: string;
  }): Promise<OrderAnalytics> {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value);
        }
      });
    }
    return this.get<OrderAnalytics>(`/admin/orders/stats?${queryParams}`);
  }

  async getProductAnalytics(): Promise<ProductAnalytics> {
    return this.get<ProductAnalytics>('/admin/products/stats');
  }
}

export const apiClient = new ApiClient();
export default apiClient;