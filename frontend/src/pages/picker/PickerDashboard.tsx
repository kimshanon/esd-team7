import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import axios from "axios";
import { format } from "date-fns";
import { Bike, Clock, MapPin, Package, DollarSign } from "lucide-react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useAppSelector } from "@/redux/hooks";
import { Skeleton } from "@/components/ui/skeleton";

// Helper function to format currency
const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(amount);
};

// Helper function to format date
const formatDate = (dateString: string) => {
  try {
    return format(new Date(dateString), "PPP 'at' p");
  } catch (error) {
    return dateString;
  }
};

// Order card component for available orders
const AvailableOrderCard = ({
  order,
  onAccept,
}: {
  order: any;
  onAccept: () => void;
}) => {
  const calculateTotal = (items: any[]) => {
    return items.reduce(
      (sum, item) => sum + item.order_price * item.order_quantity,
      0
    );
  };

  const total = calculateTotal(order.order_items);
  const estimatedEarnings = (total * 0.15).toFixed(2); // Example: 15% of order total

  return (
    <Card className="mb-4">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <CardTitle className="text-lg">
            Order #{order.id.substring(0, 8)}
          </CardTitle>
          <Badge>New Order</Badge>
        </div>
        <div className="text-sm text-muted-foreground">
          {formatDate(order.order_start)}
        </div>
      </CardHeader>
      <CardContent className="pb-2">
        <div className="space-y-4">
          <div className="flex items-start gap-2">
            <MapPin className="h-4 w-4 text-muted-foreground mt-0.5" />
            <div>
              <p className="text-sm font-medium">Delivery Location</p>
              <p className="text-sm text-muted-foreground">
                {order.order_location}
              </p>
            </div>
          </div>

          <div className="flex items-start gap-2">
            <Package className="h-4 w-4 text-muted-foreground mt-0.5" />
            <div>
              <p className="text-sm font-medium">
                {order.order_items.length} Items
              </p>
              <ul className="text-sm text-muted-foreground">
                {order.order_items
                  .slice(0, 2)
                  .map((item: any, index: number) => (
                    <li key={index}>
                      {item.order_quantity}x {item.order_item}
                    </li>
                  ))}
                {order.order_items.length > 2 && (
                  <li>+{order.order_items.length - 2} more items</li>
                )}
              </ul>
            </div>
          </div>

          <div className="flex items-start gap-2">
            <DollarSign className="h-4 w-4 text-muted-foreground mt-0.5" />
            <div>
              <p className="text-sm font-medium">Estimated Earnings</p>
              <p className="text-sm text-muted-foreground">
                ${estimatedEarnings}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
      <CardFooter>
        <Button onClick={onAccept} className="w-full">
          Accept Order
        </Button>
      </CardFooter>
    </Card>
  );
};

