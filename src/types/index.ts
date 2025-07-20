// Authentication Types
export interface AuthState {
  isAuthenticated: boolean;
  shopDomain?: string;
  accessToken?: string;
  userInfo?: UserInfo;
}

export interface UserInfo {
  id: string;
  email: string;
  shop: string;
  name: string;
}

// Custom Fields Types
export interface CustomField {
  id: number;
  name: string;
  label: string;
  type: 'text' | 'number' | 'date' | 'select' | 'multi_select' | 'boolean';
  required: boolean;
  validation_rules?: ValidationRules;
  target_entity: 'product' | 'variant' | 'inventory_item' | 'location';
  created_at: string;
  updated_at: string;
}

export interface ValidationRules {
  min?: number;
  max?: number;
  options?: string[];
  pattern?: string;
  max_length?: number;
}

// Inventory Types
export interface InventoryItem {
  id: number;
  shopify_inventory_item_id: string;
  product_id: number;
  variant_id: number;
  sku: string;
  current_stock: number;
  available_stock: number;
  reorder_point: number;
  location_id: number;
}

// API Response Types
export interface APIResponse<T> {
  status: 'success' | 'error';
  data?: T;
  error?: string;
  message?: string;
}

// Store Types
export interface Store {
  id: number;
  shopify_domain: string;
  shop_name: string;
  email: string;
  currency: string;
  timezone: string;
  subscription_plan: string;
  subscription_status: string;
}

// Location Types
export interface Location {
  id: number;
  shopify_location_id: string;
  name: string;
  address: string;
  city: string;
  country: string;
  is_active: boolean;
  manages_inventory: boolean;
}
