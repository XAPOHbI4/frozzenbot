/**
 * Authentication types for FrozenBot
 * Shared between frontend and backend
 */

// User roles enum
export enum UserRole {
  USER = 'user',
  MANAGER = 'manager',
  ADMIN = 'admin'
}

// Base user interface
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
  full_name: string;
  created_at: string;
  updated_at: string;
  last_login_at?: string;
}

// Authentication request types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface TelegramInitData {
  init_data: string;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface RegisterUserRequest {
  username: string;
  password: string;
  first_name: string;
  last_name?: string;
  email?: string;
  role: UserRole;
}

export interface LogoutRequest {
  refresh_token?: string;
}

// Authentication response types
export interface TokenResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
}

export interface LoginResponse extends TokenResponse {
  refresh_token: string;
  user: User;
}

export interface AuthResponse extends LoginResponse {}

// JWT Token payload interface
export interface TokenPayload {
  user_id: number;
  role: UserRole;
  telegram_id: number;
  username?: string;
  exp: number;
  iat: number;
  type: 'access' | 'refresh';
  jti: string;
}

// Authentication status
export interface AuthStatus {
  authenticated: boolean;
  user?: User;
  permissions: string[];
  expires_at?: string;
}

// Password validation
export interface PasswordValidation {
  valid: boolean;
  strength: 'weak' | 'medium' | 'strong';
  score: number;
  errors: string[];
}

// Permission types
export type Permission =
  // Order permissions
  | 'order:create'
  | 'order:view_own'
  | 'order:view_all'
  | 'order:update'
  | 'order:delete'

  // Product permissions
  | 'product:view'
  | 'product:create'
  | 'product:update'
  | 'product:delete'

  // Category permissions
  | 'category:view'
  | 'category:create'
  | 'category:update'
  | 'category:delete'

  // User permissions
  | 'user:view_basic'
  | 'user:view_all'
  | 'user:create'
  | 'user:update'
  | 'user:delete'

  // Admin permissions
  | 'admin:access'
  | 'admin:analytics'
  | 'admin:settings'

  // Special permissions
  | '*'; // Admin wildcard

// Role permissions mapping
export const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  [UserRole.USER]: [
    'order:create',
    'order:view_own',
    'product:view',
    'category:view'
  ],
  [UserRole.MANAGER]: [
    'order:create',
    'order:view_own',
    'order:view_all',
    'order:update',
    'product:view',
    'product:create',
    'product:update',
    'product:delete',
    'category:view',
    'category:create',
    'category:update',
    'category:delete',
    'user:view_basic'
  ],
  [UserRole.ADMIN]: ['*']
};

// Auth context interface for React
export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<LoginResponse>;
  loginWithTelegram: (initData: string) => Promise<LoginResponse>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<TokenResponse | null>;
  changePassword: (data: ChangePasswordRequest) => Promise<void>;
  hasPermission: (permission: Permission) => boolean;
  hasRole: (role: UserRole) => boolean;
  canAccessAdminPanel: () => boolean;
}

// Auth hook return type
export interface UseAuthReturn extends AuthContextType {}

// API error types related to auth
export interface AuthError {
  message: string;
  code: 'INVALID_CREDENTIALS' | 'TOKEN_EXPIRED' | 'INSUFFICIENT_PERMISSIONS' | 'ACCOUNT_LOCKED' | 'VALIDATION_ERROR';
  details?: any;
}

// Rate limiting info
export interface RateLimitInfo {
  allowed: boolean;
  remaining: number;
  resetTime: string;
  currentAttempts: number;
}

// Security event types
export interface SecurityEvent {
  type: 'login' | 'logout' | 'failed_login' | 'password_change' | 'token_refresh';
  user_id?: number;
  ip_address?: string;
  user_agent?: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

// Telegram user data from WebApp
export interface TelegramUser {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  is_premium?: boolean;
  photo_url?: string;
}

// Telegram WebApp init data parsed
export interface TelegramWebAppData {
  user?: TelegramUser;
  chat_instance?: string;
  chat_type?: string;
  start_param?: string;
  auth_date: number;
  hash: string;
}

// Form validation helpers
export interface ValidationRule {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  custom?: (value: any) => string | null;
}

export interface FieldValidation {
  [field: string]: ValidationRule[];
}

// Auth form validation schemas
export const AUTH_VALIDATION: Record<string, FieldValidation> = {
  login: {
    username: [
      { required: true },
      { minLength: 3 },
      { maxLength: 50 }
    ],
    password: [
      { required: true },
      { minLength: 6 },
      { maxLength: 100 }
    ]
  },
  register: {
    username: [
      { required: true },
      { minLength: 3 },
      { maxLength: 50 },
      { pattern: /^[a-zA-Z0-9_]+$/ }
    ],
    password: [
      { required: true },
      { minLength: 8 },
      { maxLength: 128 }
    ],
    first_name: [
      { required: true },
      { minLength: 1 },
      { maxLength: 100 }
    ],
    email: [
      { pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/ }
    ]
  },
  changePassword: {
    current_password: [
      { required: true },
      { minLength: 6 }
    ],
    new_password: [
      { required: true },
      { minLength: 8 },
      { maxLength: 128 }
    ]
  }
};

// Local storage keys for auth
export const AUTH_STORAGE_KEYS = {
  ACCESS_TOKEN: 'auth_access_token',
  REFRESH_TOKEN: 'auth_refresh_token',
  USER: 'auth_user',
  EXPIRES_AT: 'auth_expires_at'
} as const;

// Auth API endpoints
export const AUTH_ENDPOINTS = {
  LOGIN: '/api/auth/login',
  TELEGRAM_LOGIN: '/api/auth/telegram',
  REFRESH: '/api/auth/refresh',
  LOGOUT: '/api/auth/logout',
  LOGOUT_ALL: '/api/auth/logout-all',
  ME: '/api/auth/me',
  CHANGE_PASSWORD: '/api/auth/change-password',
  REGISTER: '/api/auth/register',
  VALIDATE: '/api/auth/validate',
  HEALTH: '/api/auth/health'
} as const;

// HTTP status codes for auth
export const AUTH_STATUS_CODES = {
  OK: 200,
  CREATED: 201,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  TOO_MANY_REQUESTS: 429,
  INTERNAL_SERVER_ERROR: 500
} as const;

// Auth-related utility types
export type AuthToken = string;
export type UserId = number;
export type TelegramId = number;