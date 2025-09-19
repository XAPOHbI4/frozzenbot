import api from './api';
import { Category, CategoryFormData } from '../types';

// Get all categories
export const getCategories = async (): Promise<Category[]> => {
  const response = await api.get('/categories');
  return response.data;
};

// Get single category
export const getCategory = async (id: number): Promise<Category> => {
  const response = await api.get(`/categories/${id}`);
  return response.data;
};

// Create new category
export const createCategory = async (data: CategoryFormData): Promise<Category> => {
  const response = await api.post('/categories', data);
  return response.data;
};

// Update category
export const updateCategory = async (id: number, data: Partial<CategoryFormData>): Promise<Category> => {
  const response = await api.put(`/categories/${id}`, data);
  return response.data;
};

// Delete category
export const deleteCategory = async (id: number): Promise<void> => {
  await api.delete(`/categories/${id}`);
};

// Toggle category active status
export const toggleActive = async (id: number): Promise<Category> => {
  const response = await api.patch(`/categories/${id}/toggle-active`);
  return response.data;
};