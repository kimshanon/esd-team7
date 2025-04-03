"use client"

import { useState } from "react"

import { GoogleMap, Marker, LoadScript } from "@react-google-maps/api"

const GOOGLE_MAPS_API_KEY = "AIzaSyDjH28uAStkeoEpvlVqtgt3OJk4_w74iRA"  // Replace with your actual API key

// Sample campus locations data
const campusLocations = [
  {
    id: 1,
    title: "SMU Connexion",
    address: "40 Stamford Rd",
    postal: "Singapore 178908",
    position: { lat: 1.2952469253940524, lng: 103.84974982645213 },
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
    position: { lat: 1.2958980541549707, lng: 103.84971077997338 },
  },
  {
    id: 4,
    title: "SMU Yong Pung How School of Law",
    address: "55 Armenian St",
    postal: "Singapore 179943",
    position: { lat: 1.2949679879834028, lng: 103.84943256824556 },
  },
  {
    id: 5,
    title: "Student Union Building",
    address: "Room 203",
    postal: "Singapore 123456",
    position: { lat: 1.2955, lng: 103.8495 },
  },
]

function LocationChangeComponent({ currentLocation, onClose, onLocationChange }) {
  const [selectionMode, setSelectionMode] = useState(false)
  const [selectedLocation, setSelectedLocation] = useState(null)

  const handleChooseNewLocation = () => {
    setSelectionMode(true)
  }

  const handleCancelSelection = () => {
    setSelectionMode(false)
    setSelectedLocation(null)
  }

  const handleConfirmLocation = () => {
    if (selectedLocation) {
      const newLocationString = `${selectedLocation.title}, ${selectedLocation.address}, ${selectedLocation.postal}`
      onLocationChange(newLocationString)
    }
  }

  const handleSelectLocation = (location) => {
    setSelectedLocation(location)
  }

  return (
    <div id="map-container">
      <div className="map-dialog">
        <div className="map-header">
          <div className="map-title">Change Delivery Location</div>
          <button className="map-close" onClick={onClose}>
            ×
          </button>
        </div>

        {/* Map placeholder - in a real app, this would be a Google Map */}
        <div id="map">
          <div className="map-placeholder">
            <div>Map would be displayed here</div>
            <p>In a real implementation, this would be integrated with Google Maps API</p>
          </div>
        </div>

        {!selectionMode ? (
          <div id="current-location-box">
            <h4>Current Delivery Location:</h4>
            <p id="current-delivery-location">{currentLocation}</p>
            <button
              id="choose-new-location-btn"
              className="action-button change-location-button"
              onClick={handleChooseNewLocation}
            >
              Choose New Location
            </button>
          </div>
        ) : (
          <div id="selection-box">
            <p>
              Selected Location:{" "}
              <span id="selected-location">
                {selectedLocation
                  ? `${selectedLocation.title}, ${selectedLocation.address}, ${selectedLocation.postal}`
                  : "None selected"}
              </span>
            </p>
            <div className="button-container">
              <button
                id="confirm-btn"
                className="action-button change-location-button"
                onClick={handleConfirmLocation}
                disabled={!selectedLocation}
              >
                Confirm New Location
              </button>
              <button id="cancel-selection-btn" className="action-button cancel-button" onClick={handleCancelSelection}>
                Cancel
              </button>
            </div>
          </div>
        )}

        {selectionMode && (
          <div className="location-list">
            <h4>Select a new location:</h4>
            <div className="location-options">
              {campusLocations.map((location) => (
                <div
                  key={location.id}
                  className={`location-option ${selectedLocation?.id === location.id ? "selected" : ""}`}
                  onClick={() => handleSelectLocation(location)}
                >
                  <div className="location-title">{location.title}</div>
                  <div className="location-address">
                    {location.address}, {location.postal}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default LocationChangeComponent

