"use client";

import { Plus } from "lucide-react";

import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";
import type { MenuItemFrontend } from "@/types/types";

interface MenuItemCardProps {
  item: MenuItemFrontend;
  onAddToCart: () => void;
}

export default function MenuItemCard({ item, onAddToCart }: MenuItemCardProps) {
  return (
    <Card className="overflow-hidden border shadow-sm py-0">
      <div className="flex flex-col md:flex-row">
        <div className="md:w-1/3">
          <img
            src={item.image || "/placeholder.svg"}
            alt={item.name}
            className="w-full h-full object-cover aspect-square"
          />
        </div>
        <CardContent className="flex-1 p-4 flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-start mb-2">
              <h3 className="font-semibold">{item.name}</h3>
              <span className="font-medium">${item.price.toFixed(2)}</span>
            </div>
            <p className="text-sm text-muted-foreground line-clamp-2 mb-4">
              {item.description}
            </p>
          </div>
          <Button
            size="sm"
            className="self-end"
            onClick={(e) => {
              e.preventDefault();
              onAddToCart();
            }}
          >
            <Plus className="h-4 w-4 mr-1" />
            Add to Cart
          </Button>
        </CardContent>
      </div>
    </Card>
  );
}
