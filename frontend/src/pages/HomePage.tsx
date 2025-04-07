import { Link } from "react-router-dom";
import { Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import RestaurantCard from "@/components/RestaurantCard";
import { restaurants } from "@/data/mockData";

export default function Home() {
  return (
    <div className="container mx-auto px-4 py-8">
      {/* Hero Section */}
      <section className="relative rounded-xl overflow-hidden mb-12">
        <div className="absolute inset-0 bg-primary/90" />
        <img
          src="/placeholder.svg?height=500&width=1200"
          alt="Delicious food"
          className="w-full h-[400px] object-cover"
        />
        <div className="absolute inset-0 flex flex-col justify-center z-20 p-8 md:p-16">
          <h1 className="text-3xl md:text-5xl font-bold text-white mb-4">
            Delicious food, delivered to your door
          </h1>
          <p className="text-white text-lg md:text-xl mb-6 max-w-md">
            Order from your favorite restaurants with just a few clicks
          </p>
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-3 h-5 w-5 text-muted-foreground" />
            <Input
              placeholder="Search for restaurants or dishes..."
              className="pl-10 bg-white/90 h-12 text-black"
            />
          </div>
        </div>
      </section>

      {/* Featured Restaurants */}
      <section className="mb-12">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl md:text-3xl font-bold">
            Featured Restaurants
          </h2>
          <Link to="/restaurants">
            <Button variant="outline">View All</Button>
          </Link>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {restaurants.slice(0, 6).map((restaurant) => (
            <RestaurantCard key={restaurant.id} restaurant={restaurant} />
          ))}
        </div>
      </section>

      {/* Categories */}
      <section className="mb-12">
        <h2 className="text-2xl md:text-3xl font-bold mb-6">
          Browse by Category
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {["Pizza", "Burgers", "Sushi", "Italian", "Chinese", "Mexican"].map(
            (category) => (
              <Link
                to={`/restaurants?category=${category.toLowerCase()}`}
                key={category}
                className="bg-muted rounded-lg p-4 text-center hover:bg-muted/80 transition-colors"
              >
                <div className="w-16 h-16 bg-background rounded-full mx-auto mb-2 flex items-center justify-center">
                  <span className="text-2xl">🍔</span>
                </div>
                <span className="font-medium">{category}</span>
              </Link>
            )
          )}
        </div>
      </section>

      {/* How it works */}
      <section>
        <h2 className="text-2xl md:text-3xl font-bold mb-6">How it works</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="w-16 h-16 bg-primary/10 rounded-full mx-auto mb-4 flex items-center justify-center">
              <span className="text-primary font-bold text-xl">1</span>
            </div>
            <h3 className="text-xl font-semibold mb-2">Choose a restaurant</h3>
            <p className="text-muted-foreground">
              Browse through our selection of restaurants and cuisines
            </p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-primary/10 rounded-full mx-auto mb-4 flex items-center justify-center">
              <span className="text-primary font-bold text-xl">2</span>
            </div>
            <h3 className="text-xl font-semibold mb-2">Select your meals</h3>
            <p className="text-muted-foreground">
              Add your favorite dishes to your cart
            </p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-primary/10 rounded-full mx-auto mb-4 flex items-center justify-center">
              <span className="text-primary font-bold text-xl">3</span>
            </div>
            <h3 className="text-xl font-semibold mb-2">Delivery or pickup</h3>
            <p className="text-muted-foreground">
              Get your food delivered or pick it up yourself
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
