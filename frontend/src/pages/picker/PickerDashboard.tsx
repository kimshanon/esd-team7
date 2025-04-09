import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import axios from "axios";
import { format } from "date-fns";
import { Bike, Clock, MapPin, Package, DollarSign, Store } from "lucide-react";

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
import websocketService, { WS_EVENTS } from "@/services/websocketService";
import { fetchPickerOrders } from "@/services/api";
import RouteMap from "@/components/RouteMap";

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
            <Store className="h-4 w-4 text-muted-foreground mt-0.5" />
            <div>
              <p className="text-sm font-medium">Pickup Location</p>
              <p className="text-sm text-muted-foreground">
                {order.stall_name}
              </p>
              <p className="text-sm text-muted-foreground">
                {order.stall_location}
              </p>
            </div>
          </div>

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
  onCancelOrder,
}: {
  order: any;
  onUpdateStatus: (status: string) => void;
  onCancelOrder: () => void;
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
              <Store className="h-4 w-4 text-muted-foreground mt-0.5" />
              <div>
                <p className="text-sm font-medium">Pickup Location</p>
                <p className="text-sm font-medium">{order.stall_name}</p>
                <p className="text-sm">{order.stall_location}</p>
              </div>
            </div>

            <Separator />

            <div className="flex items-start gap-2">
              <MapPin className="h-4 w-4 text-muted-foreground mt-0.5" />
              <div>
                <p className="text-sm font-medium">Delivery Location</p>
                <p className="text-sm">{order.order_location}</p>
              </div>
            </div>

            <Separator />

            {/* Add the route map */}
            <RouteMap
              startLocation={order.stall_location}
              endLocation={order.order_location}
            />

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
        <CardFooter className="flex flex-col sm:flex-row gap-2">
          {/* Show Cancel button only when in "assigned" status */}
          {order.order_status === "assigned" && (
            <Button
              variant="destructive"
              className="w-full sm:w-auto order-2 sm:order-1"
              onClick={onCancelOrder}
            >
              Cancel Assignment
            </Button>
          )}

          {/* Only show the update button if we have a next status */}
          {steps[currentStep].nextStatus && (
            <Button
              className="w-full sm:flex-1 order-1 sm:order-2"
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

// In the main PickerDashboard component, add the cancel handler
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

        // Fetch stall information for each pending order
        const ordersWithStallInfo = await Promise.all(
          pendingOrders.map(async (order: any) => {
            try {
              const stallResponse = await axios.get(
                `https://personal-dcwqxa6n.outsystemscloud.com/SMUlivery/rest/FoodStallAPI/GetAllStalls`
              );
              // console.log('Order:', { id: order.id, stall_id: order.stall_id, type: typeof order.stall_id });
              // console.log('Raw API Response:', JSON.stringify(stallResponse.data, null, 2));
              // console.log('FoodStalls array:', JSON.stringify(stallResponse.data.FoodStalls, null, 2));
              // Find the stall in the response that matches our stall_id
              const stall = stallResponse.data.FoodStalls.find((s: any) => {
                return Number(s.stall_id) === Number(order.stall_id);
              });
              if (!stall) throw new Error(`Stall ${order.stall_id} not found`);
              return {
                ...order,
                stall_name: stall.stall_name,
                stall_location: stall.stall_location,
              };
            } catch (error) {
              console.error(`Error fetching stall info for order ${order.id}:`, error);
              return order;
            }
          })
        );

        setAvailableOrders(ordersWithStallInfo);

        // 2. Fetch active and completed orders using fetchPickerOrders
        const pickerOrders = await fetchPickerOrders(user.id);
        
        const activeOrders = pickerOrders.filter((order: any) =>
          ["assigned", "preparing", "delivering"].includes(order.order_status)
        );

        setActiveOrder(activeOrders.length > 0 ? activeOrders[0] : null);

        // 3. Filter completed orders
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

    // Connect to WebSocket service
    websocketService.connect();

    // Register as picker to receive order notifications
    if (user?.id) {
      websocketService.registerAsPicker(user.id);
    }

    // Listen for new available orders
    const handleNewOrder = (orderData: any) => {
      console.log("New order received:", orderData);

      // Check if this order is already in our list - use a function that doesn't depend on state
      setAvailableOrders((prev) => {
        // Only add if not already in the list
        if (!prev.some((order) => order.id === orderData.order_id)) {
          // Show a notification
          toast.info("New order available!", {
            description: `Order #${orderData.order_id.substring(
              0,
              8
            )} is waiting for pickup`,
            action: {
              label: "View",
              onClick: () => setActiveTab("available"),
            },
          });

          // Validate that the order has all required fields before adding to the list
          const orderToAdd = orderData.details || {};

          // Make sure the order has order_items array to prevent the reduce error
          if (!orderToAdd.order_items) {
            console.warn(
              "Order is missing order_items array, fetching complete order details"
            );

            // If order_items is missing, fetch the complete order data
            axios
              .get(`http://127.0.0.1:5003/orders/${orderData.order_id}`)
              .then(async (response) => {
                // Fetch stall information
                const order = response.data;
                try {
                  const stallResponse = await axios.get(
                    `https://personal-dcwqxa6n.outsystemscloud.com/SMUlivery/rest/FoodStallAPI/GetAllStalls`
                  );
                  console.log('Order stall_id:', order.stall_id);
                  console.log('Available stalls:', stallResponse.data.FoodStalls.map((s: any) => ({ id: s.stall_id, name: s.stall_name })));
                  // Find the stall in the response that matches our stall_id
                  const stall = stallResponse.data.FoodStalls.find(
                    (s: any) => Number(s.id) === Number(order.stall_id)
                  );
                  if (!stall) throw new Error(`Stall ${order.stall_id} not found`);
                  const orderWithStall = {
                    ...order,
                    stall_name: stall.stall_name,
                    stall_location: stall.stall_location,
                  };
                  setAvailableOrders((prevOrders) => [
                    orderWithStall,
                    ...prevOrders,
                  ]);
                } catch (error) {
                  console.error(`Error fetching stall info for new order ${order.id}:`, error);
                  setAvailableOrders((prevOrders) => [
                    order,
                    ...prevOrders,
                  ]);
                }
              })
              .catch((error) => {
                console.error("Error fetching complete order:", error);
              });

            // Return unchanged for now, the axios call will update state when it completes
            return prev;
          }

          // Only add if the order has order_items property
          return [orderToAdd, ...prev];
        }
        return prev;
      });
    };

    // Listen for orders that have been taken by other pickers
    const handleOrderTaken = (data: any) => {
      console.log("Order taken:", data);

      // Remove the taken order from available orders
      setAvailableOrders((prev) =>
        prev.filter((order) => order.id !== data.order_id)
      );

      // If this picker took the order, update the active order
      if (data.picker_id === user?.id) {
        // Fetch the updated order details
        axios
          .get(`http://127.0.0.1:5003/orders/${data.order_id}`)
          .then((response) => {
            setActiveOrder(response.data);
            setActiveTab("active");
          })
          .catch((err) => console.error("Error fetching accepted order:", err));
      } else {
        // If another picker took it, just notify
        toast.info(
          `Order #${data.order_id.substring(
            0,
            8
          )} was accepted by another picker`
        );
      }
    };

    // Register event handlers
    websocketService.on(WS_EVENTS.ORDER_WAITING, handleNewOrder);
    websocketService.on(WS_EVENTS.ORDER_TAKEN, handleOrderTaken);

    // Test WebSocket connection
    websocketService.testConnection();

    // Cleanup
    return () => {
      websocketService.off(WS_EVENTS.ORDER_WAITING, handleNewOrder);
      websocketService.off(WS_EVENTS.ORDER_TAKEN, handleOrderTaken);
    };
  }, [user, navigate]);

  const handleAcceptOrder = async (orderId: string) => {
    try {
      // First, check if the picker already has an active order
      if (activeOrder) {
        toast.error("You already have an active order");
        return;
      }

      // Update the order in the backend
      await axios.post("http://127.0.0.1:5005/picker_accept", {
        order_id: orderId,
        picker_id: user?.id,
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
      // Update order status via the composite service instead of directly
      await axios.post("http://127.0.0.1:5005/order_status", {
        order_id: activeOrder.id,
        status: newStatus,
      });

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

  // Add a new function to handle cancellation
  const handleCancelOrder = async () => {
    if (!activeOrder) return;

    try {
      // Call the API to update the order status back to "pending" and remove picker assignment
      const response = await axios.post("http://127.0.0.1:5005/order_cancel", {
        order_id: activeOrder.id,
        picker_id: user?.id,
      });

      toast.success("Order assignment cancelled", {
        description: "The order is now available for other pickers",
      });

      // Set the active order to null
      setActiveOrder(null);

      // Refresh available orders after a short delay to allow the backend to update
      setTimeout(() => {
        axios
          .get("http://127.0.0.1:5003/orders")
          .then((response) => {
            const pendingOrders = response.data.filter(
              (order: any) =>
                order.order_status === "pending" && !order.picker_id
            );
            setAvailableOrders(pendingOrders);
            // Switch to available tab
            setActiveTab("available");
          })
          .catch((error) =>
            console.error("Error refreshing available orders:", error)
          );
      }, 1000);
    } catch (error) {
      console.error("Error cancelling order:", error);
      toast.error("Failed to cancel order assignment");
    }
  };

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
            onCancelOrder={handleCancelOrder}
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
