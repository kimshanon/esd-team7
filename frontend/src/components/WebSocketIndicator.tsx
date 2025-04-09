import { useEffect, useState } from "react";
import { Wifi, WifiOff } from "lucide-react";
import websocketService, { WS_EVENTS } from "@/services/websocketService";

export default function WebSocketIndicator() {
  const [connected, setConnected] = useState(false);
  const [eventCount, setEventCount] = useState(0);

  useEffect(() => {
    // Check initial connection status
    setConnected(websocketService.isConnected());

    // Listen for any WebSocket event to track activity
    const handleEvent = () => {
      setEventCount((prev) => prev + 1);
    };

    // Add event listeners for common events
    websocketService.on(WS_EVENTS.ORDER_TAKEN, handleEvent);
    websocketService.on(WS_EVENTS.PICKER_UPDATE, handleEvent);
    websocketService.on(WS_EVENTS.ORDER_WAITING, handleEvent);

    // Set up periodic checking
    const interval = setInterval(() => {
      setConnected(websocketService.isConnected());
    }, 5000);

    // Clean up interval and event listeners
    return () => {
      clearInterval(interval);
      websocketService.off(WS_EVENTS.ORDER_TAKEN, handleEvent);
      websocketService.off(WS_EVENTS.PICKER_UPDATE, handleEvent);
      websocketService.off(WS_EVENTS.ORDER_WAITING, handleEvent);
    };
  }, []);

  return (
    <div className="fixed bottom-4 right-4 z-50 p-2 bg-background border rounded-full shadow-md">
      <div
        title={`WebSocket ${
          connected ? "Connected" : "Disconnected"
        } - Events: ${eventCount}`}
      >
        {connected ? (
          <Wifi className="h-5 w-5 text-green-500" />
        ) : (
          <WifiOff className="h-5 w-5 text-red-500" />
        )}
      </div>
    </div>
  );
}
