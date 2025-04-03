import { useState } from "react";
import RefundRequestComponent from "./RefundRequestComponent";

function CompletedOrder({ order }) {
  const [showRefundForm, setShowRefundForm] = useState(false);
  const [showRefundSuccess, setShowRefundSuccess] = useState(false);

  const handleRefundSubmit = () => {
    setShowRefundForm(false);
    setShowRefundSuccess(true);
    setTimeout(() => setShowRefundSuccess(false), 3000);
  };

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
        <div className="order-info">
          <strong>Coordinates:</strong> {order.location.coordinates.lat}, {order.location.coordinates.lng}
        </div>
        <div className="order-info">
          <strong>Postal Code:</strong> {order.location.postal}
        </div>

        {showRefundSuccess && <div className="success-message">Refund request submitted successfully!</div>}

        {!showRefundSuccess && !showRefundForm && (
          <button className="action-button refund-button" onClick={() => setShowRefundForm(true)}>
            Request Refund
          </button>
        )}
      </div>

      {showRefundForm && (
        <RefundRequestComponent
          orderId={order.id}
          onCancel={() => setShowRefundForm(false)}
          onSubmit={handleRefundSubmit}
        />
      )}

      <div className="order-footer">
        <span className="total-label">Total</span>
        <span className="total-price">{order.total}</span>
      </div>
    </div>
  );
}

export default CompletedOrder;
