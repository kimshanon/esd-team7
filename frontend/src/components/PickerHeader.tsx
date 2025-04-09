import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Menu, LogOut, User, Bike } from "lucide-react";
import { signOut } from "firebase/auth";
import { toast } from "sonner";
import * as API from "@/config/api";

import { Button } from "./ui/button";
import { Sheet, SheetContent, SheetTrigger } from "./ui/sheet";
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
import { auth } from "@/config/firebase";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import axios from "axios";

export default function PickerHeader() {
  const location = useLocation();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { user } = useAppSelector((state) => state.auth);
  const [isAvailable, setIsAvailable] = useState(true);

  // Routes specialized for pickers
  const routes = [
    { href: "/picker/dashboard", label: "Dashboard" },
    // { href: "/picker/active-order", label: "Active Order" },
    // { href: "/picker/history", label: "History" },
  ];

  const isActive = (path: string) => location.pathname === path;

  const handleLogout = async () => {
    try {
      await signOut(auth);
      dispatch(logout());
      toast.success("Logged out successfully");
      navigate("/login");
    } catch (error) {
      console.error("Logout error:", error);
      toast.error("Failed to log out");
    }
  };

  const handleAvailabilityChange = async (checked: boolean) => {
    try {
      setIsAvailable(checked);
      // Update availability in the backend
      await axios.patch(
        `${API.PICKER_URL}/pickers/${user?.id}/availability`,
        {
          is_available: checked,
        }
      );

      toast.success(
        `You are now ${checked ? "available" : "unavailable"} for deliveries`
      );
    } catch (error) {
      console.error("Failed to update availability:", error);
      toast.error("Failed to update availability");
      // Revert UI state on error
      setIsAvailable(!checked);
    }
  };

  const getInitials = (name: string) => {
    return name ? name.charAt(0).toUpperCase() : "P";
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between mx-auto">
        <div className="flex items-center gap-8">
          <Link to="/picker/dashboard" className="flex items-center gap-2">
            <span className="text-2xl">🚲</span>
            <span className="font-bold text-xl">Picker Portal</span>
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
          {/* Availability toggle */}
          <div className="hidden md:flex items-center space-x-2">
            <Switch
              id="availability-mode"
              checked={isAvailable}
              onCheckedChange={handleAvailabilityChange}
            />
            <Label htmlFor="availability-mode" className="text-sm">
              {isAvailable ? "Available" : "Unavailable"}
            </Label>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="flex items-center gap-2">
                <Avatar className="h-8 w-8">
                  <AvatarFallback>
                    {user?.username ? getInitials(user.username) : "P"}
                  </AvatarFallback>
                </Avatar>
                <div className="hidden md:block text-left">
                  <p className="text-sm font-medium">{user?.username}</p>
                  <p className="text-xs text-muted-foreground capitalize">
                    Picker
                  </p>
                </div>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>My Account</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => navigate("/picker/profile")}>
                <User className="mr-2 h-4 w-4" />
                Profile
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

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
                  to="/picker/dashboard"
                  className="flex items-center gap-2"
                  onClick={() => setIsMenuOpen(false)}
                >
                  <span className="text-2xl">🚲</span>
                  <span className="font-bold text-xl">Picker Portal</span>
                </Link>

                <div className="flex items-center space-x-2 px-2">
                  <Switch
                    id="mobile-availability"
                    checked={isAvailable}
                    onCheckedChange={handleAvailabilityChange}
                  />
                  <Label htmlFor="mobile-availability">
                    {isAvailable ? "Available" : "Unavailable"}
                  </Label>
                </div>

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
                  <Button variant="outline" onClick={handleLogout}>
                    <LogOut className="mr-2 h-4 w-4" />
                    Log out
                  </Button>
                </nav>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
