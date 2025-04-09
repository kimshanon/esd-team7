/**
 * API Configuration
 * 
 * Central configuration for all API endpoints
 */

// Base URL for all services
export const API_BASE_URL = `http://localhost:8000`; // Using Kong's proxy port

// Service-specific endpoint URLs
export const CUSTOMER_URL = `${API_BASE_URL}/api/customer`;
export const PICKER_URL = `${API_BASE_URL}/api/picker`;
export const STALL_URL = `${API_BASE_URL}/api/stall`;
export const ORDER_URL = `${API_BASE_URL}/api/order`;
export const PAYMENT_URL = `${API_BASE_URL}/api/payment`;
export const ASSIGN_PICKER_URL = `${API_BASE_URL}/api/assign-picker`;
export const CREDIT_URL = `${API_BASE_URL}/api/credit`;
export const LOCATION_URL = `${API_BASE_URL}/api/location`;
export const CANCELLATION_URL = `${API_BASE_URL}/api/cancellation`;