// Active order component
const ActiveOrderView = ({
  order,
  onUpdateStatus,
}: {
  order: any;
  onUpdateStatus: (status: string) => void;
}) => {
  if (!order) {
    return (
      <div className="text-center py-12">
        <Package className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
        <h2 className="text-xl font-medium mb-2">No active orders</h2>
        <p className="text-muted-foreground">
          You don't have any active deliveries. Check the available orders tab
          to accept a new delivery.
        </p>
      </div>
    );
  }

  // Determine the current step based on order status
  const statusToStep: Record<string, number> = {
    assigned: 0,
    preparing: 1,
    delivering: 2,
    completed: 3,
  };

  const currentStep = statusToStep[order.order_status] || 0;

  // Define steps and their corresponding next statuses
  const steps = [
    {
      label: "Assigned",
      description: "You've been assigned to this order",
      icon: Bike,
      nextStatus: "preparing",
    },
    {
      label: "Preparing",
      description: "Food is being prepared",
      icon: Clock,
      nextStatus: "delivering",
    },
    {
      label: "Out for Delivery",
      description: "You're on your way to deliver",
      icon: Package,
      nextStatus: "completed",
    },
    {
      label: "Delivered",
      description: "Order has been delivered",
      icon: Package,
      nextStatus: null,
    },
  ];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle className="text-lg">
              Order #{order.id.substring(0, 8)}
            </CardTitle>
            <Badge variant="outline" className="font-normal">
              {steps[currentStep].label}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            {formatDate(order.order_start)}
          </p>
        </CardHeader>
        <CardContent>
          {/* Progress steps */}
          <div className="mb-6 relative">
            <div className="relative flex items-center justify-between">
              {steps.map((step, index) => {
                const StepIcon = step.icon;
                const isCompleted = index <= currentStep;

                return (
                  <div key={index} className="flex flex-col items-center">
                    <div
                      className={`z-10 flex items-center justify-center w-10 h-10 rounded-full ${
                        isCompleted
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      <StepIcon className="w-5 h-5" />
                    </div>
                    <span
                      className={`mt-2 text-xs text-center max-w-[80px] ${
                        isCompleted
                          ? "text-foreground font-medium"
                          : "text-muted-foreground"
                      }`}
                    >
                      {step.label}
                    </span>
                  </div>
                );
              })}

              {/* Connecting line */}
              <div className="absolute top-5 left-0 right-0 h-[2px] bg-muted -z-0">
                <div
                  className="h-full bg-primary transition-all duration-300"
                  style={{
                    width: `${(currentStep / (steps.length - 1)) * 100}%`,
                  }}
                />
              </div>
            </div>
          </div>

          <div className="grid gap-4">
            <div className="flex items-start gap-2">
              <MapPin className="h-4 w-4 text-muted-foreground mt-0.5" />
              <div>
                <p className="text-sm font-medium">Delivery Location</p>
                <p className="text-sm">{order.order_location}</p>
              </div>
            </div>

            <Separator />

            <div>
              <h3 className="text-sm font-medium mb-2">Order Items</h3>
              <ul className="space-y-1">
                {order.order_items.map((item: any, index: number) => (
                  <li key={index} className="text-sm">
                    {item.order_quantity}x {item.order_item} - $
                    {(item.order_price * item.order_quantity).toFixed(2)}
                  </li>
                ))}
              </ul>
            </div>

            <Separator />

            <div className="flex items-start gap-2">
              <Clock className="h-4 w-4 text-muted-foreground mt-0.5" />
              <div>
                <p className="text-sm font-medium">Time Elapsed</p>
                <p className="text-sm">
                  {format(new Date(order.order_start), "'Started' p")}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
        <CardFooter>
          {/* Only show the update button if we have a next status */}
          {steps[currentStep].nextStatus && (
            <Button
              className="w-full"
              onClick={() => onUpdateStatus(steps[currentStep].nextStatus!)}
            >
              Mark as {steps[currentStep + 1].label}
            </Button>
          )}
        </CardFooter>
      </Card>
    </div>
  );
};

// History order card
const CompletedOrderCard = ({ order }: { order: any }) => {
  const calculateTotal = (items: any[]) => {
    return items.reduce(
      (sum, item) => sum + item.order_price * item.order_quantity,
      0
    );
  };

  const total = calculateTotal(order.order_items);
  const earnings = (total * 0.15).toFixed(2); // Example earning calculation

  return (
    <Card className="mb-4">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <CardTitle className="text-sm md:text-base">
            Order #{order.id.substring(0, 8)}
          </CardTitle>
          <Badge
            variant={
              order.order_status === "completed" ? "default" : "destructive"
            }
          >
            {order.order_status === "completed" ? "Completed" : "Cancelled"}
          </Badge>
        </div>
        <p className="text-xs text-muted-foreground">
          {formatDate(order.order_start)}
          {order.order_completed && ` - ${formatDate(order.order_completed)}`}
        </p>
      </CardHeader>
      <CardContent className="pb-2">
        <div className="flex justify-between items-center text-sm">
          <div className="flex flex-col">
            <span className="text-muted-foreground">Delivery to</span>
            <span className="truncate max-w-[200px]">
              {order.order_location}
            </span>
          </div>
          <div className="text-right">
            <span className="text-muted-foreground">Your earnings</span>
            <p className="font-medium">${earnings}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default function PickerDashboard() {
  const navigate = useNavigate();
  const { user } = useAppSelector((state) => state.auth);
  const [activeTab, setActiveTab] = useState("available");
  const [availableOrders, setAvailableOrders] = useState<any[]>([]);
  const [activeOrder, setActiveOrder] = useState<any>(null);
  const [completedOrders, setCompletedOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      navigate("/login");
      return;
    }

    const fetchData = async () => {
      setLoading(true);
      try {
        // 1. Fetch available orders (orders with status "pending")
        const pendingResponse = await axios.get("http://127.0.0.1:5003/orders");
        const pendingOrders = pendingResponse.data.filter(
          (order: any) => order.order_status === "pending" && !order.picker_id
        );
        setAvailableOrders(pendingOrders);

        // 2. Fetch active order (orders assigned to this picker that are not completed/cancelled)
        const pickerOrdersResponse = await axios.get(
          `http://127.0.0.1:5003/pickers/${user.id}/orders`
        );
        const pickerOrders = pickerOrdersResponse.data;

        const activeOrders = pickerOrders.filter((order: any) =>
          ["assigned", "preparing", "delivering"].includes(order.order_status)
        );

        setActiveOrder(activeOrders.length > 0 ? activeOrders[0] : null);

        // 3. Fetch completed orders
        const completedOrders = pickerOrders.filter((order: any) =>
          ["completed", "cancelled"].includes(order.order_status)
        );
        setCompletedOrders(completedOrders);
      } catch (error) {
        console.error("Error fetching picker data:", error);
        toast.error("Failed to load picker data");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    // Set up a periodic refresh (every 30 seconds)
    const intervalId = setInterval(fetchData, 30000);

    return () => clearInterval(intervalId);
  }, [user, navigate]);

  const handleAcceptOrder = async (orderId: string) => {
    try {
      // First, check if the picker already has an active order
      if (activeOrder) {
        toast.error("You already have an active order");
        return;
      }

      // Update the order in the backend
      await axios.put(`http://127.0.0.1:5003/orders/${orderId}`, {
        picker_id: user?.id,
        order_status: "assigned",
      });

      // Fetch the updated order
      const response = await axios.get(
        `http://127.0.0.1:5003/orders/${orderId}`
      );

      // Update local state
      setActiveOrder(response.data);
      setAvailableOrders((prevOrders) =>
        prevOrders.filter((order) => order.id !== orderId)
      );

      // Switch to active order tab
      setActiveTab("active");

      toast.success("Order accepted successfully!");
    } catch (error) {
      console.error("Error accepting order:", error);
      toast.error("Failed to accept order");
    }
  };

  const handleUpdateOrderStatus = async (newStatus: string) => {
    if (!activeOrder) return;

    try {
      // Update order status in the backend
      await axios.patch(
        `http://127.0.0.1:5003/orders/${activeOrder.id}/status`,
        {
          order_status: newStatus,
        }
      );

      // Fetch the updated order
      const response = await axios.get(
        `http://127.0.0.1:5003/orders/${activeOrder.id}`
      );
      const updatedOrder = response.data;

      // Update local state
      if (newStatus === "completed") {
        setActiveOrder(null);
        setCompletedOrders((prev) => [updatedOrder, ...prev]);
        toast.success("Order marked as delivered!");
      } else {
        setActiveOrder(updatedOrder);
        toast.success(`Order status updated to ${newStatus}`);
      }
    } catch (error) {
      console.error("Error updating order status:", error);
      toast.error("Failed to update order status");
    }
  };

  // Calculate total earnings from completed orders
  const calculateTotalEarnings = () => {
    return completedOrders.reduce((total, order) => {
      const orderTotal = order.order_items.reduce(
        (sum: number, item: any) =>
          sum + item.order_price * item.order_quantity,
        0
      );
      return total + orderTotal * 0.15; // Assuming 15% commission
    }, 0);
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-6">Picker Dashboard</h1>
        <div className="space-y-4">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">Picker Dashboard</h1>
          <p className="text-muted-foreground">
            Manage your deliveries and track earnings
          </p>
        </div>

        <div className="mt-4 md:mt-0 p-4 bg-muted/30 rounded-lg">
          <h2 className="text-sm font-medium text-muted-foreground">
            Total Earnings
          </h2>
          <p className="text-2xl font-bold">
            {formatCurrency(calculateTotalEarnings())}
          </p>
        </div>
      </div>

      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="space-y-6"
      >
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="available" className="relative">
            Available Orders
            {availableOrders.length > 0 && (
              <span className="absolute top-0 right-1 transform -translate-y-1/2 bg-primary text-xs font-medium text-primary-foreground rounded-full w-5 h-5 flex items-center justify-center">
                {availableOrders.length}
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="active">
            Active Order
            {activeOrder && (
              <span className="ml-2 inline-block w-2 h-2 bg-green-500 rounded-full"></span>
            )}
          </TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        <TabsContent value="available" className="space-y-4">
          {availableOrders.length === 0 ? (
            <div className="text-center py-12">
              <Package className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h2 className="text-xl font-medium mb-2">No available orders</h2>
              <p className="text-muted-foreground">
                There are no orders available at the moment.
                <br />
                Check back later for new delivery opportunities.
              </p>
            </div>
          ) : (
            availableOrders.map((order) => (
              <AvailableOrderCard
                key={order.id}
                order={order}
                onAccept={() => handleAcceptOrder(order.id)}
              />
            ))
          )}
        </TabsContent>

        <TabsContent value="active">
          <ActiveOrderView
            order={activeOrder}
            onUpdateStatus={handleUpdateOrderStatus}
          />
        </TabsContent>

        <TabsContent value="history">
          {completedOrders.length === 0 ? (
            <div className="text-center py-12">
              <Package className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h2 className="text-xl font-medium mb-2">No completed orders</h2>
              <p className="text-muted-foreground">
                You haven't completed any deliveries yet.
                <br />
                Completed orders will appear here.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Completed Orders</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">
                      {
                        completedOrders.filter(
                          (o) => o.order_status === "completed"
                        ).length
                      }
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Total Earnings</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">
                      {formatCurrency(calculateTotalEarnings())}
                    </div>
                  </CardContent>
                </Card>
              </div>

              <h3 className="text-lg font-medium mt-6 mb-4">Order History</h3>
              <div className="space-y-4">
                {completedOrders.map((order) => (
                  <CompletedOrderCard key={order.id} order={order} />
                ))}
              </div>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
