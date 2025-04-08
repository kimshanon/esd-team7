import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { MenuItemFrontend } from "@/types/types";

interface CartItem extends MenuItemFrontend {
  quantity: number;
  restaurantId: string; // Add restaurant ID to track which restaurant the item belongs to
}

interface CartContextType {
  cart: CartItem[];
  addToCart: (item: MenuItemFrontend, restaurantId: string) => void;
  removeFromCart: (itemId: string) => void;
  updateQuantity: (itemId: string, quantity: number) => void;
  clearCart: () => void;
  getCartItemCount: () => number;
  getCartTotal: () => number;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export function CartProvider({ children }: { children: ReactNode }) {
  const [cart, setCart] = useState<CartItem[]>(() => {
    // Load cart from localStorage on initialization
    const savedCart = localStorage.getItem("cart");
    return savedCart ? JSON.parse(savedCart) : [];
  });

  // Save cart to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem("cart", JSON.stringify(cart));
  }, [cart]);

  const addToCart = (item: MenuItemFrontend, restaurantId: string) => {
    setCart((prevCart) => {
      // Check if adding from a different restaurant
      const firstItemRestaurantId =
        prevCart.length > 0 ? prevCart[0].restaurantId : null;

      if (firstItemRestaurantId && firstItemRestaurantId !== restaurantId) {
        // Ask user to confirm clearing cart
        const confirmed = window.confirm(
          "Your cart contains items from another restaurant. Would you like to clear your cart and add this item instead?"
        );

        if (confirmed) {
          // Clear cart and add new item
          return [{ ...item, quantity: 1, restaurantId }];
        } else {
          // Keep the cart as is
          return prevCart;
        }
      }

      // Check if the item is already in the cart
      const existingItemIndex = prevCart.findIndex(
        (cartItem) => cartItem.id === item.id
      );

      if (existingItemIndex >= 0) {
        // Item exists, update quantity
        const updatedCart = [...prevCart];
        updatedCart[existingItemIndex].quantity += 1;
        return updatedCart;
      } else {
        // Item does not exist, add new item with quantity 1
        return [...prevCart, { ...item, quantity: 1, restaurantId }];
      }
    });
  };

  const removeFromCart = (itemId: string) => {
    setCart((prevCart) => prevCart.filter((item) => item.id !== itemId));
  };

  const updateQuantity = (itemId: string, quantity: number) => {
    if (quantity <= 0) {
      removeFromCart(itemId);
      return;
    }

    setCart((prevCart) =>
      prevCart.map((item) =>
        item.id === itemId ? { ...item, quantity } : item
      )
    );
  };

  const clearCart = () => {
    setCart([]);
  };

  const getCartItemCount = () => {
    return cart.reduce((count, item) => count + item.quantity, 0);
  };

  const getCartTotal = () => {
    return cart.reduce((total, item) => total + item.price * item.quantity, 0);
  };

  return (
    <CartContext.Provider
      value={{
        cart,
        addToCart,
        removeFromCart,
        updateQuantity,
        clearCart,
        getCartItemCount,
        getCartTotal,
      }}
    >
      {children}
    </CartContext.Provider>
  );
}

export const useCart = () => {
  const context = useContext(CartContext);
  if (context === undefined) {
    throw new Error("useCart must be used within a CartProvider");
  }
  return context;
};
