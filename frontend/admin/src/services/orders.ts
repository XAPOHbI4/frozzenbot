import api from './api';
import { Order, OrderStatus, OrderStatusUpdate } from '../types';

// Get all orders with pagination and filtering
export const getOrders = async (params?: {
  page?: number;
  per_page?: number;
  status?: OrderStatus;
  date_from?: string;
  date_to?: string;
  search?: string;
}): Promise<Order[]> => {
  const response = await api.get('/orders', { params });
  // Handle both paginated and non-paginated responses
  return response.data.items || response.data;
};

// Get single order
export const getOrder = async (id: number): Promise<Order> => {
  const response = await api.get(`/orders/${id}`);
  return response.data;
};

// Update order status
export const updateOrderStatus = async (id: number, statusUpdate: OrderStatusUpdate): Promise<Order> => {
  const response = await api.put(`/orders/${id}/status`, statusUpdate);
  return response.data;
};

// Get order statistics
export const getOrderStats = async (period?: 'today' | 'week' | 'month' | 'year'): Promise<{
  total_orders: number;
  total_revenue: number;
  orders_by_status: { [key in OrderStatus]: number };
  revenue_by_period: Array<{ date: string; revenue: number; orders: number }>;
}> => {
  const response = await api.get('/orders/stats/summary', {
    params: { period }
  });
  return response.data;
};

// Export orders to CSV
export const exportOrders = async (params?: {
  date_from?: string;
  date_to?: string;
  status?: OrderStatus;
}): Promise<Blob> => {
  const response = await api.get('/orders/export', {
    params,
    responseType: 'blob',
  });
  return response.data;
};