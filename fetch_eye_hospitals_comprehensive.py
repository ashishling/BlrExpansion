"""
Comprehensive Eye Hospital Fetcher for Bangalore
Uses multiple strategies to ensure complete coverage:
1. Grid-based searching (divide Bangalore into zones)
2. Multiple keyword variations
3. Text Search API (when available)
4. Deduplication and consolidation
"""

import os
import googlemaps
import pandas as pd
from dotenv import load_dotenv
import time
from math import radians, sin, cos, sqrt, atan2

# Load environment variables
load_dotenv()
API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

if not API_KEY:
    raise ValueError("GOOGLE_MAPS_API_KEY not found in .env file")

# Initialize Google Maps client
gmaps = googlemaps.Client(key=API_KEY)

# Bangalore parameters
BANGALORE_CENTER = (12.9716, 77.5946)
SEARCH_RADIUS = 25000  # 25km radius for Bangalore metro area

# Grid parameters - divide Bangalore into zones for comprehensive coverage
GRID_POINTS = [
    # Central Bangalore
    (12.9716, 77.5946),  # Center
    # North
    (13.0500, 77.5946),
    (13.1200, 77.5946),
    # South
    (12.8900, 77.5946),
    (12.8100, 77.5946),
    # East
    (12.9716, 77.7000),
    (12.9716, 77.8000),
    # West
    (12.9716, 77.4800),
    (12.9716, 77.3800),
    # Northeast
    (13.0500, 77.7000),
    # Northwest
    (13.0500, 77.4800),
    # Southeast
    (12.8900, 77.7000),
    # Southwest
    (12.8900, 77.4800),
]

