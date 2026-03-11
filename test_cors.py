import requests

def test_cors():
    url = "http://localhost:5000/api/login"
    origins = [
        "https://isms-frontend.onrender.com",
        "http://localhost:5173",
        "http://localhost:3000"
    ]
    
    for origin in origins:
        print(f"\nTesting Origin: {origin}")
        
        # Test OPTIONS preflight
        headers = {
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        try:
            response = requests.options(url, headers=headers)
            print(f"OPTIONS Status: {response.status_code}")
            print(f"Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin')}")
            print(f"Access-Control-Allow-Credentials: {response.headers.get('Access-Control-Allow-Credentials')}")
            
            # Test actual POST request
            headers = {"Origin": origin, "Content-Type": "application/json"}
            response = requests.post(url, headers=headers, json={})
            print(f"POST Status: {response.status_code}")
            print(f"Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin')}")
            
        except requests.exceptions.ConnectionError:
            print("Server is not running. Please start the Flask server locally to run this test.")
            return

if __name__ == "__main__":
    test_cors()
