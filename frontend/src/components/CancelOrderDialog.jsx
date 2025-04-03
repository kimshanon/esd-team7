"use client"

function CancelOrderDialog({ onCancel, onConfirm }) {
  return (
    <div className="dialog-overlay">
      <div className="dialog">
        <div className="dialog-title">Cancel Order</div>
        <div className="dialog-content">Are you sure you want to cancel this order? This action cannot be undone.</div>
        <div className="dialog-buttons">
          <button className="dialog-button dialog-button-cancel" onClick={onCancel}>
            No, keep order
          </button>
          <button className="dialog-button dialog-button-confirm" onClick={onConfirm}>
            Yes, cancel order
          </button>
        </div>
      </div>
    </div>
  )
}

export default CancelOrderDialog