# Multiple keywords to try
KEYWORDS = [
    "eye hospital",
    "ophthalmology hospital",
    "eye clinic",
    "eye care center",
    "eye institute",
    "cornea hospital",
    "retina hospital",
    "cataract hospital",
]


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers"""
    R = 6371  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c

    return distance


def fetch_hospitals_grid_search(min_reviews=100, search_radius=15000):
    """
    Search for eye hospitals using grid-based approach.
    Divides Bangalore into zones to ensure comprehensive coverage.

    Args:
        min_reviews (int): Minimum number of reviews
        search_radius (int): Radius in meters for each grid point

    Returns:
        pd.DataFrame: Hospital data with deduplication
    """
    all_hospitals = {}  # Use dict with place_id as key for deduplication
    total_requests = 0
    zones_searched = 0

    print("\n" + "="*70)
    print("GRID-BASED SEARCH FOR EYE HOSPITALS")
    print("="*70)
    print(f"Search Strategy: Dividing Bangalore into {len(GRID_POINTS)} zones")
    print(f"Radius per zone: {search_radius}m")
    print(f"Minimum reviews: {min_reviews}")
    print(f"Keywords to try: {len(KEYWORDS)}")
    print("="*70 + "\n")

    for zone_idx, (lat, lon) in enumerate(GRID_POINTS, 1):
        print(f"\n[Zone {zone_idx}/{len(GRID_POINTS)}] Searching around ({lat:.4f}, {lon:.4f})")
        zone_hospitals = 0

        for keyword in KEYWORDS:
            try:
                next_page_token = None
                page_num = 0

                while True:
                    page_num += 1

                    # Search using Nearby Search API
                    places_result = gmaps.places_nearby(
                        location=(lat, lon),
                        radius=search_radius,
                        keyword=keyword,
                        type="hospital",
                        page_token=next_page_token
                    )

                    total_requests += 1

                    if not places_result.get('results'):
                        break

                    # Process results
                    for place in places_result['results']:
                        try:
                            place_id = place['place_id']

                            # Skip if already found
                            if place_id in all_hospitals:
                                continue

                            # Get detailed place info
                            details = gmaps.place(
                                place_id=place_id,
                                fields=['name', 'formatted_address', 'geometry', 'rating',
                                       'user_ratings_total', 'website', 'formatted_phone_number',
                                       'opening_hours']
                            )

                            total_requests += 1

                            place_data = details['result']
                            review_count = place_data.get('user_ratings_total', 0)

                            # Filter by minimum reviews
                            if review_count >= min_reviews:
                                hospital_info = {
                                    'name': place_data.get('name', 'N/A'),
                                    'address': place_data.get('formatted_address', 'N/A'),
                                    'latitude': place_data['geometry']['location']['lat'],
                                    'longitude': place_data['geometry']['location']['lng'],
                                    'rating': place_data.get('rating', None),
                                    'review_count': review_count,
                                    'phone': place_data.get('formatted_phone_number', 'N/A'),
                                    'website': place_data.get('website', 'N/A'),
                                    'place_id': place_id,
                                    'types': place_data.get('types', []),
                                    'zone': zone_idx,
                                    'keyword_found': keyword
                                }

                                all_hospitals[place_id] = hospital_info
                                zone_hospitals += 1

                            # Rate limiting
                            if total_requests % 10 == 0:
                                time.sleep(1)

                        except Exception as e:
                            continue

                    # Check for next page
                    next_page_token = places_result.get('next_page_token')
                    if not next_page_token or page_num >= 3:  # Max 3 pages (60 results)
                        break

                    time.sleep(1)

            except Exception as e:
                continue

        zones_searched += 1
        if zone_hospitals > 0:
            print(f"  ✓ Found {zone_hospitals} new hospitals in this zone")

        # Rate limiting between zones
        time.sleep(0.5)

    print(f"\n✓ Grid search complete: {zones_searched} zones, {len(all_hospitals)} unique hospitals")
    print(f"Total API requests: {total_requests}\n")

    if all_hospitals:
        df = pd.DataFrame(list(all_hospitals.values()))
        df = df.sort_values('review_count', ascending=False)
        return df
    else:
        return pd.DataFrame()


def fetch_hospitals_text_search(min_reviews=100):
    """
    Alternative: Use Text Search API (typically returns more results)
    Note: Text Search returns different result set, complementary to Nearby Search

    Args:
        min_reviews (int): Minimum number of reviews

    Returns:
        pd.DataFrame: Hospital data
    """
    all_hospitals = {}
    total_requests = 0

    print("\n" + "="*70)
    print("TEXT SEARCH FOR EYE HOSPITALS")
    print("="*70)
    print(f"Minimum reviews: {min_reviews}")
    print("="*70 + "\n")

    try:
        for keyword_idx, keyword in enumerate(KEYWORDS, 1):
            print(f"[{keyword_idx}/{len(KEYWORDS)}] Searching for '{keyword}' in Bangalore...")

            try:
                next_page_token = None
                page_num = 0
                keyword_results = 0

                while True:
                    page_num += 1

                    # Text Search API - can return more results
                    search_result = gmaps.places_text(
                        query=f"{keyword} Bangalore",
                        page_token=next_page_token
                    )

                    total_requests += 1

                    if not search_result.get('results'):
                        break

                    for place in search_result['results']:
                        try:
                            # Filter by Bangalore location
                            location = place.get('geometry', {}).get('location', {})
                            lat, lon = location.get('lat'), location.get('lng')

                            # Check if within Bangalore bounds (rough)
                            distance = haversine_distance(
                                BANGALORE_CENTER[0], BANGALORE_CENTER[1], lat, lon
                            )

                            if distance > 50:  # More than 50km away
                                continue

                            place_id = place['place_id']

                            if place_id in all_hospitals:
                                continue

                            # Get detailed info (note: 'types' field not allowed in place details API)
                            details = gmaps.place(
                                place_id=place_id,
                                fields=['name', 'formatted_address', 'geometry', 'rating',
                                       'user_ratings_total', 'website', 'formatted_phone_number',
                                       'opening_hours']
                            )

                            total_requests += 1

                            place_data = details['result']
                            review_count = place_data.get('user_ratings_total', 0)

                            if review_count >= min_reviews:
                                hospital_info = {
                                    'name': place_data.get('name', 'N/A'),
                                    'address': place_data.get('formatted_address', 'N/A'),
                                    'latitude': place_data['geometry']['location']['lat'],
                                    'longitude': place_data['geometry']['location']['lng'],
                                    'rating': place_data.get('rating', None),
                                    'review_count': review_count,
                                    'phone': place_data.get('formatted_phone_number', 'N/A'),
                                    'website': place_data.get('website', 'N/A'),
                                    'place_id': place_id,
                                    'search_method': 'text_search'
                                }

                                all_hospitals[place_id] = hospital_info
                                keyword_results += 1

                            if total_requests % 10 == 0:
                                time.sleep(1)

                        except Exception as e:
                            continue

                    next_page_token = search_result.get('next_page_token')
                    if not next_page_token or page_num >= 2:
                        break

                    time.sleep(1)

                if keyword_results > 0:
                    print(f"  ✓ Found {keyword_results} hospitals for '{keyword}'")

            except Exception as e:
                print(f"  ! Error searching for '{keyword}': {str(e)}")
                continue

    except Exception as e:
        print(f"Text search error: {str(e)}")

    print(f"\n✓ Text search complete: {len(all_hospitals)} unique hospitals")
    print(f"Total API requests: {total_requests}\n")

    if all_hospitals:
        df = pd.DataFrame(list(all_hospitals.values()))
        df = df.sort_values('review_count', ascending=False)
        return df
    else:
        return pd.DataFrame()


def combine_results(grid_df, text_df):
    """Combine results from both search methods, removing duplicates"""
    if grid_df.empty and text_df.empty:
        return pd.DataFrame()

    if grid_df.empty:
        return text_df

    if text_df.empty:
        return grid_df

    # Combine and deduplicate by place_id
    combined = pd.concat([grid_df, text_df]).drop_duplicates(subset=['place_id'], keep='first')
    return combined.sort_values('review_count', ascending=False)


def display_summary(df):
    """Display comprehensive summary"""
    if df.empty:
        print("No hospitals found")
        return

    print("\n" + "="*70)
    print("FINAL RESULTS - EYE HOSPITALS IN BANGALORE")
    print("="*70)
    print(f"Total hospitals found: {len(df)}")
    print(f"All hospitals have 100+ reviews\n")

    print(f"Rating Statistics:")
    print(f"  Average rating: {df['rating'].mean():.2f}/5.0")
    print(f"  Highest rated: {df['rating'].max():.1f}")
    print(f"  Lowest rated: {df['rating'].min():.1f}")

    print(f"\nReview Statistics:")
    print(f"  Total reviews across all hospitals: {df['review_count'].sum():,}")
    print(f"  Average reviews per hospital: {df['review_count'].mean():.0f}")
    print(f"  Median reviews per hospital: {df['review_count'].median():.0f}")

    print(f"\nTop 10 Hospitals by Review Count:")
    for idx, (i, row) in enumerate(df.head(10).iterrows(), 1):
        print(f"  {idx:2d}. {row['name']}")
        print(f"      Reviews: {row['review_count']:,} | Rating: ⭐ {row['rating']}")

    print("="*70 + "\n")


def save_hospitals_to_csv(df, filename='eye_hospitals_bangalore_comprehensive.csv'):
    """Save hospital data to CSV"""
    if not df.empty:
        df.to_csv(filename, index=False)
        print(f"✓ Saved {len(df)} hospitals to {filename}\n")
        return filename
    else:
        print("No data to save")
        return None


if __name__ == "__main__":
    import sys

    # Check command line arguments
    use_grid_only = '--grid-only' in sys.argv
    use_text_only = '--text-only' in sys.argv

    print("\n🔍 COMPREHENSIVE EYE HOSPITAL SEARCH FOR BANGALORE")
    print("=" * 70)

    all_results = []

    # Grid-based search (best for local exhaustive coverage)
    if not use_text_only:
        print("\nPhase 1: Grid-Based Search")
        print("-" * 70)
        grid_hospitals = fetch_hospitals_grid_search(min_reviews=100, search_radius=15000)
        all_results.append(grid_hospitals)

    # Text search (good for finding additional results)
    if not use_grid_only:
        print("\nPhase 2: Text Search")
        print("-" * 70)
        text_hospitals = fetch_hospitals_text_search(min_reviews=100)
        all_results.append(text_hospitals)

    # Combine results
    if len(all_results) == 2:
        final_df = combine_results(all_results[0], all_results[1])
        search_method = "Grid + Text Search"
    elif len(all_results) == 1:
        final_df = all_results[0]
        search_method = "Grid Search" if not use_text_only else "Text Search"
    else:
        final_df = pd.DataFrame()
        search_method = "None"

    # Display results
    if not final_df.empty:
        display_summary(final_df)

        # Save to CSV
        save_hospitals_to_csv(final_df)

        # Display sample
        print("Sample of hospitals found:")
        print(final_df[['name', 'rating', 'review_count', 'address']].head(10).to_string())
    else:
        print("No hospitals found matching criteria")

    print(f"\nSearch Method Used: {search_method}")
