import { useState } from "react";
import LocationChangeComponent from "./LocationChangeComponent";

function ActiveOrder({ order, onCancelClick }) {
  const [location, setLocation] = useState(order.location.address);
  const [showLocationSuccess, setShowLocationSuccess] = useState(false);
  const [showLocationChange, setShowLocationChange] = useState(false);

  const handleLocationChange = (newLocation) => {
    setLocation(newLocation);
    setShowLocationChange(false);
    setShowLocationSuccess(true);

    setTimeout(() => setShowLocationSuccess(false), 3000);
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
          <strong>Delivery Location:</strong> {location}
        </div>
        <div className="order-info">
          <strong>Coordinates:</strong> {order.location.coordinates.lat}, {order.location.coordinates.lng}
        </div>
        <div className="order-info">
          <strong>Postal Code:</strong> {order.location.postal}
        </div>
        <div className="order-info">
          <strong>Credits Used:</strong> {order.credit}
        </div>
        <div className="order-info">
          <strong>Picker ID:</strong> {order.picker_id ? order.picker_id : "Not assigned"}
        </div>

        {showLocationSuccess && <div className="success-message">Delivery location updated successfully!</div>}

        <button className="action-button change-location-button" onClick={() => setShowLocationChange(true)}>
          Change Delivery Location
        </button>

        <button className="action-button cancel-button" onClick={onCancelClick}>
          Cancel Order
        </button>
      </div>

      {showLocationChange && (
        <LocationChangeComponent
          currentLocation={location}
          onClose={() => setShowLocationChange(false)}
          onLocationChange={handleLocationChange}
        />
      )}
    </div>
  );
}

export default ActiveOrder;
