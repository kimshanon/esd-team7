import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter as Router } from "react-router-dom";
import { Provider } from "react-redux";
import { Toaster } from "sonner";
import { store } from "./redux/store";
import { ThemeProvider } from "./components/ThemeProvider";
import { CartProvider } from "./contexts/CartContext";
import { AuthProvider } from "./contexts/AuthProvider";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Provider store={store}>
      <Router>
        <ThemeProvider defaultTheme="system" storageKey="food-delivery-theme">
          <AuthProvider>
            <CartProvider>
              <App />
              <Toaster position="bottom-right" />
            </CartProvider>
          </AuthProvider>
        </ThemeProvider>
      </Router>
    </Provider>
  </React.StrictMode>
);
