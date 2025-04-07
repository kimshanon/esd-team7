import { ReactNode, useEffect } from "react";
import { onAuthStateChanged } from "firebase/auth";
import axios from "axios";
import { toast } from "sonner";

import { auth } from "@/config/firebase";
import { useAppDispatch } from "@/redux/hooks";
import { setUser, logout } from "@/redux/authSlice";

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const dispatch = useAppDispatch();

  useEffect(() => {
    console.log("Setting up auth state observer");

    // Set up the Firebase auth state observer
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      console.log(
        "Auth state changed:",
        firebaseUser ? "User signed in" : "No user"
      );

      if (firebaseUser) {
        // User is signed in
        try {
          // Try to get user data from both services to determine user type
          let userData = null;
          let userType = null;

          // Try customer endpoint first
          try {
            const customerResponse = await axios.get(
              `http://localhost:5000/customers/${firebaseUser.uid}`
            );
            userData = customerResponse.data;
            userType = "customer";
          } catch (customerError) {
            console.log(
              "Not found in customer database, trying picker database..."
            );

            // If customer not found (will throw an error), try picker endpoint
            const pickerResponse = await axios.get(
              `http://localhost:5001/pickers/${firebaseUser.uid}`
            );
            userData = pickerResponse.data;
            userType = "picker";
          }

          // If we got here, we have valid userData and userType
          console.log(`User found in ${userType} database:`, userData);
          console.log(`Setting user in Redux with ID: ${firebaseUser.uid}`);

          dispatch(
            setUser({
              id: firebaseUser.uid,
              username:
                userType === "customer"
                  ? userData.customer_name
                  : userData.picker_name,
              email: firebaseUser.email || "",
              userType: userType as "customer" | "picker",
            })
          );

          console.log(`Successfully logged in as ${userType}`);
        } catch (error) {
          console.error("Error fetching user data:", error);
          toast.error("Failed to load user profile", {
            description:
              "Your account exists in Firebase but not in our system.",
          });

          // Sign out from Firebase since we couldn't find the user in our backend
          auth.signOut().then(() => {
            dispatch(logout());
          });
        }
      } else {
        // User is signed out
        console.log("Dispatching logout");
        dispatch(logout());
      }
    });

    // Clean up subscription on unmount
    return () => unsubscribe();
  }, [dispatch]);

  return <>{children}</>;
}
