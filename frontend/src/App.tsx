import { useEffect } from "react";
import { Routes, Route, useNavigate, useLocation } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/Register";
import Layout from "./components/Layout";
import RestaurantsPage from "./pages/RestaurantsPage";
import RestaurantDetailPage from "./pages/RestaurantDetailPage";
import CartPage from "./pages/CartPage";
import OrdersPage from "./pages/OrdersPage";
import CompletedOrdersPage from "./pages/CompletedOrdersPage";
import OrderTrackingPage from "./pages/OrderTrackingPage";
import NotFoundPage from "./pages/NotFoundPage";
import SpecialFoodListingsPage from "./pages/SpecialFoodListingsPage";
import { ProtectedRoute } from "./components/ProtectedRoute";
import PickerLayout from "./components/PickerLayout";
import PickerDashboard from "./pages/picker/PickerDashboard";
import { useAppSelector } from "./redux/hooks";
import ProfilePage from "./pages/ProfilePage";

function App() {
  const { user, isAuthenticated } = useAppSelector((state) => state.auth);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // Check if user is a picker and redirect if needed
    if (
      isAuthenticated &&
      user?.userType === "picker" &&
      !location.pathname.startsWith("/picker") &&
      location.pathname !== "/login" &&
      location.pathname !== "/register"
    ) {
      navigate("/picker/dashboard");
    }
  }, [isAuthenticated, user, location.pathname, navigate]);

  // If user is a picker, show picker routes
  if (isAuthenticated && user?.userType === "picker") {
    return (
      <Routes>
        <Route path="/*" element={<PickerLayout />}>
          <Route index element={<PickerDashboard />} />
          <Route path="picker/dashboard" element={<PickerDashboard />} />
          <Route path="picker/active-order" element={<PickerDashboard />} />
          <Route path="picker/history" element={<PickerDashboard />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    );
  }

  // Otherwise show regular customer routes (including auth routes with customer Layout)
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        {/* Auth routes now use the same Layout as customer routes */}
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />

        {/* Regular customer routes */}
        <Route index element={<RestaurantsPage />} />
        <Route path="restaurants/:id" element={<RestaurantDetailPage />} />
        <Route path="special" element={<SpecialFoodListingsPage />} />
        <Route
          path="cart"
          element={
            <ProtectedRoute>
              <CartPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="orders"
          element={
            <ProtectedRoute>
              <OrdersPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="orders/completed"
          element={
            <ProtectedRoute>
              <CompletedOrdersPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="orders/:orderId"
          element={
            <ProtectedRoute>
              <OrderTrackingPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="profile"
          element={
            <ProtectedRoute>
              <ProfilePage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

export default App;
