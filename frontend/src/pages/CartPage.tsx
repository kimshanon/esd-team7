import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Trash2, MapPin } from "lucide-react";
import axios from "axios";
import { toast } from "sonner";
import * as API from "@/config/api";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { useCart } from "@/contexts/CartContext";
import { useAppSelector } from "@/redux/hooks";
import CartItemCard from "@/components/CartItemCard";
import { Label } from "@/components/ui/label";
import DeliveryLocation from "@/components/DeliveryLocation";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";

export default function CartPage() {
  const { cart, removeFromCart, updateQuantity, clearCart } = useCart();
  const [promoCode, setPromoCode] = useState("");
  const [deliveryAddress, setDeliveryAddress] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isMapOpen, setIsMapOpen] = useState(false);
  const navigate = useNavigate();

  // Get user from auth state
  const { user, isAuthenticated } = useAppSelector((state) => state.auth);

  const subtotal = cart.reduce(
    (sum, item) => sum + item.price * item.quantity,
    0
  );
  const deliveryFee = subtotal > 0 ? 3.99 : 0;
  const total = subtotal + deliveryFee;

  const handleLocationChange = (location: string) => {
    setDeliveryAddress(location);
    setIsMapOpen(false);
  };

  const handleCheckout = async () => {
    if (!isAuthenticated || !user) {
      toast.error("Please login to checkout");
      navigate("/login", { state: { from: "/cart" } });
      return;
    }

    if (!deliveryAddress.trim()) {
      toast.error("Please select a delivery address");
      return;
    }

    setIsLoading(true);

    try {
      // Get the restaurant ID from the first item in the cart
      // This assumes all items in cart are from the same restaurant
      const stallId = cart[0]?.restaurantId;

      if (!stallId) {
        toast.error("Invalid restaurant information");
        return;
      }

      // Format cart items according to the OrderItemModel schema
      const orderItems = cart.map((item) => ({
        order_item: item.name,
        order_quantity: item.quantity,
        order_price: item.price,
      }));

      // Prepare order data according to OrderModel schema
      const orderData = {
        customer_id: user.id,
        stall_id: stallId,
        order_status: "pending", // default status
        order_location: deliveryAddress,
        is_paid: false, // This could be set to true if using immediate payment
        order_items: orderItems,
      };

      // Post to orders endpoint
      // Instead of posting directly to the orders API, we'll post through
      // the assignment service to handle the WebSocket broadcasting
      const response = await axios.post(
        `${API.ASSIGN_PICKER_URL}/orders`, // This endpoint forwards to the order service and handles WebSocket
        orderData
      );

      // Handle successful order
      toast.success("Order placed successfully!", {
        description: `Order #${response.data.order_id} has been created.`,
      });

      // Clear the cart
      clearCart();

      // Redirect to the orders route
      navigate("/orders");
    } catch (error) {
      console.error("Checkout error:", error);
      toast.error("Failed to place order", {
        description: "Please try again later.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center mb-6">
        <Link
          to="/"
          className="flex items-center text-muted-foreground hover:text-foreground mr-4"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Continue Shopping
        </Link>
        <h1 className="text-3xl font-bold">Your Cart</h1>
      </div>

      {cart.length === 0 ? (
        <div className="text-center py-12">
          <h2 className="text-2xl font-semibold mb-4">Your cart is empty</h2>
          <p className="text-muted-foreground mb-6">
            Looks like you haven't added anything to your cart yet.
          </p>
          <Link to="/">
            <Button>Browse Restaurants</Button>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">
                Cart Items ({cart.length})
              </h2>
              <Button
                variant="ghost"
                size="sm"
                className="text-red-500 hover:text-red-700 hover:bg-red-50"
                onClick={clearCart}
              >
                <Trash2 className="h-4 w-4 mr-1" />
                Clear Cart
              </Button>
            </div>

            <div className="space-y-4">
              {cart.map((item) => (
                <CartItemCard
                  key={item.id}
                  item={item}
                  onRemove={() => removeFromCart(item.id)}
                  onUpdateQuantity={(quantity) =>
                    updateQuantity(item.id, quantity)
                  }
                />
              ))}
            </div>
          </div>

          <div className="lg:col-span-1">
            <div className="bg-muted/30 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Order Summary</h2>

              <div className="space-y-4 mb-6">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Subtotal</span>
                  <span>${subtotal.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Delivery Fee</span>
                  <span>${deliveryFee.toFixed(2)}</span>
                </div>
                <Separator />
                <div className="flex justify-between font-semibold">
                  <span>Total</span>
                  <span>${total.toFixed(2)}</span>
                </div>
              </div>

              {/* Replace Delivery Address Input with Button + Dialog */}
              <div className="space-y-2 mb-4">
                <Label htmlFor="deliveryAddress" className="flex items-center">
                  <MapPin className="h-4 w-4 mr-1" />
                  Delivery Address
                </Label>

                <Dialog open={isMapOpen} onOpenChange={setIsMapOpen}>
                  <DialogTrigger asChild>
                    <Button
                      variant="outline"
                      className="w-full text-left justify-between font-normal"
                    >
                      {deliveryAddress ? (
                        <span className="truncate">{deliveryAddress}</span>
                      ) : (
                        <span className="text-muted-foreground">
                          Select delivery location
                        </span>
                      )}
                      <MapPin className="h-4 w-4 ml-2 flex-shrink-0" />
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="sm:max-w-[700px] p-0 h-auto max-h-[90vh] overflow-hidden">
                    {/* Remove the close button from DialogContent by passing hideCloseButton prop */}
                    <DeliveryLocation
                      currentLocation={deliveryAddress}
                      onClose={() => setIsMapOpen(false)}
                      onLocationChange={handleLocationChange}
                    />
                  </DialogContent>
                </Dialog>

                {deliveryAddress && (
                  <p className="text-xs text-muted-foreground mt-1 ml-1">
                    {deliveryAddress}
                  </p>
                )}
              </div>

              <div className="flex gap-2 mb-4">
                <Input
                  placeholder="Promo code"
                  value={promoCode}
                  onChange={(e) => setPromoCode(e.target.value)}
                />
                <Button variant="outline">Apply</Button>
              </div>

              <Button
                className="w-full"
                size="lg"
                onClick={handleCheckout}
                disabled={isLoading || cart.length === 0}
              >
                {isLoading ? "Processing..." : "Proceed to Checkout"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
