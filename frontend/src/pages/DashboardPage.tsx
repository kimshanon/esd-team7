"use client";

import { useState } from "react";
import { Link } from "react-router-dom";
import {
  Bell,
  ChevronDown,
  LogOut,
  Menu,
  Package,
  Search,
  Settings,
  User,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

// Sample delivery options data
const deliveryOptions = [
  {
    id: 1,
    name: "Standard Delivery",
    description: "Delivery within 3-5 business days",
    price: "$5.99",
    icon: "🚚",
  },
  {
    id: 2,
    name: "Express Delivery",
    description: "Delivery within 1-2 business days",
    price: "$9.99",
    icon: "⚡",
  },
  {
    id: 3,
    name: "Same Day Delivery",
    description: "Delivery within 24 hours",
    price: "$14.99",
    icon: "🔥",
  },
  {
    id: 4,
    name: "International Shipping",
    description: "Delivery within 7-14 business days",
    price: "$24.99",
    icon: "🌎",
  },
];

// Sample active deliveries
const activeDeliveries = [
  {
    id: "DEL-1234",
    status: "In Transit",
    from: "123 Main St, New York, NY",
    to: "456 Oak St, Boston, MA",
    estimatedDelivery: "Today, 5:30 PM",
  },
  {
    id: "DEL-5678",
    status: "Processing",
    from: "789 Pine St, Chicago, IL",
    to: "101 Maple St, Detroit, MI",
    estimatedDelivery: "Tomorrow, 10:00 AM",
  },
];

export default function DashboardPage() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b bg-background px-4 md:px-6">
        <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
          <SheetTrigger asChild>
            <Button variant="outline" size="icon" className="md:hidden">
              <Menu className="h-5 w-5" />
              <span className="sr-only">Toggle menu</span>
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-72">
            <nav className="grid gap-6 text-lg font-medium">
              <Link
                to="/dashboard"
                className="flex items-center gap-2 text-lg font-semibold"
                onClick={() => setMobileMenuOpen(false)}
              >
                <Package className="h-6 w-6" />
                <span className="font-bold">DeliverEase</span>
              </Link>
              <Link
                to="/dashboard"
                className="flex items-center gap-2"
                onClick={() => setMobileMenuOpen(false)}
              >
                Dashboard
              </Link>
              <Link
                to="#"
                className="flex items-center gap-2"
                onClick={() => setMobileMenuOpen(false)}
              >
                My Deliveries
              </Link>
              <Link
                to="#"
                className="flex items-center gap-2"
                onClick={() => setMobileMenuOpen(false)}
              >
                New Delivery
              </Link>
              <Link
                to="#"
                className="flex items-center gap-2"
                onClick={() => setMobileMenuOpen(false)}
              >
                Settings
              </Link>
            </nav>
          </SheetContent>
        </Sheet>
        <div className="flex items-center gap-2">
          <Link
            to="/dashboard"
            className="flex items-center gap-2 font-semibold"
          >
            <Package className="h-6 w-6" />
            <span className="hidden md:inline-block">DeliverEase</span>
          </Link>
        </div>
        <div className="flex-1">
          <form>
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search deliveries..."
                className="w-full appearance-none bg-background pl-8 shadow-none md:w-2/3 lg:w-1/3"
              />
            </div>
          </form>
        </div>
        <div className="flex items-center gap-4">
          <Button variant="outline" size="icon" className="relative h-8 w-8">
            <Bell className="h-4 w-4" />
            <span className="sr-only">Notifications</span>
            <span className="absolute right-1 top-1 flex h-2 w-2 rounded-full bg-primary"></span>
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="gap-1">
                <User className="h-4 w-4" />
                <span className="hidden md:inline-block">John Doe</span>
                <ChevronDown className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>My Account</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                <User className="mr-2 h-4 w-4" />
                Profile
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Settings className="mr-2 h-4 w-4" />
                Settings
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                <LogOut className="mr-2 h-4 w-4" />
                Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>
      <div className="grid flex-1 md:grid-cols-[220px_1fr] lg:grid-cols-[280px_1fr]">
        <aside className="hidden border-r bg-muted/40 md:block">
          <nav className="grid gap-2 p-4 text-sm">
            <Link
              to="/dashboard"
              className="flex items-center gap-3 rounded-lg bg-primary px-3 py-2 text-primary-foreground transition-all hover:text-primary-foreground"
            >
              <Package className="h-4 w-4" />
              Dashboard
            </Link>
            <Link
              to="#"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:bg-muted hover:text-foreground"
            >
              <Package className="h-4 w-4" />
              My Deliveries
            </Link>
            <Link
              to="#"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:bg-muted hover:text-foreground"
            >
              <Package className="h-4 w-4" />
              New Delivery
            </Link>
            <Link
              to="#"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:bg-muted hover:text-foreground"
            >
              <Settings className="h-4 w-4" />
              Settings
            </Link>
          </nav>
        </aside>
        <main className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-8">
          <div className="flex items-center gap-4">
            <h1 className="text-lg font-semibold md:text-2xl">Dashboard</h1>
          </div>
          <Tabs defaultValue="overview" className="space-y-4">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="deliveries">Active Deliveries</TabsTrigger>
              <TabsTrigger value="options">Delivery Options</TabsTrigger>
            </TabsList>
            <TabsContent value="overview" className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Total Deliveries
                    </CardTitle>
                    <Package className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">12</div>
                    <p className="text-xs text-muted-foreground">
                      +2 from last month
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Active Deliveries
                    </CardTitle>
                    <Package className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">2</div>
                    <p className="text-xs text-muted-foreground">
                      Currently in transit
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Completed
                    </CardTitle>
                    <Package className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">10</div>
                    <p className="text-xs text-muted-foreground">
                      Successfully delivered
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Total Spent
                    </CardTitle>
                    <Package className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">$429.99</div>
                    <p className="text-xs text-muted-foreground">
                      +$89.99 from last month
                    </p>
                  </CardContent>
                </Card>
              </div>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                <Card className="col-span-4">
                  <CardHeader>
                    <CardTitle>Recent Activity</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex items-center gap-4">
                        <div className="rounded-full bg-primary/10 p-2">
                          <Package className="h-4 w-4 text-primary" />
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-medium">
                            Package DEL-1234 is out for delivery
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Today, 2:30 PM
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="rounded-full bg-primary/10 p-2">
                          <Package className="h-4 w-4 text-primary" />
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-medium">
                            Package DEL-5678 has been processed
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Today, 10:15 AM
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="rounded-full bg-primary/10 p-2">
                          <Package className="h-4 w-4 text-primary" />
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-medium">
                            Package DEL-9012 has been delivered
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Yesterday, 4:45 PM
                          </p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                <Card className="col-span-3">
                  <CardHeader>
                    <CardTitle>Quick Actions</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <Button className="w-full justify-start gap-2">
                      <Package className="h-4 w-4" />
                      Create New Delivery
                    </Button>
                    <Button
                      className="w-full justify-start gap-2"
                      variant="outline"
                    >
                      <Search className="h-4 w-4" />
                      Track a Package
                    </Button>
                    <Button
                      className="w-full justify-start gap-2"
                      variant="outline"
                    >
                      <Settings className="h-4 w-4" />
                      Manage Preferences
                    </Button>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
            <TabsContent value="deliveries" className="space-y-4">
              <div className="grid gap-4">
                {activeDeliveries.map((delivery) => (
                  <Card key={delivery.id}>
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base">
                          Delivery #{delivery.id}
                        </CardTitle>
                        <div className="rounded-full bg-primary/10 px-2 py-1 text-xs font-medium text-primary">
                          {delivery.status}
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="pb-2">
                      <div className="grid gap-2">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <p className="text-xs text-muted-foreground">
                              From
                            </p>
                            <p className="text-sm font-medium">
                              {delivery.from}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-muted-foreground">To</p>
                            <p className="text-sm font-medium">{delivery.to}</p>
                          </div>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">
                            Estimated Delivery
                          </p>
                          <p className="text-sm font-medium">
                            {delivery.estimatedDelivery}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                    <CardFooter>
                      <Button variant="outline" size="sm" className="w-full">
                        Track Package
                      </Button>
                    </CardFooter>
                  </Card>
                ))}
              </div>
            </TabsContent>
            <TabsContent value="options" className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-2">
                {deliveryOptions.map((option) => (
                  <Card key={option.id}>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <span className="text-2xl">{option.icon}</span>
                        {option.name}
                      </CardTitle>
                      <CardDescription>{option.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <p className="text-2xl font-bold">{option.price}</p>
                    </CardContent>
                    <CardFooter>
                      <Button className="w-full">Select</Button>
                    </CardFooter>
                  </Card>
                ))}
              </div>
            </TabsContent>
          </Tabs>
        </main>
      </div>
    </div>
  );
}
