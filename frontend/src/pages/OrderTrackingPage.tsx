import { useState, useEffect, useCallback } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Package,
  MapPin,
  Clock,
  CheckCircle2,
  Calendar,
  User,
  Edit,
  Store,
  Navigation,
} from "lucide-react";
import axios from "axios";
import { format } from "date-fns";
import { toast } from "sonner";

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
import { useAppSelector } from "@/redux/hooks";

import websocketService, { WS_EVENTS } from "@/services/websocketService";
import ChangeLocationModal from "@/components/ChangeLocationModal"
import { fetchOrderById, fetchRouteInfo } from "@/services/api";
import RouteMap from "@/components/RouteMap";

const orderStatusSteps = [
  { key: "pending", label: "Order Received", icon: Package },
  { key: "assigned", label: "Assigned to Picker", icon: User },
  { key: "preparing", label: "Preparing", icon: Package },
  { key: "delivering", label: "Out for Delivery", icon: Package },
  { key: "completed", label: "Delivered", icon: CheckCircle2 },
]

function OrderStatusTimeline({ currentStatus }: { currentStatus: string }) {
  // Find the index of the current status in the steps
  const currentIndex = orderStatusSteps.findIndex((step) => step.key === currentStatus)

  return (
    <div className="mt-6 mb-8">
      <div className="relative flex justify-between">
        {orderStatusSteps.map((step, index) => {
          const isActive = index <= currentIndex && currentStatus !== "cancelled"
          const StepIcon = step.icon

          return (
            <div key={step.key} className="flex flex-col items-center">
              <div
                className={`rounded-full p-2 ${
                  isActive ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                }`}
              >
                <StepIcon className="h-5 w-5" />
              </div>
              <span
                className={`text-xs mt-1 text-center max-w-[80px] ${
                  isActive ? "text-foreground font-medium" : "text-muted-foreground"
                }`}
              >
                {step.label}
              </span>
            </div>
          )
        })}

        {/* Connecting line */}
        <div className="absolute top-4 left-0 right-0 h-[2px] bg-muted -z-10">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{
              width: `${
                currentStatus === "cancelled" ? 0 : Math.min((currentIndex / (orderStatusSteps.length - 1)) * 100, 100)
              }%`,
            }}
          />
        </div>
      </div>
    </div>
  )
}

