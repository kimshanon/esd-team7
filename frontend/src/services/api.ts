import axios from "axios";
import { Stall, Restaurant, MenuItem, MenuItemFrontend } from "../types/types";

const API_URL = "http://127.0.0.1:5002";
const ORDER_API_URL = "http://127.0.0.1:5003";

// Map backend stall data to frontend restaurant format
export const mapStallToRestaurant = (stall: Stall): Restaurant => {
  return {
    id: stall.id,
    name: stall.stall_name,
    image: stall.stall_image,
    description: stall.stall_description,
    rating: stall.rating,
    reviewCount: stall.review_count,
    cuisines: stall.cuisines,
    deliveryTime: stall.preparation_time_mins,
    deliveryFee: stall.delivery_fee,
    location: stall.stall_location,
    isPromoted: stall.is_promoted,
    menu: stall.menu.map(mapMenuItemToFrontend),
  };
};

// Map backend menu item to frontend format
export const mapMenuItemToFrontend = (item: MenuItem): MenuItemFrontend => {
  return {
    id: item.id,
    name: item.food_name,
    price: item.food_price,
    description: item.food_description,
    category: item.food_category,
    image: item.food_image,
  };
};

// Fetch all restaurants
export const fetchAllRestaurants = async (): Promise<Restaurant[]> => {
  try {
    const response = await axios.get<Stall[]>(`${API_URL}/stalls`);
    return response.data.map(mapStallToRestaurant);
  } catch (error) {
    console.error("Error fetching restaurants:", error);
    throw error;
  }
};

// Fetch a single restaurant by ID
export const fetchRestaurantById = async (id: string): Promise<Restaurant> => {
  try {
    const response = await axios.get<Stall>(`${API_URL}/stalls/${id}`);
    return mapStallToRestaurant(response.data);
  } catch (error) {
    console.error(`Error fetching restaurant with ID ${id}:`, error);
    throw error;
  }
};

// Fetch menu for a restaurant
export const fetchRestaurantMenu = async (
  id: string
): Promise<MenuItemFrontend[]> => {
  try {
    const response = await axios.get<MenuItem[]>(
      `${API_URL}/stalls/${id}/menu`
    );
    return response.data.map(mapMenuItemToFrontend);
  } catch (error) {
    console.error(`Error fetching menu for restaurant ${id}:`, error);
    throw error;
  }
};

// Create a new order
export const createOrder = async (orderData: any) => {
  try {
    const response = await axios.post(`${ORDER_API_URL}/orders`, orderData);
    return response.data;
  } catch (error) {
    console.error("Error creating order:", error);
    throw error;
  }
};

// Fetch orders for a customer
export const fetchCustomerOrders = async (customerId: string) => {
  try {
    const response = await axios.get(
      `${ORDER_API_URL}/customers/${customerId}/orders`
    );
    return response.data;
  } catch (error) {
    console.error(`Error fetching orders for customer ${customerId}:`, error);
    throw error;
  }
};

// Fetch a specific order by ID
export const fetchOrderById = async (orderId: string) => {
  try {
    const response = await axios.get(`${ORDER_API_URL}/orders/${orderId}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching order ${orderId}:`, error);
    throw error;
  }
};

// Fetch orders for a picker
export const fetchPickerOrders = async (pickerId: string) => {
  try {
    const response = await axios.get(
      `${ORDER_API_URL}/pickers/${pickerId}/orders`
    );
    return response.data;
  } catch (error) {
    console.error(`Error fetching orders for picker ${pickerId}:`, error);
    throw error;
  }
};
