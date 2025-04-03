import { useState, useEffect } from "react";
import Header from "./Header";
import ActiveOrder from "./ActiveOrder";
import CompletedOrder from "./CompletedOrder";
import CancelOrderDialog from "./CancelOrderDialog";
import "./Order.css";

function App() {
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [activeOrderData, setActiveOrderData] = useState(null);
  const [completedOrdersData, setCompletedOrdersData] = useState([]);

  useEffect(() => {
    const fetchOrders = async () => {
      try {
        const response = await fetch("http://localhost:5001/orders?customer_id=QbJTSeLiZsbL509BxpY8");
        const data = await response.json();

        if (data.code === 200) {
          const activeOrders = data.data.filter(order => order.order_status === "Active");
          const completedOrders = data.data.filter(order => order.order_status === "Completed");

          setActiveOrderData(activeOrders.length > 0 ? activeOrders[0] : null);
          setCompletedOrdersData(completedOrders);
        }
      } catch (error) {
        console.error("Error fetching orders:", error);
      }
    };

    fetchOrders();
  }, []);

  const handleCancelOrder = () => {
    setShowCancelDialog(false);
    setActiveOrderData(null);
  };

  return (
    <div className="app">
      <Header />
      <div className="container">
        <h1>Your Orders</h1>

        <h2>Active Order</h2>
        {activeOrderData ? (
          <ActiveOrder order={activeOrderData} onCancelClick={() => setShowCancelDialog(true)} />
        ) : (
          <p>No active orders</p>
        )}

        <h2>Completed Orders</h2>
        {completedOrdersData.length > 0 ? (
          completedOrdersData.map(order => <CompletedOrder key={order.customer_id} order={order} />)
        ) : (
          <p>No completed orders yet</p>
        )}
      </div>

      {showCancelDialog && (
        <CancelOrderDialog onCancel={() => setShowCancelDialog(false)} onConfirm={handleCancelOrder} />
      )}
    </div>
  );
}

export default App;