export default function OrderTrackingPage() {
  const { orderId } = useParams<{ orderId: string }>();
  const navigate = useNavigate();
  const { user } = useAppSelector((state) => state.auth);
  const [order, setOrder] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [pickerInfo, setPickerInfo] = useState<{ picker_name?: string } | null>(
    null
  );
  const [isLocationModalOpen, setIsLocationModalOpen] = useState(false);
  const [routeInfo, setRouteInfo] = useState<{
    distance: number;
    duration: number;
    polyline: string;
  } | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [newLocation, setNewLocation] = useState("");

  // Create a fetchOrderDetails function that can be reused
  const fetchOrderDetails = useCallback(async () => {
    if (!orderId) return;

    try {
      setLoading(true);
      const order = await fetchOrderById(orderId);
      setOrder(order);

      // If order has a picker, fetch picker details
      if (order.picker_id) {
        try {
          const pickerResponse = await axios.get(
            `http://127.0.0.1:5001/pickers/${order.picker_id}`
          );
          setPickerInfo(pickerResponse.data);
        } catch (err) {
          console.error("Couldn't load picker details", err);
        }
      }
    } catch (error) {
      console.error("Error fetching order details:", error);
      toast.error("Failed to load order details", {
        description: "Please try again later",
      });
    } finally {
      setLoading(false);
    }
  }, [orderId]);

  // Add new function to fetch route information
  const fetchRouteDetails = useCallback(async () => {
    if (!order?.stall_location || !order?.order_location) return;

    try {
      const route = await fetchRouteInfo(order.stall_location, order.order_location);
      setRouteInfo(route);
    } catch (error) {
      console.error("Error fetching route information:", error);
      toast.error("Failed to load route information", {
        description: "Please try again later",
      });
    }
  }, [order?.stall_location, order?.order_location]);

  useEffect(() => {
    fetchOrderDetails();

    // Connect to WebSocket for real-time updates if we have an order ID and user
    if (orderId && user?.id) {
      // Connect to WebSocket
      websocketService.connect();

      // Register to get updates for this specific order
      websocketService.registerForOrderUpdates(user.id, orderId);

      // Handle when a picker accepts the order
      const handleOrderTaken = (data: any) => {
        if (data.order_id === orderId) {
          console.log("Order taken update received", data);
          // Refresh order details to get picker info
          fetchOrderDetails();

          // Show notification
          toast.success("Your order has been accepted!", {
            description:
              "A picker has accepted your order and will prepare it soon.",
          });
        }
      };

      // Listen for status updates
      const handlePickerUpdate = (data: any) => {
        console.log("Picker update received", data);

        if (data.order_id === orderId) {
          // Refresh order details to get the latest status
          fetchOrderDetails();

          // Special notification for orders returned to pending
          if (data.status === "pending" && order?.order_status !== "pending") {
            toast.info("Order returned to pending", {
              description: "Your order will be assigned to a new picker soon.",
            });
          } else {
            // Regular status update notification
            const statusStep = orderStatusSteps.find(
              (step) => step.key === data.status
            );
            const statusLabel = statusStep ? statusStep.label : data.status;

            toast.info("Order status updated!", {
              description: `Your order is now ${statusLabel.toLowerCase()}.`,
            });
          }
        }
      };

      // Register event handlers
      websocketService.on(WS_EVENTS.ORDER_TAKEN, handleOrderTaken);
      websocketService.on(WS_EVENTS.PICKER_UPDATE, handlePickerUpdate);

      // Cleanup
      return () => {
        websocketService.off(WS_EVENTS.ORDER_TAKEN, handleOrderTaken);
        websocketService.off(WS_EVENTS.PICKER_UPDATE, handlePickerUpdate);
      };
    }
  }, [orderId, user?.id, fetchOrderDetails]);

  // Update useEffect to fetch route information when order changes
  useEffect(() => {
    if (order && user?.role === "picker") {
      const fetchRoute = async () => {
        try {
          const route = await fetchRouteInfo(
            order.stall_location,
            order.order_location
          );
          setRouteInfo(route);
        } catch (error) {
          console.error("Error fetching route:", error);
        }
      };
      fetchRoute();
    }
  }, [order, user?.role]);

  // Calculate total cost
  const calculateTotal = (items: any[]) => {
    return items.reduce((sum, item) => sum + item.order_price * item.order_quantity, 0)
  }

  // Format date
  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), "PPP 'at' p")
    } catch (error) {
      return dateString
    }
  }

  // Check if order can have its location edited
  const canEditLocation = (status: string) => {
    return ["pending", "assigned", "preparing"].includes(status)
  }

  const handleLocationUpdated = (newLocation: string) => {
    if (order) {
      setOrder({
        ...order,
        order_location: newLocation,
      })
      toast.success("Delivery location updated successfully")
    }
  }

  // Add helper function to format distance and duration
  const formatDistance = (meters: number) => {
    if (meters < 1000) {
      return `${Math.round(meters)}m`;
    }
    return `${(meters / 1000).toFixed(1)}km`;
  };

  const formatDuration = (seconds: number) => {
    const minutes = Math.ceil(seconds / 60);
    if (minutes < 60) {
      return `${minutes} min`;
    }
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${hours}h ${remainingMinutes}min`;
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center mb-6">
          <Link to="/orders" className="flex items-center text-muted-foreground hover:text-foreground">
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Orders
          </Link>
        </div>
        <Skeleton className="h-8 w-64 mb-6" />
        <Skeleton className="h-48 w-full mb-6" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (!order) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center mb-6">
          <Link to="/orders" className="flex items-center text-muted-foreground hover:text-foreground">
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Orders
          </Link>
        </div>
        <div className="text-center py-12">
          <h2 className="text-2xl font-semibold mb-4">Order not found</h2>
          <p className="text-muted-foreground mb-8">We couldn't find the order you're looking for.</p>
          <Link to="/orders">
            <Button>View All Orders</Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center mb-6">
        <Link to="/orders" className="flex items-center text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Orders
        </Link>
      </div>

      <div className="flex flex-col md:flex-row justify-between items-start mb-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">Order #{orderId?.substring(0, 8)}</h1>
          <div className="flex items-center text-sm text-muted-foreground">
            <Calendar className="h-4 w-4 mr-1" />
            {formatDate(order.order_start)}

            {order.order_status === "cancelled" && (
              <Badge variant="destructive" className="ml-2">
                Cancelled
              </Badge>
            )}
          </div>
        </div>
        <div className="mt-4 md:mt-0">
          <Badge className="text-base py-1.5 px-4" variant={order.is_paid ? "default" : "outline"}>
            {order.is_paid ? "Paid" : "Payment Pending"}
          </Badge>
        </div>
      </div>

      {order.order_status !== "cancelled" && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Order Status</CardTitle>
          </CardHeader>
          <CardContent>
            <OrderStatusTimeline currentStatus={order.order_status} />
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Order Items</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="divide-y">
                {order.order_items.map((item: any, index: number) => (
                  <li key={index} className="py-3 flex justify-between">
                    <div>
                      <span className="font-medium">{item.order_quantity}x </span>
                      {item.order_item}
                    </div>
                    <div className="font-medium">${(item.order_price * item.order_quantity).toFixed(2)}</div>
                  </li>
                ))}
              </ul>
              <Separator className="my-4" />
              <div className="flex justify-between font-medium">
                <span>Total</span>
                <span>${calculateTotal(order.order_items).toFixed(2)}</span>
              </div>
            </CardContent>
          </Card>
        </div>

        <div>
          <Card>
            <CardHeader>
              <CardTitle className="flex justify-between items-center">
                <span>Delivery Details</span>
                {canEditLocation(order.order_status) && (
                  <Button variant="outline" size="sm" className="h-8" onClick={() => setIsLocationModalOpen(true)}>
                    <Edit className="h-3.5 w-3.5 mr-1" />
                    Edit
                  </Button>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="flex items-center text-sm text-muted-foreground mb-1">
                  <Store className="h-4 w-4 mr-1" />
                  Pickup Location
                </div>
                <p className="text-sm font-medium">{order.stall_name}</p>
                <p className="text-sm">{order.stall_location}</p>
              </div>

              <Separator />

              <div>
                <div className="flex items-center text-sm text-muted-foreground mb-1">
                  <MapPin className="h-4 w-4 mr-1" />
                  Delivery Address
                </div>
                <p>{order.order_location}</p>
              </div>

              {/* Only show route information for pickers */}
              {user?.role === "picker" && routeInfo && (
                <div>
                  <div className="flex items-center text-sm text-muted-foreground mb-1">
                    <Navigation className="h-4 w-4 mr-1" />
                    Route Information
                  </div>
                  <div className="grid grid-cols-2 gap-2 mb-4">
                    <div>
                      <p className="text-sm font-medium">Distance</p>
                      <p className="text-sm">{formatDistance(routeInfo.distance)}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium">Estimated Time</p>
                      <p className="text-sm">{formatDuration(routeInfo.duration)}</p>
                    </div>
                  </div>
                  <RouteMap
                    startLocation={order.stall_location}
                    endLocation={order.order_location}
                    polyline={routeInfo.polyline}
                  />
                </div>
              )}

              {order.picker_id && (
                <div>
                  <div className="flex items-center text-sm text-muted-foreground mb-1">
                    <User className="h-4 w-4 mr-1" />
                    Assigned Picker
                  </div>
                  <p>
                    {pickerInfo?.picker_name ||
                      "Picker #" + order.picker_id.substring(0, 6)}
                  </p>
                </div>
              )}

              {order.order_completed && (
                <div>
                  <div className="flex items-center text-sm text-muted-foreground mb-1">
                    <Clock className="h-4 w-4 mr-1" />
                    Delivered On
                  </div>
                  <p>{formatDate(order.order_completed)}</p>
                </div>
              )}
            </CardContent>
            <CardFooter>
              <Button variant="outline" className="w-full">
                Contact Support
              </Button>
            </CardFooter>
          </Card>
        </div>
      </div>

      {/* Location Change Modal */}
      <ChangeLocationModal
        isOpen={isLocationModalOpen}
        onClose={() => setIsLocationModalOpen(false)}
        currentLocation={order.order_location}
        orderId={orderId || ""}
        onLocationUpdated={handleLocationUpdated}
      />

      {/* Only show route information for pickers */}
      {user?.role === "picker" && routeInfo && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Delivery Route</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">Distance</p>
                  <p className="text-sm text-muted-foreground">
                    {(routeInfo.distance / 1000).toFixed(1)} km
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">Estimated Time</p>
                  <p className="text-sm text-muted-foreground">
                    {Math.ceil(routeInfo.duration / 60)} minutes
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
