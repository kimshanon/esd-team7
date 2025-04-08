"use client"

import { useState, useEffect } from "react"
import { useNavigate, Link } from "react-router-dom"
import { ShoppingBag, Package, ArrowRight, Calendar, MapPin, Edit } from "lucide-react"
import axios from "axios"
import { format } from "date-fns"
import { useAppSelector } from "@/redux/hooks"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import ChangeLocationModal from "@/components/ChangeLocationModal"

// Order status mapping for UI display
const orderStatusMap = {
  pending: { label: "Pending", color: "bg-yellow-500" },
  assigned: { label: "Assigned", color: "bg-blue-500" },
  preparing: { label: "Preparing", color: "bg-purple-500" },
  delivering: { label: "Out for Delivery", color: "bg-indigo-500" },
  completed: { label: "Delivered", color: "bg-green-500" },
  cancelled: { label: "Cancelled", color: "bg-red-500" },
}

// UI badge component for order status
function OrderStatusBadge({ status }: { status: string }) {
  const statusInfo = orderStatusMap[status as keyof typeof orderStatusMap] || {
    label: status,
    color: "bg-gray-500",
  }

  return <Badge className={`${statusInfo.color} text-white`}>{statusInfo.label}</Badge>
}

export default function OrdersPage() {
  const [orders, setOrders] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const { user, isAuthenticated } = useAppSelector((state) => state.auth)
  const navigate = useNavigate()
  const [selectedOrderForLocation, setSelectedOrderForLocation] = useState<{ id: string; location: string } | null>(
    null,
  )

  useEffect(() => {
    // Redirect to login if not authenticated
    if (!isAuthenticated) {
      navigate("/login", { state: { from: "/orders" } })
      return
    }

    async function fetchOrders() {
      try {
        setLoading(true)
        const response = await axios.get(`http://127.0.0.1:5003/customers/${user?.id}/orders`)

        // Sort orders by date (newest first)
        const sortedOrders = response.data.sort((a: any, b: any) => {
          return new Date(b.order_start).getTime() - new Date(a.order_start).getTime()
        })

        setOrders(sortedOrders)
      } catch (error) {
        console.error("Error fetching orders:", error)
        toast.error("Failed to load orders", {
          description: "Please try again later",
        })
      } finally {
        setLoading(false)
      }
    }

    if (user?.id) {
      fetchOrders()
    }
  }, [user?.id, isAuthenticated, navigate])

  // Calculate total cost of an order
  const calculateTotal = (items: any[]) => {
    return items.reduce((sum, item) => sum + item.order_price * item.order_quantity, 0)
  }

  // Format date string
  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString)
      return format(date, "PPP 'at' p") // e.g., "Apr 29, 2023 at 2:30 PM"
    } catch (error) {
      return dateString
    }
  }

  // Handle location update
  const handleLocationUpdated = (newLocation: string) => {
    if (selectedOrderForLocation) {
      // Update the order in the local state
      setOrders(
        orders.map((order) =>
          order.id === selectedOrderForLocation.id ? { ...order, order_location: newLocation } : order,
        ),
      )

      toast.success("Delivery location updated successfully")
      setSelectedOrderForLocation(null)
    }
  }

  // Check if order can have its location edited
  const canEditLocation = (status: string) => {
    return ["pending", "assigned", "preparing"].includes(status)
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Your Orders</h1>
        <Link to="/">
          <Button variant="outline">Continue Shopping</Button>
        </Link>
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
          <h2 className="text-2xl font-semibold mb-4">No orders yet</h2>
          <p className="text-muted-foreground mb-8">
            You haven't placed any orders yet. Browse our restaurants to place your first order!
          </p>
          <Link to="/">
            <Button>Explore Restaurants</Button>
          </Link>
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
                    {order.order_items.slice(0, 3).map((item: any, index: number) => (
                      <li key={index} className="text-sm">
                        {item.order_quantity}x {item.order_item} - $
                        {(item.order_price * item.order_quantity).toFixed(2)}
                      </li>
                    ))}
                    {order.order_items.length > 3 && (
                      <li className="text-sm text-muted-foreground">+{order.order_items.length - 3} more items</li>
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
  )
}
