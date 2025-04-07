import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

// Your web app's Firebase configuration
// Replace these with your actual Firebase project details
const firebaseConfig = {
    apiKey: "AIzaSyCRDx3WscAUzwPqQsOUfsvXK-9YbmiL6RA",
    authDomain: "esd-team-7.firebaseapp.com",
    projectId: "esd-team-7",
    storageBucket: "esd-team-7.firebasestorage.app",
    messagingSenderId: "364578801673",
    appId: "1:364578801673:web:5ecced026d2d68438b10d8",
    measurementId: "G-DTC7NPGTNY"
  };

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);

export default app;