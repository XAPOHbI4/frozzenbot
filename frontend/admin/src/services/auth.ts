import api from './api';
import { LoginRequest, AuthResponse, User } from '../types';

// Login
export const login = async (credentials: LoginRequest): Promise<AuthResponse> => {
  const response = await api.post('/auth/login', credentials);
  const authData = response.data;

  // Store token and user data
  localStorage.setItem('access_token', authData.access_token);
  localStorage.setItem('user', JSON.stringify(authData.user));

  return authData;
};

// Logout
export const logout = (): void => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
};

// Get current user from localStorage
export const getCurrentUser = (): User | null => {
  const userStr = localStorage.getItem('user');
  return userStr ? JSON.parse(userStr) : null;
};

// Check if user is authenticated
export const isAuthenticated = (): boolean => {
  const token = localStorage.getItem('access_token');
  const user = getCurrentUser();
  return !!(token && user);
};

// Check if user is admin
export const isAdmin = (): boolean => {
  const user = getCurrentUser();
  return user?.is_admin === true;
};

// Get current user profile from API
export const getProfile = async (): Promise<User> => {
  const response = await api.get('/users/me');
  return response.data;
};

// Refresh user data
export const refreshUser = async (): Promise<User> => {
  const user = await getProfile();
  localStorage.setItem('user', JSON.stringify(user));
  return user;
};