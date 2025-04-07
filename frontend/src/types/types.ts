// Backend data types
export interface Stall {
  id: string;
  stall_name: string;
  stall_image: string;
  stall_description: string;
  rating: number;
  review_count: number;
  cuisines: string[];
  preparation_time_mins: number;
  delivery_fee: number;
  stall_location: string;
  is_promoted: boolean;
  menu: MenuItem[];
}

export interface MenuItem {
  id: string;
  food_name: string;
  food_price: number;
  food_description: string;
  food_category: string;
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
