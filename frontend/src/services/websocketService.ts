import { io, Socket } from "socket.io-client";
import * as API from "@/config/api";

// WebSocket events we'll be listening for
export const WS_EVENTS = {
  ORDER_WAITING: "order_waiting",
  ORDER_TAKEN: "order_taken",
  PICKER_UPDATE: "picker_update",
  REGISTER_PICKER: "register_picker",
  REGISTER_CUSTOMER: "register_customer",
  TEST_EVENT: "test_event",
  TEST_RESPONSE: "test_response",
};

class WebSocketService {
  private socket: Socket | null = null;
  private pickerId: string | null = null;
  private connected: boolean = false;
  private eventHandlers: Record<string, Array<(data: any) => void>> = {};

  constructor() {
    // Initialize empty event handler collections for each event type
    Object.values(WS_EVENTS).forEach((event) => {
      this.eventHandlers[event] = [];
    });
  }

  // Connect to the WebSocket server
  connect(url: string = `${API.ASSIGN_PICKER_URL}`) {
    if (this.socket) {
      console.log("WebSocket already connected");
      return;
    }

    this.socket = io(url, {
      // transports: ["websocket", "polling"],
      // withCredentials: true,
      // If you created a separate route for WebSockets with a specific path:
      // path: "/api/assign-picker/socket.io", // Only if your Kong route doesn't already include /socket.io
    });

    this.socket.on("connect", () => {
      console.log("WebSocket connected");
      this.connected = true;

      // Register the picker if we have a picker ID set already
      if (this.pickerId) {
        this.registerAsPicker(this.pickerId);
      }
    });

    this.socket.on("disconnect", () => {
      console.log("WebSocket disconnected");
      this.connected = false;
    });

    // Set up listeners for all the events we're interested in
    Object.values(WS_EVENTS).forEach((event) => {
      this.socket?.on(event, (data: any) => {
        console.log(`Received ${event} event:`, data);
        this.eventHandlers[event].forEach((handler) => handler(data));
      });
    });
  }

  // Disconnect from the WebSocket server
  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.connected = false;
      this.pickerId = null;
      console.log("WebSocket disconnected");
    }
  }

  // Register as a picker to receive order notifications
  registerAsPicker(pickerId: string) {
    if (!this.socket || !this.connected) {
      console.log("WebSocket not connected, can't register picker");
      this.pickerId = pickerId; // Store for when we connect
      return;
    }

    console.log(`Registering picker: ${pickerId}`);
    this.pickerId = pickerId;
    this.socket.emit(WS_EVENTS.REGISTER_PICKER, { picker_id: pickerId });
  }

  // Register for updates on a specific order (typically for customers)
  registerForOrderUpdates(customerId: string, orderId: string) {
    if (!this.socket || !this.connected) {
      console.log("WebSocket not connected, can't register for order updates");
      return;
    }

    this.socket.emit(WS_EVENTS.REGISTER_CUSTOMER, {
      customer_id: customerId,
      order_id: orderId,
    });
  }

  // Add this new method to register for all order updates for a customer
  registerForAllCustomerOrders(customerId: string, orderIds: string[]) {
    if (!this.socket || !this.connected) {
      console.log(
        "WebSocket not connected, can't register for customer orders"
      );
      return;
    }

    console.log(
      `Registering customer ${customerId} for updates on ${orderIds.length} orders`
    );

    // Register each order individually
    orderIds.forEach((orderId) => {
      this.socket!.emit(WS_EVENTS.REGISTER_CUSTOMER, {
        customer_id: customerId,
        order_id: orderId,
      });
    });
  }

  // Send a picker's acceptance of an order
  acceptOrder(pickerId: string, orderId: string) {
    if (!this.socket || !this.connected) {
      console.log("WebSocket not connected, can't accept order");
      return false;
    }

    // We'll use the HTTP endpoint instead of WebSocket for this
    // but we could emit an event here as well
    return true;
  }

  // Add an event handler
  on(event: string, handler: (data: any) => void) {
    if (!this.eventHandlers[event]) {
      this.eventHandlers[event] = [];
    }
    this.eventHandlers[event].push(handler);
  }

  // Remove an event handler
  off(event: string, handler: (data: any) => void) {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event] = this.eventHandlers[event].filter(
        (h) => h !== handler
      );
    }
  }

  // Check if connected
  isConnected() {
    return this.connected;
  }

  // For debugging
  testConnection() {
    if (!this.socket || !this.connected) {
      console.log("WebSocket not connected, can't send test");
      return;
    }

    this.socket.emit(WS_EVENTS.TEST_EVENT, { message: "Hello from client" });
  }
}

// Create a singleton instance
const websocketService = new WebSocketService();

export default websocketService;
