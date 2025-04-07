import { Minus, Plus, Trash } from "lucide-react";
import { MenuItemFrontend } from "@/types/types";
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";

interface CartItem extends MenuItemFrontend {
  quantity: number;
  restaurantId?: string; // Make this optional for backward compatibility
}

interface CartItemCardProps {
  item: CartItem;
  onRemove: () => void;
  onUpdateQuantity: (quantity: number) => void;
}

export default function CartItemCard({
  item,
  onRemove,
  onUpdateQuantity,
}: CartItemCardProps) {
  const itemTotal = item.price * item.quantity;

  return (
    <Card className="overflow-hidden">
      <CardContent className="p-4">
        <div className="flex gap-4">
          <div className="h-20 w-20 flex-shrink-0">
            <img
              src={item.image || "/placeholder.svg"}
              alt={item.name}
              className="h-full w-full rounded-md object-cover"
            />
          </div>
          <div className="flex flex-1 flex-col">
            <div className="flex justify-between">
              <h3 className="font-medium">{item.name}</h3>
              <p className="font-medium">${itemTotal.toFixed(2)}</p>
            </div>
            <p className="text-sm text-muted-foreground">
              ${item.price.toFixed(2)} each
            </p>
            <div className="mt-auto flex items-center justify-between">
              <div className="flex items-center">
                <Button
                  variant="outline"
                  size="icon"
                  className="h-8 w-8 rounded-full"
                  onClick={() => onUpdateQuantity(item.quantity - 1)}
                  disabled={item.quantity <= 1}
                >
                  <Minus className="h-3 w-3" />
                  <span className="sr-only">Decrease</span>
                </Button>
                <span className="mx-2 w-6 text-center">{item.quantity}</span>
                <Button
                  variant="outline"
                  size="icon"
                  className="h-8 w-8 rounded-full"
                  onClick={() => onUpdateQuantity(item.quantity + 1)}
                >
                  <Plus className="h-3 w-3" />
                  <span className="sr-only">Increase</span>
                </Button>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-muted-foreground hover:text-foreground"
                onClick={onRemove}
              >
                <Trash className="h-4 w-4" />
                <span className="sr-only">Remove</span>
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
