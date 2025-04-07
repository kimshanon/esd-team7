import { createSlice, PayloadAction } from "@reduxjs/toolkit";

// Define the user type
export interface User {
  id: string;
  username: string;
  email: string;
  userType: "customer" | "picker";
}

// Define the authentication state
interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
}

// Get user from localStorage if available
const getUserFromStorage = (): User | null => {
  const userString = localStorage.getItem("user");
  if (userString) {
    try {
      return JSON.parse(userString);
    } catch (error) {
      console.error("Error parsing user from localStorage:", error);
      return null;
    }
  }
  return null;
};

// Initialize the state with user from localStorage
const initialState: AuthState = {
  user: getUserFromStorage(),
  isAuthenticated: !!getUserFromStorage(),
};

// Create the auth slice
const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    setUser: (state, action: PayloadAction<User>) => {
      state.user = action.payload;
      state.isAuthenticated = true;
      // Also save to localStorage for persistence
      localStorage.setItem("user", JSON.stringify(action.payload));
    },
    logout: (state) => {
      state.user = null;
      state.isAuthenticated = false;
      // Remove from localStorage
      localStorage.removeItem("user");
    },
  },
});

export const { setUser, logout } = authSlice.actions;
export default authSlice.reducer;
