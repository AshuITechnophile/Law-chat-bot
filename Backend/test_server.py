import requests
import sys
import time

def test_backend_health():
    url = "http://localhost:5000/api/health"
    max_retries = 3
    
    print(f"Testing backend connection at {url}...")
    
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                print(f"✓ Backend is running! Status code: {response.status_code}")
                print(f"Response: {response.text}")
                return True
            else:
                print(f"✗ Backend returned status code: {response.status_code}")
                print(f"Response: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"✗ Attempt {attempt}/{max_retries} failed: {str(e)}")
        
        if attempt < max_retries:
            print(f"Retrying in {attempt} seconds...")
            time.sleep(attempt)
    
    print("Could not connect to the backend server.")
    print("Make sure the server is running on port 5000.")
    return False

if __name__ == "__main__":
    test_backend_health() 