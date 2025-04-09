import { useState, useEffect, useRef } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  ShoppingBag,
  Clock,
  Package,
  ArrowRight,
  Calendar,
  MapPin,
  Edit,
  CheckCircle,
} from "lucide-react";
import axios from "axios";
import { format } from "date-fns";
import { useAppSelector } from "@/redux/hooks";
import { toast } from "sonner";
import * as API from "@/config/api";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import websocketService, { WS_EVENTS } from "@/services/websocketService";
import ChangeLocationModal from "@/components/ChangeLocationModal";

// Order status mapping for UI display
const orderStatusMap = {
  pending: { label: "Pending", color: "bg-yellow-500" },
  assigned: { label: "Assigned", color: "bg-blue-500" },
  preparing: { label: "Preparing", color: "bg-purple-500" },
  delivering: { label: "Out for Delivery", color: "bg-indigo-500" },
  completed: { label: "Delivered", color: "bg-green-500" },
  cancelled: { label: "Cancelled", color: "bg-red-500" },
};

// UI badge component for order status
function OrderStatusBadge({ status }: { status: string }) {
  const statusInfo = orderStatusMap[status as keyof typeof orderStatusMap] || {
    label: status,
    color: "bg-gray-500",
  };

  return (
    <Badge className={`${statusInfo.color} text-white`}>
      {statusInfo.label}
    </Badge>
  );
}

