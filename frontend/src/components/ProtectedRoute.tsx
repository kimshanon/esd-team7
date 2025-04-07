import { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAppSelector } from "@/redux/hooks";

interface ProtectedRouteProps {
  children: ReactNode;
  requiredUserType?: "customer" | "picker";
}

export function ProtectedRoute({
  children,
  requiredUserType,
}: ProtectedRouteProps) {
  const { isAuthenticated, user } = useAppSelector((state) => state.auth);
  const location = useLocation();

  if (!isAuthenticated) {
    // Redirect to login if not authenticated
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requiredUserType && user?.userType !== requiredUserType) {
    // Redirect to home if user type doesn't match required type
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
