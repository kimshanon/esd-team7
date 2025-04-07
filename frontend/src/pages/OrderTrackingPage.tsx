import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import {
  ArrowLeft,
  Package,
  MapPin,
  Clock,
  CheckCircle2,
  Calendar,
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

const orderStatusSteps = [
  { key: "pending", label: "Order Received", icon: Package },
  { key: "assigned", label: "Assigned to Picker", icon: Package },
  { key: "preparing", label: "Preparing", icon: Package },
  { key: "delivering", label: "Out for Delivery", icon: Package },
  { key: "completed", label: "Delivered", icon: CheckCircle2 },
];

function OrderStatusTimeline({ currentStatus }: { currentStatus: string }) {
  // Find the index of the current status in the steps
  const currentIndex = orderStatusSteps.findIndex(
    (step) => step.key === currentStatus
  );

  return (
    <div className="mt-6 mb-8">
      <div className="relative flex justify-between">
        {orderStatusSteps.map((step, index) => {
          const isActive =
            index <= currentIndex && currentStatus !== "cancelled";
          const StepIcon = step.icon;

          return (
            <div key={step.key} className="flex flex-col items-center">
              <div
                className={`rounded-full p-2 ${
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                <StepIcon className="h-5 w-5" />
              </div>
              <span
                className={`text-xs mt-1 text-center max-w-[80px] ${
                  isActive
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
        <div className="absolute top-4 left-0 right-0 h-[2px] bg-muted -z-10">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{
              width: `${
                currentStatus === "cancelled"
                  ? 0
                  : Math.min(
                      (currentIndex / (orderStatusSteps.length - 1)) * 100,
                      100
                    )
              }%`,
            }}
          />
        </div>
      </div>
    </div>
  );
}

export default function OrderTrackingPage() {
  const { orderId } = useParams<{ orderId: string }>();
  const [order, setOrder] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchOrderDetails() {
      try {
        setLoading(true);
        const response = await axios.get(
          `http://127.0.0.1:5003/orders/${orderId}`
        );
        setOrder(response.data);
      } catch (error) {
        console.error("Error fetching order details:", error);
        toast.error("Failed to load order details", {
          description: "Please try again later",
        });
      } finally {
        setLoading(false);
      }
    }

    if (orderId) {
      fetchOrderDetails();
    }
  }, [orderId]);

  // Calculate total cost
  const calculateTotal = (items: any[]) => {
    return items.reduce(
      (sum, item) => sum + item.order_price * item.order_quantity,
      0
    );
  };

  // Format date
  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), "PPP 'at' p");
    } catch (error) {
      return dateString;
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center mb-6">
          <Link
            to="/orders"
            className="flex items-center text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Orders
          </Link>
        </div>
        <Skeleton className="h-8 w-64 mb-6" />
        <Skeleton className="h-48 w-full mb-6" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!order) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center mb-6">
          <Link
            to="/orders"
            className="flex items-center text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Orders
          </Link>
        </div>
        <div className="text-center py-12">
          <h2 className="text-2xl font-semibold mb-4">Order not found</h2>
          <p className="text-muted-foreground mb-8">
            We couldn't find the order you're looking for.
          </p>
          <Link to="/orders">
            <Button>View All Orders</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center mb-6">
        <Link
          to="/orders"
          className="flex items-center text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Orders
        </Link>
      </div>

      <div className="flex flex-col md:flex-row justify-between items-start mb-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">
            Order #{orderId?.substring(0, 8)}
          </h1>
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
          <Badge
            className="text-base py-1.5 px-4"
            variant={order.is_paid ? "default" : "outline"}
          >
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
                      <span className="font-medium">
                        {item.order_quantity}x{" "}
                      </span>
                      {item.order_item}
                    </div>
                    <div className="font-medium">
                      ${(item.order_price * item.order_quantity).toFixed(2)}
                    </div>
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
              <CardTitle>Delivery Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="flex items-center text-sm text-muted-foreground mb-1">
                  <MapPin className="h-4 w-4 mr-1" />
                  Delivery Address
                </div>
                <p>{order.order_location}</p>
              </div>

              {order.picker_id && (
                <div>
                  <div className="flex items-center text-sm text-muted-foreground mb-1">
                    <Package className="h-4 w-4 mr-1" />
                    Assigned Picker
                  </div>
                  <p>Picker ID: {order.picker_id}</p>
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
    </div>
  );
}
