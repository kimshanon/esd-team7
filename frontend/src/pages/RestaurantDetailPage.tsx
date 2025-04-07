"use client";

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Clock, Star, ArrowLeft } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import MenuItemCard from "@/components/MenuItemCard";
import { useCart } from "@/contexts/CartContext";
import { fetchRestaurantById } from "@/services/api";
import { Restaurant, MenuItemFrontend } from "@/types/types";

export default function RestaurantDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [restaurant, setRestaurant] = useState<Restaurant | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeCategory, setActiveCategory] = useState("all");

  const { addToCart } = useCart();

  useEffect(() => {
    const loadRestaurant = async () => {
      if (!id) return;

      try {
        setLoading(true);
        const data = await fetchRestaurantById(id);
        setRestaurant(data);
        setError(null);
      } catch (err) {
        setError("Failed to load restaurant details. Please try again later.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadRestaurant();
  }, [id]);

  // If loading or error, show appropriate message
  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 text-center">
        <div className="text-xl">Loading restaurant details...</div>
      </div>
    );
  }

  if (error || !restaurant) {
    return (
      <div className="container mx-auto px-4 py-8 text-center">
        <h2 className="text-2xl font-bold mb-4">
          {error || "Restaurant not found"}
        </h2>
        <Button onClick={() => navigate("/restaurants")}>
          Back to Restaurants
        </Button>
      </div>
    );
  }

  // Get unique categories from menu items
  const menuCategories = [
    "all",
    ...new Set(restaurant.menu.map((item) => item.category)),
  ];

  // Filter menu items based on selected category
  const filteredMenu =
    activeCategory === "all"
      ? restaurant.menu
      : restaurant.menu.filter((item) => item.category === activeCategory);

  return (
    <div>
      {/* Restaurant Banner */}
      <div className="relative h-[300px]">
        <img
          src={restaurant.image || "/placeholder.svg"}
          alt={restaurant.name}
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-black/50" />
      </div>

      {/* Restaurant Info */}
      <div className="container mx-auto px-4 py-8">
        <Button
          variant="ghost"
          className="mb-4 flex items-center text-muted-foreground hover:text-foreground"
          onClick={() => navigate("/")}
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Restaurants
        </Button>

        <div className="flex flex-col md:flex-row justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold mb-2">{restaurant.name}</h1>
            <div className="flex items-center gap-4 text-sm text-muted-foreground mb-2">
              <span className="flex items-center">
                <Star className="h-4 w-4 text-yellow-500 mr-1" />
                {restaurant.rating} ({restaurant.reviewCount} reviews)
              </span>
              <span className="flex items-center">
                <Clock className="h-4 w-4 mr-1" />
                {restaurant.deliveryTime} min
              </span>
              <span>${restaurant.deliveryFee.toFixed(2)} delivery fee</span>
            </div>
            <div className="flex flex-wrap gap-2 mb-4">
              {restaurant.cuisines.map((cuisine) => (
                <Badge key={cuisine} variant="outline">
                  {cuisine}
                </Badge>
              ))}
            </div>
            <p className="text-muted-foreground max-w-2xl">
              {restaurant.description}
            </p>
          </div>
        </div>

        {/* Menu */}
        <Tabs defaultValue="menu" className="mb-8">
          <TabsList>
            <TabsTrigger value="menu">Menu</TabsTrigger>
            <TabsTrigger value="reviews">Reviews</TabsTrigger>
            <TabsTrigger value="info">Info</TabsTrigger>
          </TabsList>
          <TabsContent value="menu">
            <div className="flex overflow-x-auto gap-2 py-4 mb-6">
              {menuCategories.map((category) => (
                <Button
                  key={category}
                  variant={activeCategory === category ? "default" : "outline"}
                  onClick={() => setActiveCategory(category)}
                  className="capitalize"
                >
                  {category}
                </Button>
              ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {filteredMenu.map((item) => (
                <MenuItemCard
                  key={item.id}
                  item={item}
                  onAddToCart={() => addToCart(item, restaurant.id)} // Pass restaurant.id
                />
              ))}
            </div>

            {filteredMenu.length === 0 && (
              <div className="text-center py-8">
                No menu items found in this category
              </div>
            )}
          </TabsContent>
          <TabsContent value="reviews">
            <p className="text-muted-foreground">Reviews coming soon...</p>
          </TabsContent>
          <TabsContent value="info">
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-semibold mb-2">Address</h3>
                <p className="text-muted-foreground">{restaurant.location}</p>
              </div>
              <div>
                <h3 className="text-lg font-semibold mb-2">Hours</h3>
                <p className="text-muted-foreground">
                  Monday - Friday: 11:00 AM - 10:00 PM
                </p>
                <p className="text-muted-foreground">
                  Saturday - Sunday: 10:00 AM - 11:00 PM
                </p>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
