// Backend data types
export interface Stall {
  stall_id: number;
  stall_name: string;
  stall_description: string;
  stall_rating: number;
  review_count: number;
  preparation_time_mins: number;
  delivery_fee: number;
  stall_location: string;
  is_promoted: boolean;
  stall_image?: string; // Optional since not all stalls have images
}

export interface MenuItem {
  menu_item_id: number;
  food_name: string;
  food_price: number;
  food_description: string;
  food_category: string;
  stall_id: number;
  food_image: string;
}

// Frontend mapped types (for compatibility with existing components)
export interface Restaurant {
  id: string;
  name: string;
  image: string;
  description: string;
  rating: number;
  reviewCount: number;
  cuisines: string[];
  deliveryTime: number;
  deliveryFee: number;
  location: string;
  isPromoted: boolean;
  menu: MenuItemFrontend[];
}

export interface MenuItemFrontend {
  id: string;
  name: string;
  price: number;
  description: string;
  category: string;
  image: string;
}

export interface FoodListing {
  Id: number;
  RestaurantEmail: string;
  RestaurantName: string;
  Title: string;
  Qty?: number;
  FoodType: string;
  Price: number;
  PickupAddress: string;
  ExpiryTime: string;
  CreatedTime: string;
  ImageText?: string;
}

export interface FoodListingsResponse {
  Result: {
    Success: boolean;
  };
  FoodListings: FoodListing[];
}

export interface SingleFoodListingResponse {
  Result: {
    Success: boolean;
  };
  FoodListing: FoodListing;
}