export default function OrdersPage() {
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [completedOrdersCount, setCompletedOrdersCount] = useState(0); // Track number of completed orders
  const { user, isAuthenticated } = useAppSelector((state) => state.auth);
  const navigate = useNavigate();
  const [selectedOrderForLocation, setSelectedOrderForLocation] = useState<{
    id: string;
    location: string;
  } | null>(null);

  // Add refs to track registered orders and prevent duplicate registrations
  const registeredOrdersRef = useRef<Set<string>>(new Set());
  // Track whether event handlers are registered
  const eventHandlersRegisteredRef = useRef(false);

  // Function to fetch orders - extracted so we can call it after updates
  const fetchOrders = async () => {
    if (!user?.id) return;

    try {
      setLoading(true);
      const response = await axios.get(
        `${API.CUSTOMER_URL}/customers/${user.id}/orders`
      );

      // Filter out completed orders and count them
      const activeOrders = response.data.filter(
        (order: any) => order.order_status !== "completed"
      );
      const completedOrders = response.data.filter(
        (order: any) => order.order_status === "completed"
      );
      setCompletedOrdersCount(completedOrders.length);

      // Sort orders by date (newest first)
      const sortedOrders = activeOrders.sort((a: any, b: any) => {
        return (
          new Date(b.order_start).getTime() - new Date(a.order_start).getTime()
        );
      });

      setOrders(sortedOrders);
    } catch (error) {
      console.error("Error fetching orders:", error);
      toast.error("Failed to load orders", {
        description: "Please try again later",
      });
    } finally {
      setLoading(false);
    }
  };

  // Connect to WebSocket and setup event handlers - run once
  useEffect(() => {
    // Redirect to login if not authenticated
    if (!isAuthenticated) {
      navigate("/login", { state: { from: "/orders" } });
      return;
    }

    if (!user?.id || eventHandlersRegisteredRef.current) return;

    // Connect to WebSocket
    websocketService.connect();

    // Listen for order assignments (when a picker accepts an order)
    const handleOrderTaken = (data: any) => {
      console.log("Order taken event received:", data);

      if (data.order_id) {
        // Refresh the orders list without checking current state
        fetchOrders();

        // Notify the customer
        toast.success("Order update!", {
          description: `Your order #${data.order_id.substring(
            0,
            8
          )} has been accepted by a picker.`,
          action: {
            label: "View",
            onClick: () => navigate(`/orders/${data.order_id}`),
          },
        });
      }
    };

    // Listen for status updates (preparing, delivering, completed)
    const handlePickerUpdate = (data: any) => {
      console.log("Picker update event received:", data);

      // Check if this update is for the current customer
      if (data.customer_id === user.id) {
        // Refresh the orders list
        fetchOrders();

        // Get the readable status label
        const statusLabel =
          orderStatusMap[data.status as keyof typeof orderStatusMap]?.label ||
          data.status;

        // Notify the customer
        toast.info("Order status updated!", {
          description: `Your order #${data.order_id.substring(
            0,
            8
          )} is now ${statusLabel.toLowerCase()}.`,
          action: {
            label: "View",
            onClick: () => navigate(`/orders/${data.order_id}`),
          },
        });
      }
    };

    // Register for WebSocket events
    websocketService.on(WS_EVENTS.ORDER_TAKEN, handleOrderTaken);
    websocketService.on(WS_EVENTS.PICKER_UPDATE, handlePickerUpdate);

    // Set flag to prevent duplicate registrations
    eventHandlersRegisteredRef.current = true;

    // Initial data fetch
    fetchOrders();

    // Cleanup function
    return () => {
      websocketService.off(WS_EVENTS.ORDER_TAKEN, handleOrderTaken);
      websocketService.off(WS_EVENTS.PICKER_UPDATE, handlePickerUpdate);
      eventHandlersRegisteredRef.current = false;
    };
  }, [user?.id, isAuthenticated, navigate]);

  // Register new orders for WebSocket updates when orders list changes
  useEffect(() => {
    if (!user?.id || orders.length === 0) return;

    // Only register for orders we haven't registered for yet
    const newOrders = orders.filter(
      (order) => !registeredOrdersRef.current.has(order.id)
    );

    if (newOrders.length > 0) {
      console.log(
        `Registering ${newOrders.length} new orders for WebSocket updates`
      );

      newOrders.forEach((order) => {
        websocketService.registerForOrderUpdates(user.id, order.id);
        registeredOrdersRef.current.add(order.id);
      });
    }
  }, [orders, user?.id]);

  // Calculate total cost of an order
  const calculateTotal = (items: any[]) => {
    return items.reduce(
      (sum, item) => sum + item.order_price * item.order_quantity,
      0
    );
  };

  // Format date string
  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return format(date, "PPP 'at' p"); // e.g., "Apr 29, 2023 at 2:30 PM"
    } catch (error) {
      return dateString;
    }
  };

  // Handle location update
  const handleLocationUpdated = (newLocation: string) => {
    if (selectedOrderForLocation) {
      // Update the order in the local state
      setOrders(
        orders.map((order) =>
          order.id === selectedOrderForLocation.id
            ? { ...order, order_location: newLocation }
            : order
        )
      );

      toast.success("Delivery location updated successfully");
      setSelectedOrderForLocation(null);
    }
  };

  // Check if order can have its location edited
  const canEditLocation = (status: string) => {
    return ["pending", "assigned", "preparing"].includes(status);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h1 className="text-3xl font-bold">Active Orders</h1>
          <p className="text-muted-foreground mt-1">
            View and track your current orders
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {completedOrdersCount > 0 && (
            <Link to="/orders/completed">
              <Button variant="secondary" className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4" />
                Completed Orders
                {completedOrdersCount > 0 && (
                  <span className="ml-1 bg-secondary-foreground text-secondary rounded-full w-5 h-5 flex items-center justify-center text-xs">
                    {completedOrdersCount}
                  </span>
                )}
              </Button>
            </Link>
          )}
          <Link to="/">
            <Button variant="outline">Continue Shopping</Button>
          </Link>
        </div>
      </div>

      {loading ? (
        // Loading state
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="w-full">
              <CardHeader>
                <div className="flex justify-between">
                  <Skeleton className="h-8 w-48" />
                  <Skeleton className="h-6 w-24" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-4 w-1/2" />
                </div>
              </CardContent>
              <CardFooter>
                <Skeleton className="h-10 w-full" />
              </CardFooter>
            </Card>
          ))}
        </div>
      ) : orders.length === 0 ? (
        // No orders state
        <div className="text-center py-12">
          <ShoppingBag className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h2 className="text-2xl font-semibold mb-4">No active orders</h2>
          <div className="space-y-4">
            <p className="text-muted-foreground">
              You don't have any active orders at the moment.
            </p>
            {completedOrdersCount > 0 ? (
              <div className="flex flex-col items-center gap-4">
                <Link to="/orders/completed">
                  <Button>View Completed Orders</Button>
                </Link>
                <span className="text-muted-foreground">or</span>
              </div>
            ) : null}
            <Link to="/">
              <Button
                variant={completedOrdersCount > 0 ? "outline" : "default"}
              >
                Explore Restaurants
              </Button>
            </Link>
          </div>
        </div>
      ) : (
        // Orders list
        <div className="space-y-6">
          {orders.map((order) => (
            <Card key={order.id} className="overflow-hidden">
              <CardHeader className="pb-2">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                  <div>
                    <CardTitle className="text-lg flex items-center gap-2">
                      Order #{order.id.substring(0, 8)}
                      <OrderStatusBadge status={order.order_status} />
                    </CardTitle>
                    <div className="flex items-center text-sm text-muted-foreground mt-1">
                      <Calendar className="h-4 w-4 mr-1" />
                      {formatDate(order.order_start)}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold">
                      {order.order_items.length} item
                      {order.order_items.length !== 1 ? "s" : ""}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Total: ${calculateTotal(order.order_items).toFixed(2)}
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pb-2">
                {/* Order Items Summary */}
                <div className="space-y-2">
                  <div className="flex items-center text-sm">
                    <Package className="h-4 w-4 mr-1 text-muted-foreground" />
                    <span className="font-medium">Items:</span>
                  </div>
                  <ul className="pl-6 space-y-1">
                    {order.order_items
                      .slice(0, 3)
                      .map((item: any, index: number) => (
                        <li key={index} className="text-sm">
                          {item.order_quantity}x {item.order_item} - $
                          {(item.order_price * item.order_quantity).toFixed(2)}
                        </li>
                      ))}
                    {order.order_items.length > 3 && (
                      <li className="text-sm text-muted-foreground">
                        +{order.order_items.length - 3} more items
                      </li>
                    )}
                  </ul>
                </div>
                <Separator className="my-4" />
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center">
                      <MapPin className="h-4 w-4 mr-1 text-muted-foreground" />
                      <span className="font-medium">Delivery Address:</span>
                    </div>
                    {canEditLocation(order.order_status) && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 px-2 text-xs"
                        onClick={() =>
                          setSelectedOrderForLocation({
                            id: order.id,
                            location: order.order_location,
                          })
                        }
                      >
                        <Edit className="h-3 w-3 mr-1" />
                        Edit
                      </Button>
                    )}
                  </div>
                  <p className="text-sm pl-6">{order.order_location}</p>
                </div>
              </CardContent>
              <CardFooter className="pt-2">
                <Button
                  variant="outline"
                  className="w-full flex items-center justify-center"
                  onClick={() => navigate(`/orders/${order.id}`)}
                >
                  View Details
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      {/* Location Change Modal */}
      {selectedOrderForLocation && (
        <ChangeLocationModal
          isOpen={!!selectedOrderForLocation}
          onClose={() => setSelectedOrderForLocation(null)}
          currentLocation={selectedOrderForLocation.location}
          orderId={selectedOrderForLocation.id}
          onLocationUpdated={handleLocationUpdated}
        />
      )}
    </div>
  );
}
