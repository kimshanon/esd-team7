import { useState } from "react";

function CancelledOrder({ order }) {

  return (
    <div className="order-card">
      <div className="order-header">
        <div>
          <div className="restaurant-name">Stall ID: {order.stall_id}</div>
          <div className="order-id">Customer ID: {order.customer_id}</div>
        </div>
        <span className={`status-badge status-${order.order_status}`}>{order.order_status}</span>
      </div>

      <div className="order-content">
        <div className="order-info">
          <strong>Items:</strong> {order.items}
        </div>
        <div className="order-info">
          <strong>Ordered at:</strong> {order.orderedAt}
        </div>
        <div className="order-info">
          <strong>Delivered at:</strong> {order.deliveredAt}
        </div>
        <div className="order-info">
          <strong>Delivery location:</strong> {order.location.address}
        </div>
      </div>

      <div className="order-footer">
        <span className="total-label">Total</span>
        <span className="total-price">{order.total}</span>
      </div>
    </div>
  );
}

export default CancelledOrder;