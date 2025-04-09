import axios from "axios";
import { Stall, Restaurant, MenuItem, MenuItemFrontend, FoodListingsResponse, SingleFoodListingResponse, FoodListing } from "../types/types";

const API_URL = "http://127.0.0.1:5002";
const ORDER_API_URL = "http://127.0.0.1:5003";
const FOOD_LISTINGS_API_URL = "https://personal-9l4pf9hj.outsystemscloud.com/FoodListingsAPI/rest/FoodListingAPI";



// Map backend stall data to frontend restaurant format
export const mapStallToRestaurant = (stall: Stall): Restaurant => {
  return {
    id: stall.stall_id.toString(),
    name: stall.stall_name,
    image: stall.stall_image || "", // Use empty string if no image is provided
    description: stall.stall_description,
    rating: stall.stall_rating,
    reviewCount: stall.review_count,
    cuisines: [], // You might want to add this data if available
    deliveryTime: stall.preparation_time_mins,
    deliveryFee: stall.delivery_fee,
    location: stall.stall_location,
    isPromoted: stall.is_promoted,
    menu: [], // You might want to fetch this separately
  };
};

// Map backend menu item to frontend format
export const mapMenuItemToFrontend = (item: MenuItem): MenuItemFrontend => {
  return {
    id: item.menu_item_id.toString(),
    name: item.food_name,
    price: item.food_price,
    description: item.food_description,
    category: item.food_category,
    image: item.food_image,
  };
};

interface StallResponse {
  FoodStalls: Stall[];
}

interface MenuResponse {
  StallItems: MenuItem[];
}

// Fetch all restaurants
export const fetchAllRestaurants = async (): Promise<Restaurant[]> => {
  try {
    const response = await axios.get<StallResponse>(`https://personal-dcwqxa6n.outsystemscloud.com/SMUlivery/rest/FoodStallAPI/GetAllStalls`);
    return response.data["FoodStalls"].map(mapStallToRestaurant);
  } catch (error) {
    console.error("Error fetching restaurants:", error);
    throw error;
  }
};

// Fetch a single restaurant by ID
export const fetchRestaurantById = async (id: string): Promise<Restaurant> => {
  try {
    // Fetch both restaurant and menu data
    const [stallResponse, menuResponse] = await Promise.all([
      axios.get<StallResponse>(`https://personal-dcwqxa6n.outsystemscloud.com/SMUlivery/rest/FoodStallAPI/GetAllStalls`),
      axios.get<MenuResponse>(`https://personal-dcwqxa6n.outsystemscloud.com/SMUlivery/rest/FoodStallAPI/GetAllFoodFromStall/${id}`)
    ]);

    // Find the specific stall from the response
    const stall = stallResponse.data.FoodStalls.find(s => s.stall_id.toString() === id);
    
    if (!stall) {
      throw new Error(`Restaurant with ID ${id} not found`);
    }

    // Convert stall to restaurant format and include menu
    const restaurant = mapStallToRestaurant(stall);
    restaurant.menu = menuResponse.data.StallItems.map(mapMenuItemToFrontend);

    return restaurant;
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
    const response = await axios.get<MenuResponse>(
      `https://personal-dcwqxa6n.outsystemscloud.com/SMUlivery/rest/FoodStallAPI/GetAllFoodFromStall/${id}`
    );
    return response.data.StallItems.map(mapMenuItemToFrontend);

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

// Fetch all food listings from Stamford Road
export const fetchStamfordFoodListings = async (): Promise<FoodListing[]> => {
  try {
    const response = await axios.get<FoodListingsResponse>(`${FOOD_LISTINGS_API_URL}/FoodListings`);
    
    // Filter for any Stamford Road listings (case insensitive)
    const stamfordListings = response.data.FoodListings.filter(
      listing => listing.PickupAddress.toLowerCase().includes("stamford road")
    );

    // Create a map to deduplicate listings based on unique characteristics
    const uniqueListings = new Map<string, FoodListing>();
    
    stamfordListings.forEach(listing => {
      // Create a unique key based on title, restaurant, and expiry time
      const key = `${listing.Title}-${listing.RestaurantName}-${listing.ExpiryTime}`;
      
      // If we haven't seen this listing before, add it to our map
      if (!uniqueListings.has(key)) {
        // Remove price information
        const listingWithoutPrice = { ...listing };
        delete listingWithoutPrice.Price;
        uniqueListings.set(key, listingWithoutPrice);
      }
    });
    
    // Convert the map values back to an array and sort by expiry time
    return Array.from(uniqueListings.values()).sort((a, b) => 
      new Date(a.ExpiryTime).getTime() - new Date(b.ExpiryTime).getTime()
    );
  } catch (error) {
    console.error("Error fetching Stamford food listings:", error);
    throw error;
  }
};

// Fetch a single food listing by ID
export const fetchFoodListingById = async (id: number): Promise<FoodListing> => {
  try {
    const response = await axios.get<SingleFoodListingResponse>(
      `${FOOD_LISTINGS_API_URL}/FoodListing/${id}`
    );
    return response.data.FoodListing;
  } catch (error) {
    console.error(`Error fetching food listing with ID ${id}:`, error);
    throw error;
  }
};
