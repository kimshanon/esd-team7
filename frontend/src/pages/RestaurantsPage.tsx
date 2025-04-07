"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { Search } from "lucide-react";

import { Input } from "@/components/ui/input";
import RestaurantCard from "@/components/RestaurantCard";
import { fetchAllRestaurants } from "@/services/api";
import { Restaurant } from "@/types/types";

export default function RestaurantsPage() {
  const [searchParams] = useSearchParams();
  const categoryParam = searchParams.get("category");

  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState(categoryParam || "");
  const [sortBy, setSortBy] = useState("recommended");

  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadRestaurants = async () => {
      try {
        setLoading(true);
        const data = await fetchAllRestaurants();
        setRestaurants(data);
        setError(null);
      } catch (err) {
        setError("Failed to load restaurants. Please try again later.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadRestaurants();
  }, []);

  // Filter restaurants based on search, category, and sort
  const filteredRestaurants = restaurants.filter((restaurant) => {
    const matchesSearch =
      restaurant.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      restaurant.description.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesCategory =
      selectedCategory === "" ||
      restaurant.cuisines.some(
        (cuisine) => cuisine.toLowerCase() === selectedCategory.toLowerCase()
      );

    return matchesSearch && matchesCategory;
  });

  // Sort restaurants
  const sortedRestaurants = [...filteredRestaurants].sort((a, b) => {
    if (sortBy === "rating") {
      return b.rating - a.rating;
    } else if (sortBy === "delivery-time") {
      return a.deliveryTime - b.deliveryTime;
    }
    // Default: recommended
    return 0;
  });

  // Get unique cuisine types for filter dropdown
  const allCuisines = Array.from(
    new Set(restaurants.flatMap((restaurant) => restaurant.cuisines))
  );

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Restaurants</h1>

      {/* Search and Filters */}
      <div className="flex flex-col md:flex-row gap-4 mb-8">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 h-5 w-5 text-muted-foreground" />
          <Input
            placeholder="Search restaurants..."
            className="pl-10"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <select
          className="h-10 rounded-md border border-input bg-background px-3 py-2"
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
        >
          <option value="">All Categories</option>
          {allCuisines.map((cuisine) => (
            <option key={cuisine} value={cuisine.toLowerCase()}>
              {cuisine}
            </option>
          ))}
        </select>
        <select
          className="h-10 rounded-md border border-input bg-background px-3 py-2"
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
        >
          <option value="recommended">Recommended</option>
          <option value="rating">Highest Rated</option>
          <option value="delivery-time">Fastest Delivery</option>
        </select>
      </div>

      {/* Restaurant Grid */}
      {loading ? (
        <div className="text-center py-12">Loading restaurants...</div>
      ) : error ? (
        <div className="text-center py-12 text-red-500">{error}</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {sortedRestaurants.map((restaurant) => (
            <RestaurantCard key={restaurant.id} restaurant={restaurant} />
          ))}
        </div>
      )}

      {!loading && !error && sortedRestaurants.length === 0 && (
        <div className="text-center py-12">
          <h2 className="text-xl font-semibold mb-2">No restaurants found</h2>
          <p className="text-muted-foreground">
            Try adjusting your search or filters
          </p>
        </div>
      )}
    </div>
  );
}
