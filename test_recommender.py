import requests
import json

def test_taiwan_mirror():
    # London coordinates
    lat, lon = 51.5074456, -0.1277653
    radius_meters = 5000
    
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="hospital"](around:{radius_meters},{lat},{lon});
      way["amenity"="hospital"](around:{radius_meters},{lat},{lon});
      relation["amenity"="hospital"](around:{radius_meters},{lat},{lon});
    );
    out center;
    """
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    try:
        response = requests.post("https://overpass.nchc.org.tw/api/interpreter", data={"data": query}, headers=headers, timeout=25)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"SUCCESS! Found {len(data.get('elements', []))} elements in London.")
        if len(data.get('elements', [])) > 0:
            print(f"Sample: {data.get('elements')[0].get('tags', {}).get('name')}")
    except Exception as ex:
        print(f"Exception: {ex}")

if __name__ == "__main__":
    test_taiwan_mirror()
