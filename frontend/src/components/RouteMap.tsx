import { useEffect, useRef, useState } from "react";
import { Loader } from "@googlemaps/js-api-loader";

interface RouteMapProps {
  startLocation: string;
  endLocation: string;
  onRouteCalculated?: (duration: string) => void;
}

export default function RouteMap({ startLocation, endLocation, onRouteCalculated }: RouteMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<google.maps.Map | null>(null);
  const directionsService = useRef<google.maps.DirectionsService | null>(null);
  const directionsRenderer = useRef<google.maps.DirectionsRenderer | null>(null);
  const [estimatedTime, setEstimatedTime] = useState<string>("");
  const [isMapInitialized, setIsMapInitialized] = useState<boolean>(false);

  useEffect(() => {
    // Initialize map once
    const initMap = async () => {
      const loader = new Loader({
        apiKey: "AIzaSyDjH28uAStkeoEpvlVqtgt3OJk4_w74iRA",
        version: "weekly",
        libraries: ["geometry", "places"]
      });

      try {
        const google = await loader.load();
        
        // Initialize map
        if (mapRef.current && !mapInstance.current) {
          mapInstance.current = new google.maps.Map(mapRef.current, {
            center: { lat: 1.2955, lng: 103.8495 }, // SMU center
            zoom: 15,
            mapTypeControl: false,
            streetViewControl: false,
            fullscreenControl: false,
            zoomControl: true,
          });

          // Initialize directions service and renderer
          directionsService.current = new google.maps.DirectionsService();
          directionsRenderer.current = new google.maps.DirectionsRenderer({
            map: mapInstance.current,
            suppressMarkers: false,
            polylineOptions: {
              strokeColor: "#2563eb",
              strokeWeight: 5,
            },
          });
          
          // Set map as initialized
          setIsMapInitialized(true);
          console.log("Map initialized successfully");
        }
      } catch (error) {
        console.error("Error initializing Google Maps:", error);
      }
    };

    initMap();

    // Cleanup
    return () => {
      if (directionsRenderer.current) {
        directionsRenderer.current.setMap(null);
      }
    };
  }, []); // Empty dependency array means this only runs once

  // Update route whenever locations change or map is initialized
  useEffect(() => {
    const updateRoute = async () => {
      if (!isMapInitialized || !directionsService.current || !directionsRenderer.current || !mapInstance.current) {
        console.log("Map not initialized yet, will try again when ready");
        return;
      }

      console.log("Updating route with:", { startLocation, endLocation });

      // Create route request
      const request = {
        origin: startLocation,
        destination: endLocation,
        travelMode: google.maps.TravelMode.WALKING,
      };

      // Get directions
      directionsService.current.route(request, (result, status) => {
        if (status === "OK" && directionsRenderer.current && result) {
          console.log("Route calculated successfully");
          directionsRenderer.current.setDirections(result);
          
          // Extract and display the duration
          if (result.routes[0] && result.routes[0].legs[0]) {
            const duration = result.routes[0].legs[0].duration?.text || "Unknown";
            setEstimatedTime(duration);
            
            // Call the callback if provided
            if (onRouteCalculated) {
              onRouteCalculated(duration);
            }
          }
          
          // Fit map to show the entire route
          const bounds = new google.maps.LatLngBounds();
          result.routes[0].bounds.getNorthEast();
          result.routes[0].bounds.getSouthWest();
          mapInstance.current?.fitBounds(result.routes[0].bounds);
        } else {
          console.error("Error calculating route:", status);
        }
      });
    };

    if (startLocation && endLocation && isMapInitialized) {
      console.log("Attempting to update route with initialized map");
      updateRoute();
    }
  }, [startLocation, endLocation, onRouteCalculated, isMapInitialized]);

  return (
    <div className="w-full h-[400px] rounded-lg overflow-hidden relative">
      <div ref={mapRef} className="w-full h-full" />
      {estimatedTime && (
        <div className="absolute bottom-4 left-4 bg-gray-800 px-4 py-3 rounded-md shadow-lg z-10">
          <p className="text-sm font-medium text-white">Estimated walking time: <span className="font-bold text-yellow-300">{estimatedTime}</span></p>
        </div>
      )}
    </div>
  );
} 