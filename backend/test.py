import requests
import json

# Set the base URL for the Kong Admin API
KONG_API_URL = "http://localhost:8001"

# Define the services and their routes
services_data = [
    {
        "service_name": "customer-service",
        "url": "http://customer-service:5000",
        "routes": [
            {
                "name": "customer-route",
                "paths": ["/api/customer"],
                "strip_path": True,
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
            }
        ]
    },
    {
        "service_name": "picker-service",
        "url": "http://picker-service:5001",
        "routes": [
            {
                "name": "picker-route",
                "paths": ["/api/picker"],
                "strip_path": True,
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
            }
        ]
    },
    {
        "service_name": "stall-service",
        "url": "http://stall-service:5002",
        "routes": [
            {
                "name": "stall-route",
                "paths": ["/api/stall"],
                "strip_path": True,
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
            }
        ]
    },
    {
        "service_name": "order-service",
        "url": "http://order-service:5003",
        "routes": [
            {
                "name": "order-route",
                "paths": ["/api/order"],
                "strip_path": True,
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
            }
        ]
    },
    {
        "service_name": "payment-service",
        "url": "http://payment-service:5004",
        "routes": [
            {
                "name": "payment-route",
                "paths": ["/api/payment"],
                "strip_path": True,
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
            }
        ]
    },
    {
        "service_name": "assign-picker-service",
        "url": "http://assign-picker-service:5005",
        "routes": [
            {
                "name": "assign-picker-route",
                "paths": ["/api/assign-picker"],
                "strip_path": True,
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
            }
        ]
    },
    {
        "service_name": "calc-payment-service",
        "url": "http://calc-payment-service:5009",
        "routes": [
            {
                "name": "credit-route",
                "paths": ["/api/credit"],
                "strip_path": True,
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
            }
        ]
    },
    {
        "service_name": "update-location-service",
        "url": "http://update-location-service:5002",
        "routes": [
            {
                "name": "location-route",
                "paths": ["/api/location"],
                "strip_path": True,
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
            }
        ]
    },
    {
        "service_name": "cancellation-service",
        "url": "http://cancellation-service:5003",
        "routes": [
            {
                "name": "cancellation-route",
                "paths": ["/api/cancellation"],
                "strip_path": True,
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
            }
        ]
    }
]

def create_service(service_name, url):
    service_data = {
        "name": service_name,
        "url": url
    }
    response = requests.post(f"{KONG_API_URL}/services", json=service_data)
    if response.status_code == 201:
        print(f"Service '{service_name}' created successfully!")
    else:
        print(f"Failed to create service '{service_name}': {response.text}")

def create_route(service_name, route_data):
    route_url = f"{KONG_API_URL}/services/{service_name}/routes"
    response = requests.post(route_url, json=route_data)
    if response.status_code == 201:
        print(f"Route '{route_data['name']}' created successfully for service '{service_name}'!")
    else:
        print(f"Failed to create route '{route_data['name']}' for service '{service_name}': {response.text}")

def main():
    for service in services_data:
        service_name = service["service_name"]
        url = service["url"]
        
        # Create the service
        create_service(service_name, url)

        # Create the routes for the service
        for route in service["routes"]:
            create_route(service_name, route)

if __name__ == "__main__":
    main()
