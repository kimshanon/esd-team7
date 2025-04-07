import { Routes, Route } from "react-router-dom";
import PickerLayout from "./PickerLayout";
import PickerDashboard from "@/pages/picker/PickerDashboard";
import NotFoundPage from "@/pages/NotFoundPage";
import { ProtectedRoute } from "./ProtectedRoute";

export default function PickerRoutes() {
  return (
    <Routes>
      <Route
        path="/*" // This catches all paths and passes them to nested routes
        element={
          <ProtectedRoute requiredUserType="picker">
            <PickerLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<PickerDashboard />} />
        <Route path="picker/dashboard" element={<PickerDashboard />} />
        <Route path="picker/active-order" element={<PickerDashboard />} />
        <Route path="picker/history" element={<PickerDashboard />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
