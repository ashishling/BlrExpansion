"""
Simple API Test Script - Verify Google Maps API is working
"""

import os
import googlemaps
from dotenv import load_dotenv

# Load API key
load_dotenv()
API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

print("="*70)
print("GOOGLE MAPS API TEST")
print("="*70)

# Check if key exists
if not API_KEY:
    print("❌ ERROR: GOOGLE_MAPS_API_KEY not found in .env file")
    exit(1)

print(f"✓ API Key loaded: {API_KEY[:20]}...")
print()

# Initialize client
try:
    gmaps = googlemaps.Client(key=API_KEY)
    print("✓ Google Maps client initialized")
except Exception as e:
    print(f"❌ Failed to initialize client: {e}")
    exit(1)

print()
print("Testing API with a simple nearby search...")
print("-" * 70)

try:
    # Test with a simple nearby search
    result = gmaps.places_nearby(
        location=(12.9716, 77.5946),  # Bangalore center
        radius=5000,  # 5km radius
        keyword="eye hospital"
    )

    print(f"✓ API Call successful!")
    print(f"  Status: {result.get('status', 'Unknown')}")
    print(f"  Results found: {len(result.get('results', []))}")

    if result.get('status') == 'OK':
        print(f"\n✓✓✓ API IS WORKING! ✓✓✓")
        print()
        print("Hospital results from Bangalore:")
        for i, place in enumerate(result.get('results', [])[:5], 1):
            print(f"  {i}. {place['name']}")

        # Check if there are more results
        if result.get('next_page_token'):
            print(f"\n  ℹ️ More results available (has next_page_token)")

        print()
        print("="*70)
        print("SUCCESS: API is working correctly!")
        print("You can now run the comprehensive search:")
        print("  python fetch_eye_hospitals_comprehensive.py --grid-only")
        print("="*70)

    elif result.get('status') == 'ZERO_RESULTS':
        print(f"\n⚠️ API is working but no results found for eye hospitals")
        print("This might be a search parameter issue")

    else:
        print(f"\n⚠️ Unexpected status: {result.get('status')}")
        print(f"Response: {result}")

except Exception as e:
    print(f"❌ API Call failed: {e}")
    print()
    print("Possible reasons:")
    print("  1. Billing not enabled on Google Cloud Project")
    print("  2. Places API not enabled in Google Cloud Console")
    print("  3. API key is invalid or expired")
    print("  4. API key restricted to certain APIs")
    exit(1)
