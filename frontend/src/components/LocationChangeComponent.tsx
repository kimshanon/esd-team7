import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import * as API from "@/config/api";

interface Location {
  id: number
  title: string
  address: string
  postal: string
  position: {
    lat: number
    lng: number
  }
}

interface LocationChangeComponentProps {
  currentLocation: string
  onClose: () => void
  onLocationChange: (newLocation: string) => void
  orderId: string
}

const campusLocations: Location[] = [
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
]

// Add Google Maps types
declare global {
  interface Window {
    google: any
    initMap: () => void
  }
}

export default function LocationChangeComponent({
  currentLocation,
  onClose,
  onLocationChange,
  orderId,
}: LocationChangeComponentProps) {
  const [selectionMode, setSelectionMode] = useState(false)
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null)
  const [loading, setLoading] = useState(false)
  const [mapLoaded, setMapLoaded] = useState(false)

  // Refs for Google Maps
  const mapRef = useRef<any>(null)
  const mapContainerRef = useRef<HTMLDivElement>(null)
  const markersRef = useRef<any[]>([])
  const infoWindowRef = useRef<any>(null)
  const locationListRef = useRef<HTMLDivElement>(null)

  // Load Google Maps API
  useEffect(() => {
    // Create a callback that will be called when Google Maps loads
    window.initMap = () => {
      setMapLoaded(true)
    }

    // Skip if already loaded
    if (window.google && window.google.maps) {
      window.initMap()
      return
    }

    // Prevent multiple script loads
    const existingScript = document.querySelector('script[src*="maps.googleapis.com/maps/api"]')
    if (existingScript) {
      // If script exists but not loaded yet, just wait for our callback
      return
    }

    // Create script element
    const googleMapScript = document.createElement("script")
    googleMapScript.src = `https://maps.googleapis.com/maps/api/js?key=AIzaSyDjH28uAStkeoEpvlVqtgt3OJk4_w74iRA&libraries=places&callback=initMap`
    googleMapScript.async = true
    googleMapScript.defer = true

    // Append script to document
    document.head.appendChild(googleMapScript)

    // Cleanup
    return () => {
      // Only cleanup if component unmounts before Google loads
      if (!window.google || !window.google.maps) {
        const script = document.querySelector('script[src*="maps.googleapis.com/maps/api"]')
        if (script && script === googleMapScript) {
          document.head.removeChild(script)
        }
        delete window.initMap
      }
    }
  }, [])

  // Initialize map when API is loaded
  useEffect(() => {
    if (!mapLoaded || !mapContainerRef.current) return

    initializeMap()
  }, [mapLoaded])

  // Update map when selection mode changes
  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return

    if (selectionMode) {
      // Show all markers in selection mode
      markersRef.current.forEach((marker) => {
        marker.setVisible(true)
      })
    } else {
      // Only show selected or current location marker
      updateVisibleMarkers()
    }
  }, [selectionMode, mapLoaded])

  // Update markers when selected location changes
  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return

    updateVisibleMarkers()

    // Scroll to the selected location in the list
    if (selectedLocation && locationListRef.current) {
      const selectedElement = document.getElementById(`location-${selectedLocation.id}`)
      if (selectedElement) {
        selectedElement.scrollIntoView({ behavior: "smooth", block: "nearest" })
      }
    }
  }, [selectedLocation, mapLoaded])

  const initializeMap = () => {
    try {
      // Campus center coordinates (SMU)
      const campusCenter = { lat: 1.2955, lng: 103.8495 }

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
      }

      const map = new window.google.maps.Map(mapContainerRef.current, mapOptions)
      mapRef.current = map

      // Create info window (shared)
      const infoWindow = new window.google.maps.InfoWindow()
      infoWindowRef.current = infoWindow

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
        })

        // Create info window content
        const infoContent = `
          <div style="padding: 8px; max-width: 200px; font-family: system-ui, sans-serif;">
            <h3 style="margin: 0 0 8px 0; font-size: 16px; color: #0f172a;">${location.title}</h3>
            <p style="margin: 0 0 5px 0; font-size: 14px; color: #475569;">${location.address}</p>
            <p style="margin: 0; font-size: 14px; color: #475569;">${location.postal}</p>
          </div>
        `

        // Add click listener
        marker.addListener("click", () => {
          // Close any open info window
          infoWindow.close()

          // Set content and open
          infoWindow.setContent(infoContent)
          infoWindow.open(map, marker)

          // Stop any existing animations on all markers
          markersRef.current.forEach((m) => m.setAnimation(null))

          // Animate this marker
          marker.setAnimation(window.google.maps.Animation.BOUNCE)

          // Stop the animation after a short time
          setTimeout(() => {
            marker.setAnimation(null)
          }, 1500)

          // Select this location
          setSelectedLocation(location)
        })

        // Store location with marker for reference
        marker.locationData = location

        return marker
      })

      // Add click listener to map to close info window
      map.addListener("click", () => {
        infoWindow.close()
      })

      // Show initial marker(s)
      updateVisibleMarkers()
    } catch (error) {
      console.error("Error initializing map:", error)
    }
  }

  const updateVisibleMarkers = () => {
    if (!markersRef.current.length) return

    if (selectionMode) {
      // Show all markers in selection mode
      markersRef.current.forEach((marker) => {
        marker.setVisible(true)
      })
    } else {
      // In non-selection mode, only show the selected or current location
      const locationToShow = selectedLocation || findCurrentLocation()

      markersRef.current.forEach((marker) => {
        // Show marker if it matches the location to show
        const isMatch =
          locationToShow &&
          marker.locationData.position.lat === locationToShow.position.lat &&
          marker.locationData.position.lng === locationToShow.position.lng

        marker.setVisible(isMatch)

        // Center map on the visible marker
        if (isMatch && mapRef.current) {
          mapRef.current.setCenter(marker.getPosition())
          mapRef.current.setZoom(17)
        }
      })
    }
  }

  const findCurrentLocation = (): Location | null => {
    // Try to find a location that matches the current location string
    if (!currentLocation) return null

    // Extract location name from the current location string
    const locationName = currentLocation.split(",")[0]?.trim()

    return campusLocations.find((loc) => locationName && loc.title.includes(locationName)) || campusLocations[0] // Default to first location if not found
  }

  const handleChooseNewLocation = () => setSelectionMode(true)

  const handleCancelSelection = () => {
    setSelectionMode(false)
    setSelectedLocation(null)

    // Close any open info window
    if (infoWindowRef.current) {
      infoWindowRef.current.close()
    }
  }

  const handleSelectLocation = (location: Location) => {
    setSelectedLocation(location)

    // Show info window for the selected location
    if (mapRef.current && markersRef.current && infoWindowRef.current) {
      // Find the marker for this location
      const marker = markersRef.current.find(
        (m) =>
          m.locationData.position.lat === location.position.lat &&
          m.locationData.position.lng === location.position.lng,
      )

      if (marker) {
        // Close any open info window
        infoWindowRef.current.close()

        // Create info window content
        const infoContent = `
          <div style="padding: 8px; max-width: 200px; font-family: system-ui, sans-serif;">
            <h3 style="margin: 0 0 8px 0; font-size: 16px; color: #0f172a;">${location.title}</h3>
            <p style="margin: 0 0 5px 0; font-size: 14px; color: #475569;">${location.address}</p>
            <p style="margin: 0; font-size: 14px; color: #475569;">${location.postal}</p>
          </div>
        `

        // Set content and open
        infoWindowRef.current.setContent(infoContent)
        infoWindowRef.current.open(mapRef.current, marker)

        // Center map on the marker
        mapRef.current.setCenter(marker.getPosition())

        // Animate the marker to make it "pop"
        // First stop any existing animations on all markers
        markersRef.current.forEach((m) => m.setAnimation(null))

        // Then set the animation on the selected marker
        marker.setAnimation(window.google.maps.Animation.BOUNCE)

        // Stop the animation after a short time (1.5 seconds)
        setTimeout(() => {
          marker.setAnimation(null)
        }, 1500)
      }
    }
  }

  // Fix for handleConfirmLocation function in LocationChangeComponent.tsx
  const handleConfirmLocation = async () => {
    if (!selectedLocation || !orderId) return;

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

      // Call the orders API directly - this matches the orders.py endpoint
      const response = await fetch(`${API.ORDER_URL}/orders/${orderId}/location`, {
        method: "PATCH",
        headers: { 
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body: JSON.stringify({
          location: newLocation,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to update location');
      }

      setLoading(false);
      onLocationChange(`${newLocation.address}, ${newLocation.postal}`);
      setSelectionMode(false);
      onClose();
    } catch (err) {
      console.error("API error:", err);
      setLoading(false);
      alert("Failed to update location. Please try again.");
    }
  }

  return (
    <div className="font-sans">
      {/* Google Maps Container */}
      <div ref={mapContainerRef} className="h-[400px] w-full relative">
        {!mapLoaded && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="w-10 h-10 border-4 border-gray-200 border-t-primary rounded-full animate-spin mx-auto mb-2" />
              <p>Loading map...</p>
            </div>
          </div>
        )}
      </div>

      {!selectionMode ? (
        <div className="p-4">
          <h4 className="text-sm text-gray-500 mb-2">Current Delivery Location:</h4>
          <p className="mb-4">{currentLocation}</p>
          <Button onClick={handleChooseNewLocation} className="w-full">
            Choose New Location
          </Button>
        </div>
      ) : (
        <>
          <div className="p-4 border-b">
            <h4 className="text-sm text-gray-500 mb-2">Selected Location:</h4>
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
          </div>

          <div ref={locationListRef} className="p-4 max-h-[200px] overflow-y-auto">
            <h4 className="text-sm text-gray-500 mb-3">Select a new location:</h4>
            <div className="flex flex-col gap-2">
              {campusLocations.map((location) => (
                <div
                  id={`location-${location.id}`}
                  key={location.id}
                  onClick={() => handleSelectLocation(location)}
                  className={`p-3 rounded-lg cursor-pointer transition-all ${
                    selectedLocation?.id === location.id
                      ? "bg-emerald-50 border border-emerald-200"
                      : "bg-gray-50 border border-gray-200 hover:bg-gray-100"
                  }`}
                >
                  <div className="flex justify-between">
                    <div>
                      <div
                        className={`font-medium mb-1 ${
                          selectedLocation?.id === location.id ? "text-emerald-700" : "text-gray-800"
                        }`}
                      >
                        {location.title}
                      </div>
                      <div className="text-sm text-gray-500">
                        {location.address}, {location.postal}
                      </div>
                    </div>
                    {selectedLocation?.id === location.id && (
                      <div className="text-emerald-500 text-lg flex items-center">✓</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="p-4 border-t flex gap-3">
            <Button onClick={handleConfirmLocation} disabled={!selectedLocation || loading} className="flex-1">
              {loading ? "Updating..." : "Confirm New Location"}
            </Button>
            <Button onClick={handleCancelSelection} variant="outline" className="flex-1">
              Cancel
            </Button>
          </div>
        </>
      )}
    </div>
  )
}