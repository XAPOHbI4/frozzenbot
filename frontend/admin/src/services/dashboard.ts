import api from './api';
import { DashboardStats, RevenueData, ProductSalesData, OrdersByStatusData } from '../types';

// Get dashboard statistics
export const getDashboardStats = async (): Promise<DashboardStats> => {
  try {
    const response = await api.get('/admin/dashboard/stats');
    return response.data;
  } catch (error) {
    // Return default stats if API fails
    return {
      total_orders: 0,
      total_revenue: 0,
      pending_orders: 0,
      total_products: 0,
      low_stock_products: 0,
      orders_today: 0,
      revenue_today: 0,
      orders_this_week: 0,
      revenue_this_week: 0,
      orders_this_month: 0,
      revenue_this_month: 0,
    };
  }
};

// Get revenue data for charts
export const getRevenueData = async (
  period: '7d' | '30d' | '90d' = '30d'
): Promise<RevenueData[]> => {
  const response = await api.get(`/admin/dashboard/revenue?period=${period}`);
  return response.data;
};

// Get product sales data
export const getProductSalesData = async (): Promise<ProductSalesData[]> => {
  const response = await api.get('/admin/dashboard/product-sales');
  return response.data;
};

// Get orders by status data
export const getOrdersByStatusData = async (): Promise<OrdersByStatusData[]> => {
  const response = await api.get('/admin/dashboard/orders-by-status');
  return response.data;
};