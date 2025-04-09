"use client";

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Clock } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { fetchStamfordFoodListings } from "@/services/api";
import { FoodListing } from "@/types/types";

export default function SpecialFoodListingsPage() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState("");
  const [foodType, setFoodType] = useState("");
  const [listings, setListings] = useState<FoodListing[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadListings = async () => {
      try {
        setLoading(true);
        const data = await fetchStamfordFoodListings();
        setListings(data);
        setError(null);
      } catch (err) {
        setError("Failed to load food listings. Please try again later.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadListings();
  }, []);

  // Filter listings based on search and food type
  const filteredListings = listings.filter((listing) => {
    const matchesSearch =
      listing.Title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      listing.RestaurantName.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesFoodType =
      foodType === "" || listing.FoodType.toLowerCase() === foodType.toLowerCase();

    return matchesSearch && matchesFoodType;
  });

  // Get unique food types for filter dropdown
  const foodTypes = Array.from(
    new Set(listings.map((listing) => listing.FoodType))
  );

  const formatExpiryTime = (expiryTime: string) => {
    const expiry = new Date(expiryTime);
    const now = new Date();
    const hoursUntilExpiry = Math.round((expiry.getTime() - now.getTime()) / (1000 * 60 * 60));
    
    if (hoursUntilExpiry < 24) {
      return `${hoursUntilExpiry} hours left`;
    } else {
      const daysUntilExpiry = Math.round(hoursUntilExpiry / 24);
      return `${daysUntilExpiry} days left`;
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-3xl mx-auto text-center mb-8">
        <h1 className="text-3xl font-bold mb-4">Special Food Listings</h1>
        <p className="text-muted-foreground">
          Browse food items available for self-collection at SMU. Help reduce food waste and enjoy great food at a discounted price!
        </p>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col md:flex-row gap-4 mb-8">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 h-5 w-5 text-muted-foreground" />
          <Input
            placeholder="Search food listings..."
            className="pl-10"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <select
          className="h-10 rounded-md border border-input bg-background px-3 py-2"
          value={foodType}
          onChange={(e) => setFoodType(e.target.value)}
        >
          <option value="">All Types</option>
          {foodTypes.map((type) => (
            <option key={type} value={type.toLowerCase()}>
              {type}
            </option>
          ))}
        </select>
      </div>

      {/* Listings Grid */}
      {loading ? (
        <div className="text-center py-12">Loading food listings...</div>
      ) : error ? (
        <div className="text-center py-12 text-red-500">{error}</div>
      ) : filteredListings.length === 0 ? (
        <div className="text-center py-12">
          <h2 className="text-xl font-semibold mb-2">No food listings found</h2>
          <p className="text-muted-foreground">
            Try adjusting your search or filters
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredListings.map((listing) => (
            <Card key={listing.Id} className="overflow-hidden hover:shadow-md transition-shadow">
              <div className="relative h-48">
                <img
                  src={listing.ImageText || "/placeholder.svg"}
                  alt={listing.Title}
                  className="w-full h-full object-cover"
                />
                <Badge variant="default" className="absolute top-2 right-2">
                  {listing.FoodType}
                </Badge>
              </div>
              <CardContent className="p-4">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-semibold text-lg">{listing.Title}</h3>
                </div>
                <p className="text-sm font-medium mb-1">{listing.RestaurantName}</p>
                <p className="text-sm text-muted-foreground mb-2">
                  Pickup at: {listing.PickupAddress}
                </p>
                {listing.Qty && (
                  <p className="text-sm text-muted-foreground">
                    Available Quantity: {listing.Qty}
                  </p>
                )}
              </CardContent>
              <CardFooter className="p-4 pt-0 text-sm">
                <div className="flex items-center justify-between w-full">
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">Price available at store</span>
                  </div>
                  <div className="flex items-center text-muted-foreground">
                    <Clock className="h-4 w-4 mr-1" />
                    {formatExpiryTime(listing.ExpiryTime)}
                  </div>
                </div>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
} 