"use client"

import { useState, useEffect } from "react"

function Header() {
  const [activePage, setActivePage] = useState("orders")

  useEffect(() => {
    // In a real app, this would be based on the current route
    setActivePage("orders")
  }, [])

  return (
    <header>
      <div className="logo">CampusEats</div>
      <div className="nav-links">
        <a href="/" className={activePage === "home" ? "active" : ""}>
          Home
        </a>
        <a href="/food" className={activePage === "food" ? "active" : ""}>
          Food
        </a>
        <a href="/orders" className={activePage === "orders" ? "active" : ""}>
          My Orders
        </a>
      </div>
      <div className="user-icon">JD</div>
    </header>
  )
}

export default Header

