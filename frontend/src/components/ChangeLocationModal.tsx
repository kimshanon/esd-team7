"use client"

import { useState } from "react"
import { MapPin, X } from "lucide-react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"

// Import the LocationChangeComponent
import LocationChangeComponent from "./LocationChangeComponent"

interface ChangeLocationModalProps {
  isOpen: boolean
  onClose: () => void
  currentLocation: string
  orderId: string
  onLocationUpdated: (newLocation: string) => void
}

export default function ChangeLocationModal({
  isOpen,
  onClose,
  currentLocation,
  orderId,
  onLocationUpdated,
}: ChangeLocationModalProps) {
  const [isUpdating, setIsUpdating] = useState(false)

  const handleLocationChange = (newLocation: string) => {
    onLocationUpdated(newLocation)
    onClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-[700px] p-0 overflow-hidden">
        <DialogHeader className="px-6 pt-6 pb-2">
          <div className="flex items-center justify-between">
            <DialogTitle className="flex items-center">
              <MapPin className="h-5 w-5 mr-2 text-primary" />
              Change Delivery Location
            </DialogTitle>
          </div>
        </DialogHeader>

        <div className="h-[600px] overflow-auto">
          <LocationChangeComponent
            currentLocation={currentLocation}
            onClose={onClose}
            onLocationChange={handleLocationChange}
            orderId={orderId}
          />
        </div>
      </DialogContent>
    </Dialog>
  )
}
