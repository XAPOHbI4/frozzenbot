/**
 * useCatalog Hook
 * Manages catalog data fetching and state
 */

import { useState, useCallback, useEffect } from 'react';
import { Product, Category } from '../types';
import { WebAppApiClient } from '../services/apiClient';

interface CatalogState {
  products: Product[];
  categories: Category[];
  selectedCategoryId: number | null;
  loading: boolean;
  error: string | null;
  lastUpdated: string | null;
}

interface UseCatalogReturn extends CatalogState {
  setSelectedCategory: (categoryId: number | null) => void;
  loadProducts: () => Promise<void>;
  loadCategories: () => Promise<void>;
  refreshCatalog: () => Promise<void>;
  clearError: () => void;
}

export const useCatalog = (apiClient: WebAppApiClient): UseCatalogReturn => {
  const [state, setState] = useState<CatalogState>({
    products: [],
    categories: [],
    selectedCategoryId: null,
    loading: false,
    error: null,
    lastUpdated: null,
  });

  // Clear error
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  // Set selected category
  const setSelectedCategory = useCallback((categoryId: number | null) => {
    setState(prev => ({
      ...prev,
      selectedCategoryId: categoryId,
      error: null
    }));
  }, []);

  // Load products from API
  const loadProducts = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));

      const response = await apiClient.getProducts();
      const products = response.products || [];

      // Filter and sort products
      const validProducts = products
        .filter((product: Product) => product.is_active && product.in_stock)
        .sort((a: Product, b: Product) => a.sort_order - b.sort_order);

      setState(prev => ({
        ...prev,
        products: validProducts,
        loading: false,
        lastUpdated: new Date().toISOString(),
      }));
    } catch (error) {
      console.error('Failed to load products:', error);
      setState(prev => ({
        ...prev,
        products: [],
        loading: false,
        error: 'Не удалось загрузить товары. Проверьте подключение к интернету.',
      }));
    }
  }, [apiClient]);

  // Load categories from API
  const loadCategories = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));

      const response = await apiClient.getCategories();
      const categories = response.categories || [];

      // Filter and sort categories
      const validCategories = categories
        .filter((category: Category) => category.is_active)
        .sort((a: Category, b: Category) => a.sort_order - b.sort_order);

      setState(prev => ({
        ...prev,
        categories: validCategories,
        loading: false,
        lastUpdated: new Date().toISOString(),
      }));
    } catch (error) {
      console.error('Failed to load categories:', error);
      setState(prev => ({
        ...prev,
        categories: [],
        loading: false,
        error: 'Не удалось загрузить категории. Проверьте подключение к интернету.',
      }));
    }
  }, [apiClient]);

  // Refresh entire catalog
  const refreshCatalog = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      // Load both products and categories in parallel
      const [productsResponse, categoriesResponse] = await Promise.all([
        apiClient.getProducts(),
        apiClient.getCategories(),
      ]);

      const products = productsResponse.products || [];
      const categories = categoriesResponse.categories || [];

      // Process products
      const validProducts = products
        .filter((product: Product) => product.is_active && product.in_stock)
        .sort((a: Product, b: Product) => a.sort_order - b.sort_order);

      // Process categories
      const validCategories = categories
        .filter((category: Category) => category.is_active)
        .sort((a: Category, b: Category) => a.sort_order - b.sort_order);

      setState(prev => ({
        ...prev,
        products: validProducts,
        categories: validCategories,
        loading: false,
        lastUpdated: new Date().toISOString(),
      }));
    } catch (error) {
      console.error('Failed to refresh catalog:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: 'Не удалось обновить каталог. Проверьте подключение к интернету.',
      }));
    }
  }, [apiClient]);

  // Auto-refresh catalog periodically (optional)
  useEffect(() => {
    const refreshInterval = 5 * 60 * 1000; // 5 minutes
    let intervalId: NodeJS.Timeout;

    // Only set up auto-refresh if we have data
    if (state.products.length > 0 || state.categories.length > 0) {
      intervalId = setInterval(() => {
        // Silently refresh in background
        refreshCatalog();
      }, refreshInterval);
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [refreshCatalog, state.products.length, state.categories.length]);

  return {
    ...state,
    setSelectedCategory,
    loadProducts,
    loadCategories,
    refreshCatalog,
    clearError,
  };
};

export default useCatalog;