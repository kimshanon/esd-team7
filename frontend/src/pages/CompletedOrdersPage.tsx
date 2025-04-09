import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  ShoppingBag,
  Calendar,
  Package,
  ArrowRight,
  MapPin,
  RotateCcw,
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";

export default function CompletedOrdersPage() {
  const [completedOrders, setCompletedOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { user, isAuthenticated } = useAppSelector((state) => state.auth);
  const navigate = useNavigate();
  const [isRefundDialogOpen, setIsRefundDialogOpen] = useState(false);
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);
  const [selectedOrder, setSelectedOrder] = useState<any | null>(null);
  const [refundReason, setRefundReason] = useState("");
  const [refundDetails, setRefundDetails] = useState("");

  // Function to fetch completed orders
  const fetchCompletedOrders = async () => {
    if (!user?.id) return;

    try {
      setLoading(true);
      const response = await axios.get(
        `${API.ORDER_URL}/customers/${user.id}/orders`
      );

      // Filter for completed orders only and sort by date (newest first)
      const completedOrders = response.data
        .filter((order: any) => order.order_status === "completed")
        .sort((a: any, b: any) => {
          return (
            new Date(b.order_completed || b.order_start).getTime() -
            new Date(a.order_completed || a.order_start).getTime()
          );
        });

      setCompletedOrders(completedOrders);
    } catch (error) {
      console.error("Error fetching completed orders:", error);
      toast.error("Failed to load completed orders", {
        description: "Please try again later",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Redirect to login if not authenticated
    if (!isAuthenticated) {
      navigate("/login", { state: { from: "/orders/completed" } });
      return;
    }

    fetchCompletedOrders();
  }, [user?.id, isAuthenticated, navigate]);

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

  const handleRequestRefund = (orderId: string) => {
    const order = completedOrders.find((order) => order.id === orderId);
    if (order) {
      setSelectedOrder(order);
      setSelectedOrderId(orderId);
      setIsRefundDialogOpen(true);
      setRefundReason(""); // Reset form
      setRefundDetails(""); // Reset form
    } else {
      toast.error("Order details not found");
    }
  };

  const submitRefundRequest = async () => {
    if (!user?.id || !selectedOrderId || !refundReason) {
      toast.error("Missing required information for refund");
      return;
    }

    try {
      setIsSubmitting(true);

      // Call the refund endpoint
      const response = await axios.post(
        `${API.CREDIT_URL}/customer/refund`,
        {
          customer_id: user.id,
          order_id: selectedOrderId,
          refund_reason: refundReason,
          refund_details: refundDetails,
        }
      );

      // Update UI
      toast.success("Refund processed successfully", {
        description: `$${response.data.transaction.refund_amount.toFixed(
          2
        )} has been added to your account.`,
      });

      // Close dialog and reset state
      setIsRefundDialogOpen(false);
      setSelectedOrderId(null);
      setSelectedOrder(null);
      setRefundReason("");
      setRefundDetails("");

      // Refresh orders to show any updates
      fetchCompletedOrders();
    } catch (error: any) {
      console.error("Refund error:", error);
      toast.error("Failed to process refund", {
        description: error.response?.data?.error || "Please try again later",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Completed Orders</h1>
          <p className="text-muted-foreground mt-1">
            View history of all your completed orders
          </p>
        </div>
        <div className="flex space-x-2">
          <Link to="/orders">
            <Button variant="outline">Active Orders</Button>
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
      ) : completedOrders.length === 0 ? (
        // No completed orders state
        <div className="text-center py-12">
          <ShoppingBag className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h2 className="text-2xl font-semibold mb-4">
            No completed orders yet
          </h2>
          <p className="text-muted-foreground mb-8">
            You don't have any completed orders yet. Check your active orders to
            see what's in progress.
          </p>
          <Link to="/orders">
            <Button>View Active Orders</Button>
          </Link>
        </div>
      ) : (
        // Completed orders list
        <div className="space-y-6">
          {completedOrders.map((order) => (
            <Card key={order.id} className="overflow-hidden">
              <CardHeader className="pb-2">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                  <div>
                    <CardTitle className="text-lg flex items-center gap-2">
                      Order #{order.id.substring(0, 8)}
                      <Badge className="bg-green-500 text-white">
                        Completed
                      </Badge>
                    </CardTitle>
                    <div className="flex flex-col sm:flex-row sm:gap-4">
                      <div className="flex items-center text-sm text-muted-foreground mt-1">
                        <Calendar className="h-4 w-4 mr-1" />
                        Ordered: {formatDate(order.order_start)}
                      </div>
                      {order.order_completed && (
                        <div className="flex items-center text-sm text-muted-foreground mt-1">
                          <Calendar className="h-4 w-4 mr-1" />
                          Delivered: {formatDate(order.order_completed)}
                        </div>
                      )}
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
                  <div className="flex items-center text-sm">
                    <MapPin className="h-4 w-4 mr-1 text-muted-foreground" />
                    <span className="font-medium">Delivered to:</span>
                  </div>
                  <p className="text-sm pl-6">{order.order_location}</p>
                </div>
              </CardContent>
              <CardFooter className="pt-2 flex flex-col sm:flex-row gap-2">
                <Button
                  variant="outline"
                  className="w-full sm:flex-1 flex items-center justify-center"
                  onClick={() => navigate(`/orders/${order.id}`)}
                >
                  View Details
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
                <Button
                  variant="secondary"
                  className="w-full sm:flex-1 flex items-center justify-center"
                  onClick={() => handleRequestRefund(order.id)}
                >
                  Request Refund
                  <RotateCcw className="h-4 w-4 ml-2" />
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      {/* Refund Request Dialog */}
      <Dialog open={isRefundDialogOpen} onOpenChange={setIsRefundDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Request a Refund</DialogTitle>
            <DialogDescription>
              Please provide details about why you'd like a refund for order #
              {selectedOrderId?.substring(0, 8)}.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {selectedOrder && (
              <div className="p-3 bg-muted rounded-md mb-2">
                <p className="font-medium">
                  Order Total: $
                  {calculateTotal(selectedOrder.order_items).toFixed(2)}
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  This amount will be credited to your account
                </p>
              </div>
            )}
            <div className="space-y-2">
              <label htmlFor="refund-reason" className="text-sm font-medium">
                Reason for refund <span className="text-red-500">*</span>
              </label>
              <select
                id="refund-reason"
                className="w-full p-2 border rounded-md"
                value={refundReason}
                onChange={(e) => setRefundReason(e.target.value)}
                required
              >
                <option value="" disabled>
                  Select a reason
                </option>
                <option value="missing-items">Missing items</option>
                <option value="wrong-items">Wrong items delivered</option>
                <option value="quality-issues">Quality issues</option>
                <option value="late-delivery">Extremely late delivery</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div className="space-y-2">
              <label htmlFor="refund-details" className="text-sm font-medium">
                Additional details
              </label>
              <textarea
                id="refund-details"
                className="w-full p-2 border rounded-md h-24"
                placeholder="Please provide more details about your refund request..."
                value={refundDetails}
                onChange={(e) => setRefundDetails(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsRefundDialogOpen(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              onClick={submitRefundRequest}
              disabled={isSubmitting || !refundReason}
            >
              {isSubmitting ? "Processing..." : "Submit Request"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
