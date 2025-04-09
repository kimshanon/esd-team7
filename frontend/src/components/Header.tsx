"use client";

import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Menu, ShoppingCart, User, LogOut } from "lucide-react";
import { toast } from "sonner";
import { signOut } from "firebase/auth";
import { auth } from "@/config/firebase";

import { Button } from "./ui/button";
import { Sheet, SheetContent, SheetTrigger } from "./ui/sheet";
import { useCart } from "@/contexts/CartContext";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useAppSelector, useAppDispatch } from "@/redux/hooks";
import { logout } from "@/redux/authSlice";

export default function Header() {
  const location = useLocation();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { cart } = useCart();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  // Get user from Redux store
  const { user, isAuthenticated } = useAppSelector((state) => state.auth);

  const routes = [
    { href: "/", label: "Home" },
    { href: "/special", label: "Deals" },
    { href: "/orders", label: "My Orders" },
    { href: "/orders/completed", label: "Completed Order" },
  ];

  const isActive = (path: string) => location.pathname === path;

  const handleLogout = async () => {
    try {
      // Sign out from Firebase
      await signOut(auth);

      // Dispatch Redux logout action
      dispatch(logout());

      toast.success("Logged out successfully");

      navigate("/");
    } catch (error) {
      console.error("Logout error:", error);
      toast.error("Failed to log out");
    }
  };

  // Get initials for avatar
  const getInitials = (name: string) => {
    return name ? name.charAt(0).toUpperCase() : "U";
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between mx-auto">
        <div className="flex items-center gap-8">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-2xl">🍔</span>
            <span className="font-bold text-xl">SMOOeats</span>
          </Link>

          <nav className="hidden md:flex gap-6">
            {routes.map((route) => (
              <Link
                key={route.href}
                to={route.href}
                className={`text-sm font-medium transition-colors hover:text-primary ${
                  isActive(route.href)
                    ? "text-foreground"
                    : "text-muted-foreground"
                }`}
              >
                {route.label}
              </Link>
            ))}
          </nav>
        </div>

        <div className="flex items-center gap-4">
          <Link to="/cart">
            <Button variant="outline" size="icon" className="relative">
              <ShoppingCart className="h-5 w-5" />
              {cart.length > 0 && (
                <span className="absolute -top-2 -right-2 bg-primary text-primary-foreground text-xs rounded-full h-5 w-5 flex items-center justify-center">
                  {cart.length}
                </span>
              )}
            </Button>
          </Link>

          {isAuthenticated && user ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="flex items-center gap-2">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback>
                      {getInitials(user.username)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="hidden md:block text-left">
                    <p className="text-sm font-medium">{user.username}</p>
                    <p className="text-xs text-muted-foreground capitalize">
                      {user.userType}
                    </p>
                  </div>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel>My Account</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => navigate("/profile")}>
                  <User className="mr-2 h-4 w-4" />
                  <Link to="/profile" className="hover:text-gray-600">
                    Profile
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleLogout}>
                  <LogOut className="mr-2 h-4 w-4" />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Button onClick={() => navigate("/login")}>Login</Button>
          )}

          <Sheet open={isMenuOpen} onOpenChange={setIsMenuOpen}>
            <SheetTrigger asChild className="md:hidden">
              <Button variant="outline" size="icon">
                <Menu className="h-5 w-5" />
                <span className="sr-only">Toggle menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent side="left">
              <div className="flex flex-col gap-6 py-6">
                <Link
                  to="/"
                  className="flex items-center gap-2"
                  onClick={() => setIsMenuOpen(false)}
                >
                  <span className="text-2xl">🍔</span>
                  <span className="font-bold text-xl">SMOOeats</span>
                </Link>
                <nav className="flex flex-col gap-4">
                  {routes.map((route) => (
                    <Link
                      key={route.href}
                      to={route.href}
                      className={`text-sm font-medium transition-colors hover:text-primary ${
                        isActive(route.href)
                          ? "text-foreground"
                          : "text-muted-foreground"
                      }`}
                      onClick={() => setIsMenuOpen(false)}
                    >
                      {route.label}
                    </Link>
                  ))}

                  {!isAuthenticated && (
                    <>
                      <Link
                        to="/login"
                        className="text-sm font-medium transition-colors hover:text-primary"
                        onClick={() => setIsMenuOpen(false)}
                      >
                        Login
                      </Link>
                      <Link
                        to="/register"
                        className="text-sm font-medium transition-colors hover:text-primary"
                        onClick={() => setIsMenuOpen(false)}
                      >
                        Register
                      </Link>
                    </>
                  )}

                  {isAuthenticated && (
                    <Button variant="outline" onClick={handleLogout}>
                      Log out
                    </Button>
                  )}
                </nav>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
