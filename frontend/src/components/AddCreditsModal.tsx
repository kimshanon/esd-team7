import type React from "react"
import { useState } from "react"
import { toast } from "sonner"
import { CreditCard, Loader2 } from "lucide-react"
import axios from "axios"
import * as API from "@/config/api";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

interface AddCreditsModalProps {
  isOpen: boolean
  onClose: () => void
  userId: string
  onCreditsAdded: () => void
}

export default function AddCreditsModal({ isOpen, onClose, userId, onCreditsAdded }: AddCreditsModalProps) {
  const [amount, setAmount] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Only allow numbers and decimal point
    const value = e.target.value.replace(/[^0-9.]/g, "")
    // Ensure only one decimal point
    const parts = value.split(".")
    if (parts.length > 2) {
      return
    }
    // Limit to 2 decimal places
    if (parts.length === 2 && parts[1].length > 2) {
      return
    }
    setAmount(value)
    setError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // Validate amount
    const amountValue = Number.parseFloat(amount)
    if (isNaN(amountValue) || amountValue <= 0) {
      setError("Please enter a valid amount greater than zero")
      return
    }

    try {
      setIsLoading(true)

      console.log(userId)
      console.log(amountValue)

      // Use the composite microservice instead of calling individual services
      const response = await axios.post(`${API.CREDIT_URL}/credits/add`, {
        customer_id: userId,
        amount: amountValue,
      })

      if (response.status === 201) {
        toast.success("Credits added successfully", {
          description: `$${amountValue.toFixed(2)} has been added to your account`,
        })

        // Reset form and close modal
        setAmount("")
        onCreditsAdded()
        onClose()
      }
    } catch (error) {
      console.error("Error adding credits:", error)
      toast.error("Failed to add credits", {
        description: "Please try again later",
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            Add Credits
          </DialogTitle>
          <DialogDescription>Add credits to your account to use for future orders.</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="amount">Amount</Label>
              <div className="relative">
                <span className="absolute left-3 top-2.5 text-muted-foreground">$</span>
                <Input
                  id="amount"
                  placeholder="0.00"
                  className="pl-7"
                  value={amount}
                  onChange={handleAmountChange}
                  autoFocus
                />
              </div>
              {error && <p className="text-sm text-red-500">{error}</p>}
            </div>
            <div className="space-y-1">
              <Label>Payment Method</Label>
              <div className="flex items-center gap-2 p-2 border rounded-md">
                <div className="h-8 w-12 bg-muted rounded flex items-center justify-center">
                  <CreditCard className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-sm font-medium">Credit Card ending in 4242</p>
                  <p className="text-xs text-muted-foreground">Expires 12/25</p>
                </div>
              </div>
              <p className="text-xs text-muted-foreground">This is a demo. No actual payment will be processed.</p>
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose} disabled={isLoading}>
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                "Add Credits"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

