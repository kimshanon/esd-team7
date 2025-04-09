"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { toast } from "sonner"
import axios from "axios"
import { User, CreditCard, Phone, Mail, Save, Edit, Loader2, Plus } from "lucide-react"
import * as API from "@/config/api";

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { useAppSelector } from "@/redux/hooks"
import AddCreditsModal from "@/components/AddCreditsModal"

interface CustomerData {
  customer_name: string
  customer_email: string
  customer_phone: number
  customer_credits: number
  firebase_uid: string
  id?: string
}

interface Transaction {
  id: string
  type: "credit" | "debit"
  amount: number
  description: string
  date: string
}

export default function ProfilePage() {
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAppSelector((state) => state.auth)

  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [isAddCreditsModalOpen, setIsAddCreditsModalOpen] = useState(false)
  const [customerData, setCustomerData] = useState<CustomerData | null>(null)
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [formData, setFormData] = useState({
    customer_name: "",
    customer_email: "",
    customer_phone: "",
  })

  useEffect(() => {
    // Redirect to login if not authenticated
    if (!isAuthenticated) {
      navigate("/login", { state: { from: "/profile" } })
      return
    }

    // Only fetch if user is a customer
    if (user?.userType !== "customer") {
      navigate("/")
      toast.error("Only customers can access this page")
      return
    }

    fetchCustomerData()
    fetchTransactions()
  }, [isAuthenticated, user, navigate])

  const fetchCustomerData = async () => {
    try {
      setIsLoading(true)
      const response = await axios.get(`${API.CUSTOMER_URL}/customers/${user?.id}`)
      setCustomerData(response.data)

      // Initialize form data
      setFormData({
        customer_name: response.data.customer_name,
        customer_email: response.data.customer_email,
        customer_phone: response.data.customer_phone.toString(),
      })
    } catch (error) {
      console.error("Error fetching customer data:", error)
      toast.error("Failed to load profile data", {
        description: "Please try again later",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const fetchTransactions = async () => {
    if (!user?.id) return;

    try {
      const response = await axios.get(`${API.PAYMENT_URL}/payments/customer/${user.id}`);

      if (response.data && Array.isArray(response.data)) {
        const payments = response.data;

        // Map API response to Transaction[]
        const mappedTransactions: Transaction[] = payments.map((txn: any) => ({
          id: txn.payment_id || txn.id,
          type:
            txn.event_type === "Add Credits" ? "credit" :
            txn.event_type === "Payment" ? "debit" : "credit", // default
          amount: txn.payment_amount,
          description: txn.event_details || txn.event_type || "Transaction",
          date: txn.timestamp,
        }));

        // Sort by date (most recent first)
        mappedTransactions.sort(
          (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
        );

        setTransactions(mappedTransactions);
      } else {
        setTransactions([]);
      }
    } catch (error) {
      console.error("Error fetching transactions:", error);
      toast.error("Failed to load transaction history");
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { id, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [id]: value,
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    try {
      setIsSaving(true)

      // Prepare data for API
      const updateData = {
        customer_name: formData.customer_name,
        customer_email: formData.customer_email,
        customer_phone: Number.parseInt(formData.customer_phone) || 0,
      }

      // Update customer data
      await axios.put(`${API.CUSTOMER_URL}/customers/${user?.id}`, updateData)

      // Refresh data
      await fetchCustomerData()

      toast.success("Profile updated successfully")
      setIsEditing(false)
    } catch (error) {
      console.error("Error updating profile:", error)
      toast.error("Failed to update profile", {
        description: "Please try again later",
      })
    } finally {
      setIsSaving(false)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    })
  }

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8 flex justify-center items-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-2">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Loading profile data...</p>
        </div>
      </div>
    )
  }

  if (!customerData) {
    return (
      <div className="container mx-auto px-4 py-8 text-center">
        <h2 className="text-2xl font-semibold mb-4">Profile not found</h2>
        <p className="text-muted-foreground mb-8">We couldn't find your profile information.</p>
        <Button onClick={() => navigate("/")}>Return to Home</Button>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Your Profile</h1>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Personal Information Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              Personal Information
            </CardTitle>
            <CardDescription>Manage your personal details</CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="customer_name">Full Name</Label>
                  {!isEditing && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => setIsEditing(true)}
                      className="h-8 px-2 text-muted-foreground"
                    >
                      <Edit className="h-4 w-4 mr-1" />
                      Edit
                    </Button>
                  )}
                </div>
                <Input
                  id="customer_name"
                  value={formData.customer_name}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className={!isEditing ? "bg-muted" : ""}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="customer_email">Email Address</Label>
                <div className="flex items-center gap-2">
                  <Mail className="h-4 w-4 text-muted-foreground" />
                  <Input
                    id="customer_email"
                    value={formData.customer_email}
                    onChange={handleChange}
                    disabled={!isEditing}
                    className={!isEditing ? "bg-muted" : ""}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="customer_phone">Phone Number</Label>
                <div className="flex items-center gap-2">
                  <Phone className="h-4 w-4 text-muted-foreground" />
                  <Input
                    id="customer_phone"
                    value={formData.customer_phone}
                    onChange={handleChange}
                    disabled={!isEditing}
                    className={!isEditing ? "bg-muted" : ""}
                  />
                </div>
              </div>
            </CardContent>

            {isEditing && (
              <CardFooter className="flex justify-between">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setIsEditing(false)
                    // Reset form data to original values
                    setFormData({
                      customer_name: customerData.customer_name,
                      customer_email: customerData.customer_email,
                      customer_phone: customerData.customer_phone.toString(),
                    })
                  }}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={isSaving}>
                  {isSaving ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="mr-2 h-4 w-4" />
                      Save Changes
                    </>
                  )}
                </Button>
              </CardFooter>
            )}
          </form>
        </Card>

        {/* Credits Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CreditCard className="h-5 w-5" />
              Account Credits
            </CardTitle>
            <CardDescription>Manage your account credits</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="rounded-lg bg-muted p-6 text-center">
              <div className="text-4xl font-bold text-primary mb-2">${customerData.customer_credits.toFixed(2)}</div>
              <p className="text-sm text-muted-foreground">Available Credits</p>
            </div>

            <Separator />

            <div className="space-y-4">
              <h3 className="text-sm font-medium">Recent Transactions</h3>

              {transactions.length > 0 ? (
                <div className="space-y-2 text-sm">
                  {transactions.map((transaction) => (
                    <div key={transaction.id} className="flex justify-between items-center py-2 border-b">
                      <div>
                        <p className="font-medium">{transaction.description}</p>
                        <p className="text-muted-foreground">{formatDate(transaction.date)}</p>
                      </div>
                      <div
                        className={`font-medium ${transaction.type === "credit" ? "text-green-500" : "text-red-500"}`}
                      >
                        {transaction.type === "credit" ? "+" : "-"}${transaction.amount.toFixed(2)}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground text-center py-2">
                  No transaction history available
                </p>
              )}
            </div>
          </CardContent>
          <CardFooter>
            <Button className="w-full" onClick={() => setIsAddCreditsModalOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Credits
            </Button>
          </CardFooter>
        </Card>
      </div>

      {/* Add Credits Modal */}
      <AddCreditsModal
        isOpen={isAddCreditsModalOpen}
        onClose={() => setIsAddCreditsModalOpen(false)}
        userId={user?.id || ""}
        onCreditsAdded={fetchCustomerData}
      />
    </div>
  )
}
