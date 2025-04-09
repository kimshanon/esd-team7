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
  const [googleApi, setGoogleApi] = useState<any>(null);
  
  // Store the current locations for use in callbacks
  const locationRef = useRef({ start: startLocation, end: endLocation });

  // Update locationRef whenever props change
  useEffect(() => {
    locationRef.current = { start: startLocation, end: endLocation };
  }, [startLocation, endLocation]);

  useEffect(() => {
    // Initialize map once
    const initMap = async () => {
      const loader = new Loader({
        apiKey: "AIzaSyDjH28uAStkeoEpvlVqtgt3OJk4_w74iRA",
        version: "weekly",
        libraries: ["geometry", "places"]
      });

      try {
        // Short delay to ensure DOM is ready
        await new Promise(resolve => setTimeout(resolve, 500));
        
        const google = await loader.load();
        setGoogleApi(google);
        
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

          // Wait for map to be fully loaded before proceeding
          google.maps.event.addListenerOnce(mapInstance.current, 'idle', () => {
            console.log("Map fully loaded and ready");
            
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
            
            // Calculate route immediately after map is fully loaded
            calculateRoute(locationRef.current.start, locationRef.current.end);
          });
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

  // Function to calculate route (more reliable as a separate function)
  const calculateRoute = (origin: string, destination: string) => {
    if (!directionsService.current || !directionsRenderer.current || !googleApi) {
      console.log("Map services not ready yet");
      return;
    }

    console.log("Calculating route:", { origin, destination });

    // Create route request
    const request = {
      origin,
      destination,
      travelMode: googleApi.maps.TravelMode.WALKING,
    };

    // Get directions
    directionsService.current.route(request, (result, status) => {
      if (status === "OK" && directionsRenderer.current && result) {
        console.log("Route calculated successfully");
        
        // Need to ensure map is still valid
        if (!mapInstance.current) return;
        
        // Ensure the renderer is attached to the map
        directionsRenderer.current.setMap(mapInstance.current);
        
        // Set the directions
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
        if (mapInstance.current && result.routes[0] && result.routes[0].bounds) {
          mapInstance.current.fitBounds(result.routes[0].bounds);
        }
      } else {
        console.error("Error calculating route:", status);
      }
    });
  };

  // Update route whenever locations change
  useEffect(() => {
    if (isMapInitialized && startLocation && endLocation) {
      console.log("Locations changed, recalculating route");
      calculateRoute(startLocation, endLocation);
    }
  }, [startLocation, endLocation, isMapInitialized]);

  return (
    <div className="w-full h-[400px] rounded-lg overflow-hidden relative">
      <div ref={mapRef} className="w-full h-full" />
      {!isMapInitialized && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 bg-opacity-75">
          <div className="flex flex-col items-center">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500 mb-2"></div>
            <span className="text-gray-700">Loading map...</span>
          </div>
        </div>
      )}
      {estimatedTime && (
        <div className="absolute bottom-4 left-4 bg-gray-800 px-4 py-3 rounded-md shadow-lg z-10">
          <p className="text-sm font-medium text-white">Estimated walking time: <span className="font-bold text-yellow-300">{estimatedTime}</span></p>
        </div>
      )}
    </div>
  );
}