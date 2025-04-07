import { Link } from "react-router-dom";
import { Clock, Star } from "lucide-react";

import { Badge } from "./ui/badge";
import { Card, CardContent, CardFooter } from "./ui/card";
import type { Restaurant } from "../types/types";

interface RestaurantCardProps {
  restaurant: Restaurant;
}

export default function RestaurantCard({ restaurant }: RestaurantCardProps) {
  return (
    <Link to={`/restaurants/${restaurant.id}`}>
      <Card className="overflow-hidden hover:shadow-md transition-shadow py-0 gap-3 border shadow-sm">
        <div className="relative h-48">
          <img
            src={restaurant.image || "/placeholder.svg"}
            alt={restaurant.name}
            className="w-full h-full object-cover"
          />
          {restaurant.isPromoted && (
            <Badge className="absolute top-2 right-2">Promoted</Badge>
          )}
        </div>
        <CardContent className="p-4">
          <div className="flex justify-between items-start mb-2">
            <h3 className="font-semibold text-lg">{restaurant.name}</h3>
            <div className="flex items-center">
              <Star className="h-4 w-4 text-yellow-500 mr-1" />
              <span>{restaurant.rating}</span>
            </div>
          </div>
          <div className="flex flex-wrap gap-1 mb-2">
            {restaurant.cuisines.slice(0, 3).map((cuisine) => (
              <Badge key={cuisine} variant="outline" className="text-xs">
                {cuisine}
              </Badge>
            ))}
          </div>
          <p className="text-sm text-muted-foreground line-clamp-2 mb-2">
            {restaurant.description}
          </p>
        </CardContent>
        <CardFooter className="p-4 pt-0 text-sm text-muted-foreground">
          <div className="flex items-center justify-between w-full">
            <span className="flex items-center">
              <Clock className="h-4 w-4 mr-1" />
              {restaurant.deliveryTime} min
            </span>
            <span>${restaurant.deliveryFee.toFixed(2)} delivery</span>
          </div>
        </CardFooter>
      </Card>
    </Link>
  );
}
