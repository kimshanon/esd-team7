/// <reference types="@types/google.maps" />

import * as API from "@/config/api";
import { useState, useEffect, useRef } from "react";
import { ArrowLeft, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
// import { Separator } from "@/components/ui/separator";
// import { ScrollArea } from "@/components/ui/scroll-area";

// Define TypeScript interfaces
interface LocationData {
  id: number;
  title: string;
  address: string;
  postal: string;
  position: {
    lat: number;
    lng: number;
  };
}

interface LocationChangeProps {
  currentLocation: string;
  onClose: () => void;
  onLocationChange: (location: string) => void;
  orderId?: string; // Make this optional
}

interface GoogleMapMarker extends google.maps.Marker {
  locationData?: LocationData;
}

const campusLocations: LocationData[] = [
  {
    id: 1,
    title: "SMU Connexion",
    address: "40 Stamford Rd",
    postal: "Singapore 178908",
    position: { lat: 1.2952279507976274, lng: 103.8496330448519 },
  },
  {
    id: 2,
    title: "SMU Lee Kong Chian School of Business",
    address: "50 Stamford Rd",
    postal: "Singapore 178899",
    position: { lat: 1.2954025541766494, lng: 103.85071292943596 },
  },
  {
    id: 3,
    title: "SMU School of Accountancy",
    address: "60 Stamford Rd",
    postal: "Singapore 178900",
    position: { lat: 1.2959253732909164, lng: 103.8497992708802 },
  },
  {
    id: 4,
    title: "SMU Yong Pung How School of Law",
    address: "55 Armenian St",
    postal: "Singapore 179943",
    position: { lat: 1.2948868842764918, lng: 103.84949662195385 },
  },
  {
    id: 5,
    title: "SMU Campus Green",
    address: "91 Stamford Rd",
    postal: "Singapore 178896",
    position: { lat: 1.2968378642124887, lng: 103.84953104246888 },
  },
  {
    id: 6,
    title: "SMU School of Computing and Information Systems",
    address: "80 Stamford Rd",
    postal: "Singapore 178902",
    position: { lat: 1.297597444236072, lng: 103.84942955991028 },
  },
  {
    id: 7,
    title: "SMU School of Economics",
    address: "90 Stamford Rd",
    postal: "Singapore 178903",
    position: { lat: 1.2976217036188233, lng: 103.84892371534994 },
  },
  {
    id: 8,
    title: "SMU School of Social Sciences & College of Integrative Studies",
    address: "10 Canning Rise",
    postal: "Singapore 179873",
    position: { lat: 1.294887847140721, lng: 103.84840586729175 },
  },
];

function LocationChangeComponent({
  currentLocation,
//   onClose,
  onLocationChange,
  orderId,
}: LocationChangeProps) {
  const [selectionMode, setSelectionMode] = useState<boolean>(false);
  const [selectedLocation, setSelectedLocation] = useState<LocationData | null>(
    null
  );
  const [loading, setLoading] = useState<boolean>(false);
  const [mapLoaded, setMapLoaded] = useState<boolean>(false);

  // Refs for Google Maps
  const mapRef = useRef<google.maps.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const markersRef = useRef<GoogleMapMarker[]>([]);
  const infoWindowRef = useRef<google.maps.InfoWindow | null>(null);
  const locationListRef = useRef<HTMLDivElement | null>(null);

  // Load Google Maps API
  useEffect(() => {
    // Skip if already loaded
    if (window.google && window.google.maps) {
      setMapLoaded(true);
      return;
    }

    // Create script element
    const googleMapScript = document.createElement("script");
    googleMapScript.src = `https://maps.googleapis.com/maps/api/js?key=AIzaSyDjH28uAStkeoEpvlVqtgt3OJk4_w74iRA&libraries=places`;
    googleMapScript.async = true;
    googleMapScript.defer = true;

    // Define callback function for when the script loads
    googleMapScript.onload = () => {
      setMapLoaded(true);
    };

    // Append script to document
    document.head.appendChild(googleMapScript);

    // Cleanup
    return () => {
      const script = document.querySelector(
        `script[src*="maps.googleapis.com/maps/api"]`
      );
      if (script) {
        document.head.removeChild(script);
      }
    };
  }, []);

  // Initialize map when API is loaded
  useEffect(() => {
    if (!mapLoaded || !mapContainerRef.current) return;

    initializeMap();
  }, [mapLoaded]);

  // Update map when selection mode changes
  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return;

    if (selectionMode) {
      // Show all markers in selection mode
      markersRef.current.forEach((marker) => {
        marker.setVisible(true);
      });
    } else {
      // Only show selected or current location marker
      updateVisibleMarkers();
    }
  }, [selectionMode, mapLoaded]);

  // Update markers when selected location changes
  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return;

    updateVisibleMarkers();

    // Scroll to the selected location in the list
    if (selectedLocation && locationListRef.current) {
      const selectedElement = document.getElementById(
        `location-${selectedLocation.id}`
      );
      if (selectedElement) {
        selectedElement.scrollIntoView({
          behavior: "smooth",
          block: "nearest",
        });
      }
    }
  }, [selectedLocation, mapLoaded]);

  const initializeMap = () => {
    try {
      if (!window.google || !window.google.maps) return;

      // Campus center coordinates (SMU)
      const campusCenter = { lat: 1.2955, lng: 103.8495 };

      // Create map
      const mapOptions = {
        zoom: 17,
        center: campusCenter,
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: false,
        zoomControl: true,
        styles: [
          {
            featureType: "poi.business",
            stylers: [{ visibility: "off" }],
          },
          {
            featureType: "transit",
            elementType: "labels.icon",
            stylers: [{ visibility: "off" }],
          },
        ],
      };

      const map = new window.google.maps.Map(
        mapContainerRef.current!,
        mapOptions
      );
      mapRef.current = map;

      // Create info window (shared)
      const infoWindow = new window.google.maps.InfoWindow();
      infoWindowRef.current = infoWindow;

      // Create markers for each location
      markersRef.current = campusLocations.map((location) => {
        const marker = new window.google.maps.Marker({
          position: location.position,
          map: map,
          title: location.title,
          animation: window.google.maps.Animation.DROP,
          visible: false, // Initially hidden
          icon: {
            path: window.google.maps.SymbolPath.CIRCLE,
            scale: 10,
            fillColor: "#ef4444", // Red color
            fillOpacity: 1,
            strokeWeight: 2,
            strokeColor: "#ffffff",
          },
        }) as GoogleMapMarker;

        // Create info window content
        const infoContent = `
          <div class="p-2 max-w-[200px] font-sans">
            <h3 class="m-0 mb-2 text-base font-medium text-slate-900">${location.title}</h3>
            <p class="m-0 mb-1 text-sm text-slate-600">${location.address}</p>
            <p class="m-0 text-sm text-slate-600">${location.postal}</p>
          </div>
        `;

        // Add click listener
        marker.addListener("click", () => {
          // Close any open info window
          infoWindow.close();

          // Set content and open
          infoWindow.setContent(infoContent);
          infoWindow.open(map, marker);

          // Stop any existing animations on all markers
          markersRef.current.forEach((m) => m.setAnimation(null));

          // Animate this marker
          marker.setAnimation(window.google.maps.Animation.BOUNCE);

          // Stop the animation after a short time
          setTimeout(() => {
            marker.setAnimation(null);
          }, 1500);

          // Select this location
          setSelectedLocation(location);
        });

        // Store location with marker for reference
        marker.locationData = location;

        return marker;
      });

      // Add click listener to map to close info window
      map.addListener("click", () => {
        infoWindow.close();
      });

      // Show initial marker(s)
      updateVisibleMarkers();
    } catch (error) {
      console.error("Error initializing map:", error);
    }
  };

  const updateVisibleMarkers = () => {
    if (!markersRef.current.length) return;

    if (selectionMode) {
      // Show all markers in selection mode
      markersRef.current.forEach((marker) => {
        marker.setVisible(true);
      });
    } else {
      // In non-selection mode, only show the selected or current location
      const locationToShow = selectedLocation || findCurrentLocation();

      markersRef.current.forEach((marker) => {
        // Show marker if it matches the location to show
        const isMatch =
          locationToShow &&
          marker.locationData?.position.lat === locationToShow.position.lat &&
          marker.locationData?.position.lng === locationToShow.position.lng;

        marker.setVisible(!!isMatch);

        // Center map on the visible marker
        if (isMatch && mapRef.current) {
          mapRef.current.setCenter(marker.getPosition()!);
          mapRef.current.setZoom(17);
        }
      });
    }
  };

  const findCurrentLocation = (): LocationData | null => {
    // Try to find a location that matches the current location string
    if (!currentLocation) return null;

    // Extract location name from the current location string
    const locationName = currentLocation.split(",")[0]?.trim();

    return (
      campusLocations.find(
        (loc) => locationName && loc.title.includes(locationName)
      ) || campusLocations[0]
    ); // Default to first location if not found
  };

  const handleChooseNewLocation = () => setSelectionMode(true);

  const handleCancelSelection = () => {
    setSelectionMode(false);
    setSelectedLocation(null);

    // Close any open info window
    if (infoWindowRef.current) {
      infoWindowRef.current.close();
    }
  };

  const handleSelectLocation = (location: LocationData) => {
    setSelectedLocation(location);

    // Show info window for the selected location
    if (mapRef.current && markersRef.current && infoWindowRef.current) {
      // Find the marker for this location
      const marker = markersRef.current.find(
        (m) =>
          m.locationData?.position.lat === location.position.lat &&
          m.locationData?.position.lng === location.position.lng
      );

      if (marker) {
        // Close any open info window
        infoWindowRef.current.close();

        // Create info window content
        const infoContent = `
          <div class="p-2 max-w-[200px] font-sans">
            <h3 class="m-0 mb-2 text-base font-medium text-slate-900">${location.title}</h3>
            <p class="m-0 mb-1 text-sm text-slate-600">${location.address}</p>
            <p class="m-0 text-sm text-slate-600">${location.postal}</p>
          </div>
        `;

        // Set content and open
        infoWindowRef.current.setContent(infoContent);
        infoWindowRef.current.open(mapRef.current, marker);

        // Center map on the marker
        mapRef.current.setCenter(marker.getPosition()!);

        // Animate the marker to make it "pop"
        // First stop any existing animations on all markers
        markersRef.current.forEach((m) => m.setAnimation(null));

        // Then set the animation on the selected marker
        marker.setAnimation(window.google.maps.Animation.BOUNCE);

        // Stop the animation after a short time (1.5 seconds)
        setTimeout(() => {
          marker.setAnimation(null);
        }, 1500);
      }
    }
  };

  // Update this method to handle both order updates and direct selection
  const handleConfirmLocation = async () => {
    if (!selectedLocation) return;

    if (orderId) {
      // Order update flow - leave this as is
      const newLocation = {
        address: selectedLocation.title,
        coordinates: {
          lat: selectedLocation.position.lat,
          lng: selectedLocation.position.lng,
        },
        postal: selectedLocation.postal,
      };

      try {
        setLoading(true);
        const response = await fetch(
          `${API.ORDER_URL}/orders/${orderId}/location`,
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              location: newLocation,
            }),
          }
        );

        const result = await response.json();
        setLoading(false);

        if (response.ok) {
          onLocationChange(`${newLocation.address}, ${newLocation.postal}`);
          setSelectionMode(false);
          alert(`Location updated to ${newLocation.address}`);
        } else {
          alert(`Error: ${result.message}`);
        }
      } catch (err) {
        console.error("PATCH error:", err);
        setLoading(false);
        alert("Unexpected error occurred. Please try again later.");
      }
    } else {
      // Direct selection flow for cart page
      const formattedLocation = `${selectedLocation.title}, ${selectedLocation.postal}`;
      onLocationChange(formattedLocation);
    }
  };

  return (
    <div className="font-sans w-full max-h-[90vh] flex flex-col">
      <Card className="w-full overflow-hidden shadow-none border-0 gap-0 py-0">
        <CardHeader className="flex flex-row items-center justify-between px-4 py-3 border-b">
          <CardTitle className="text-lg flex items-center">
            {selectionMode && (
              <Button
                variant="ghost"
                size="icon"
                className="mr-2"
                onClick={handleCancelSelection}
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
            )}
            Choose Delivery Location
          </CardTitle>
          {/* <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="h-8 w-8"
          >
            <X className="h-4 w-4" />
          </Button> */}
        </CardHeader>

        {/* Google Maps Container - fixed height */}
        <div
          ref={mapContainerRef}
          className="h-[300px] w-full bg-gray-100 relative flex-shrink-0"
        >
          {!mapLoaded && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
              <div className="text-center">
                <div className="w-10 h-10 border-4 border-gray-200 border-t-blue-500 rounded-full animate-spin mx-auto mb-2"></div>
                <p>Loading map...</p>
              </div>
            </div>
          )}
        </div>

        {!selectionMode ? (
          <CardContent className="p-4 overflow-auto">
            <h4 className="mb-2 text-sm text-gray-500">
              Current Delivery Location:
            </h4>
            <p className="mb-4">{currentLocation || "None selected"}</p>
            <Button className="w-full" onClick={handleChooseNewLocation}>
              Choose New Location
            </Button>
          </CardContent>
        ) : (
          <div className="flex flex-col flex-1 overflow-hidden">
            <CardContent className="p-4 border-b">
              <h4 className="mb-2 text-sm text-gray-500">Selected Location:</h4>
              {selectedLocation ? (
                <div>
                  <p className="font-medium mb-1">{selectedLocation.title}</p>
                  <p className="text-sm text-gray-500">
                    {selectedLocation.address}, {selectedLocation.postal}
                  </p>
                </div>
              ) : (
                <p className="italic text-gray-400">None selected</p>
              )}
            </CardContent>

            <div className="overflow-auto flex-1 p-4 max-h-[200px]">
              <h4 className="mb-3 text-sm text-gray-500">
                Select a new location:
              </h4>
              <div className="flex flex-col gap-2" ref={locationListRef}>
                {campusLocations.map((location) => (
                  <div
                    id={`location-${location.id}`}
                    key={location.id}
                    className={`p-3 rounded-md cursor-pointer transition-all ${
                      selectedLocation?.id === location.id
                        ? "bg-emerald-50 border border-emerald-200"
                        : "bg-gray-50 border border-gray-200 hover:bg-gray-100"
                    }`}
                    onClick={() => handleSelectLocation(location)}
                  >
                    <div className="flex justify-between">
                      <div>
                        <div
                          className={`font-medium mb-1 ${
                            selectedLocation?.id === location.id
                              ? "text-emerald-700"
                              : "text-gray-800"
                          }`}
                        >
                          {location.title}
                        </div>
                        <div className="text-sm text-gray-500">
                          {location.address}, {location.postal}
                        </div>
                      </div>
                      {selectedLocation?.id === location.id && (
                        <div className="text-emerald-500 flex items-center">
                          <Check className="h-5 w-5" />
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <CardFooter className="p-4 border-t flex gap-3 flex-shrink-0">
              <Button
                variant="default"
                className="flex-1"
                onClick={handleConfirmLocation}
                disabled={!selectedLocation || loading}
              >
                {loading ? "Updating..." : "Confirm New Location"}
              </Button>
              <Button
                variant="outline"
                className="flex-1"
                onClick={handleCancelSelection}
              >
                Cancel
              </Button>
            </CardFooter>
          </div>
        )}
      </Card>
    </div>
  );
}

export default LocationChangeComponent;
