import api from './api';
import { Product, ProductFormData } from '../types';

// Get all products with pagination and filtering
export const getProducts = async (params?: {
  page?: number;
  per_page?: number;
  category_id?: number;
  search?: string;
  is_available?: boolean;
}): Promise<Product[]> => {
  const response = await api.get('/products', { params });
  // Handle both paginated and non-paginated responses
  return response.data.items || response.data;
};

// Get single product
export const getProduct = async (id: number): Promise<Product> => {
  const response = await api.get(`/products/${id}`);
  return response.data;
};

// Create new product
export const createProduct = async (data: ProductFormData): Promise<Product> => {
  const response = await api.post('/products', data);
  return response.data;
};

// Update product
export const updateProduct = async (id: number, data: Partial<ProductFormData>): Promise<Product> => {
  const response = await api.put(`/products/${id}`, data);
  return response.data;
};

// Delete product
export const deleteProduct = async (id: number): Promise<void> => {
  await api.delete(`/products/${id}`);
};

// Toggle product availability
export const toggleAvailability = async (id: number): Promise<Product> => {
  const response = await api.patch(`/products/${id}/toggle-availability`);
  return response.data;
};

// Upload product image
export const uploadImage = async (file: File): Promise<{ image_url: string }> => {
  const formData = new FormData();
  formData.append('image', file);

  const response = await api.post('/products/upload-image', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};