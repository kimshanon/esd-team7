import { Outlet } from "react-router-dom"
import Header from "./Header"
import Footer from "./Footer"
import { Link } from "react-router-dom"

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b">
        <div className="container mx-auto px-4 py-3">
          <nav className="flex items-center justify-between">
            <div className="flex items-center space-x-8">
              <Link to="/" className="text-xl font-bold">
                SMUlivery
              </Link>
              <div className="hidden md:flex items-center space-x-6">
                <Link
                  to="/"
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  Home
                </Link>
                <Link
                  to="/special"
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  Special
                </Link>
                <Link
                  to="/orders"
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  My Orders
                </Link>
              </div>
            </div>
            {/* ... rest of the navigation ... */}
          </nav>
        </div>
      </header>
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}

