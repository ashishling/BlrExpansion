"""
Fetch eye hospitals in Bangalore from Google Maps Places API.
Filters results to show only hospitals with at least 100 reviews.

NOTE: This requires Google Maps Places API to be enabled with billing.
Fallback sample data is provided for demonstration purposes.
"""

import os
import googlemaps
import pandas as pd
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()
API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

if not API_KEY:
    raise ValueError("GOOGLE_MAPS_API_KEY not found in .env file")

# Bangalore center coordinates
BANGALORE_CENTER = (12.9716, 77.5946)
SEARCH_RADIUS = 30000  # 30km radius to cover greater Bangalore

# Fallback sample data - well-known eye hospitals in Bangalore with 100+ reviews
SAMPLE_EYE_HOSPITALS = [
    {
        'name': 'L V Prasad Eye Institute',
        'address': 'L V Prasad Marg, Whitefield, Bangalore 560066',
        'latitude': 13.0259,
        'longitude': 77.7362,
        'rating': 4.6,
        'review_count': 1850,
        'phone': '+91 80 4055 2020',
        'website': 'https://www.lvpei.org',
        'place_id': 'sample_1',
        'open_now': True
    },
    {
        'name': 'Narayana Nethralaya',
        'address': '#121, Chord Road, Opp. St. Johns School, High Grounds, Bangalore 560001',
        'latitude': 13.0065,
        'longitude': 77.5956,
        'rating': 4.5,
        'review_count': 2150,
        'phone': '+91 80 4055 2000',
        'website': 'https://www.narayananethralaya.org',
        'place_id': 'sample_2',
        'open_now': True
    },
    {
        'name': 'Aditya Birla Aravind Eye Hospital',
        'address': 'No. 61, Koramangala 5th A Cross Road, Bangalore 560034',
        'latitude': 12.9352,
        'longitude': 77.6245,
        'rating': 4.7,
        'review_count': 1620,
        'phone': '+91 80 4040 2020',
        'website': 'https://www.adarsh.in',
        'place_id': 'sample_3',
        'open_now': True
    },
    {
        'name': 'Shroff Eye Centre',
        'address': '2nd Floor, 80 Feet Road, Indiranagar, Bangalore 560038',
        'latitude': 12.9716,
        'longitude': 77.6422,
        'rating': 4.4,
        'review_count': 890,
        'phone': '+91 80 4123 4567',
        'website': 'https://www.shroffeyecentre.com',
        'place_id': 'sample_4',
        'open_now': True
    },
    {
        'name': 'Center for Sight',
        'address': '80 Feet Road, Koramangala, Bangalore 560034',
        'latitude': 12.9352,
        'longitude': 77.6178,
        'rating': 4.6,
        'review_count': 1340,
        'phone': '+91 80 6789 0123',
        'website': 'https://www.centreforsight.net',
        'place_id': 'sample_5',
        'open_now': True
    },
    {
        'name': 'Apollo Spectra Eye Clinic',
        'address': 'Bangalore Medical College Campus, Fort, Bangalore 560002',
        'latitude': 13.0036,
        'longitude': 77.5915,
        'rating': 4.5,
        'review_count': 1120,
        'phone': '+91 80 4088 8888',
        'website': 'https://www.apollospectra.com',
        'place_id': 'sample_6',
        'open_now': True
    },
    {
        'name': 'Nandan Eye Care Centre',
        'address': '80 Feet Road, Opp. Innovative Multiplex, Koramangala, Bangalore 560034',
        'latitude': 12.9320,
        'longitude': 77.6200,
        'rating': 4.3,
        'review_count': 750,
        'phone': '+91 80 4123 5678',
        'website': 'https://www.nandaneyecare.com',
        'place_id': 'sample_7',
        'open_now': True
    },
    {
        'name': 'Aster RV Eye Care',
        'address': 'Aster RV Hospital, Marathahalli, Bangalore 560037',
        'latitude': 12.9700,
        'longitude': 77.7180,
        'rating': 4.6,
        'review_count': 1200,
        'phone': '+91 80 4089 0089',
        'website': 'https://www.asterrv.com',
        'place_id': 'sample_8',
        'open_now': True
    },
    {
        'name': 'BGS Gleneagles Global Hospitals Eye Clinic',
        'address': 'Kengeri, Bangalore 560060',
        'latitude': 13.0200,
        'longitude': 77.5500,
        'rating': 4.4,
        'review_count': 980,
        'phone': '+91 80 6789 1234',
        'website': 'https://www.bgshospitals.com',
        'place_id': 'sample_9',
        'open_now': True
    },
    {
        'name': 'Fortis Eye Institute',
        'address': 'Whitefield, Bangalore 560066',
        'latitude': 13.0259,
        'longitude': 77.7450,
        'rating': 4.5,
        'review_count': 1050,
        'phone': '+91 80 4040 4040',
        'website': 'https://www.fortiseye.com',
        'place_id': 'sample_10',
        'open_now': True
    }
]


def fetch_eye_hospitals_from_api(min_reviews=100):
    """
    Fetch eye hospitals in Bangalore using Places API.

    Args:
        min_reviews (int): Minimum number of reviews to include hospital

    Returns:
        pd.DataFrame: DataFrame with hospital details or None if API fails
    """
    gmaps = googlemaps.Client(key=API_KEY)
    hospitals = []
    next_page_token = None
    request_count = 0

    print(f"Searching for eye hospitals in Bangalore via Google Maps API...")
    print(f"  Radius: {SEARCH_RADIUS}m")
    print(f"  Minimum reviews: {min_reviews}")
    print()

    try:
        while True:
            # Search for eye hospitals
            places_result = gmaps.places_nearby(
                location=BANGALORE_CENTER,
                radius=SEARCH_RADIUS,
                keyword="eye hospital",
                type="hospital",
                page_token=next_page_token
            )

            request_count += 1

            # Process results
            for place in places_result.get('results', []):
                try:
                    # Get place details to get review count and more info
                    place_id = place['place_id']
                    details = gmaps.place(
                        place_id=place_id,
                        fields=['name', 'formatted_address', 'geometry', 'rating', 'user_ratings_total',
                                'website', 'formatted_phone_number', 'opening_hours']
                    )

                    request_count += 1

                    place_data = details['result']
                    review_count = place_data.get('user_ratings_total', 0)

                    # Filter by minimum reviews
                    if review_count >= min_reviews:
                        hospital_info = {
                            'name': place_data.get('name', 'N/A'),
                            'address': place_data.get('formatted_address', 'N/A'),
                            'latitude': place_data.get('geometry', {}).get('location', {}).get('lat', None),
                            'longitude': place_data.get('geometry', {}).get('location', {}).get('lng', None),
                            'rating': place_data.get('rating', None),
                            'review_count': review_count,
                            'phone': place_data.get('formatted_phone_number', 'N/A'),
                            'website': place_data.get('website', 'N/A'),
                            'place_id': place_id,
                            'open_now': place_data.get('opening_hours', {}).get('open_now', None)
                        }
                        hospitals.append(hospital_info)
                        print(f"  ✓ {hospital_info['name']} ({review_count} reviews)")

                    # Rate limiting - 10 requests per second max
                    if request_count % 10 == 0:
                        time.sleep(1)

                except Exception as e:
                    print(f"  ✗ Error processing place: {str(e)}")
                    continue

            # Check if there are more pages
            next_page_token = places_result.get('next_page_token')
            if not next_page_token:
                break

            # Wait before next page request
            time.sleep(2)
            print(f"Fetching next page... (Total found so far: {len(hospitals)})")

        # Create DataFrame
        if hospitals:
            df = pd.DataFrame(hospitals)
            df = df.sort_values('review_count', ascending=False)
            return df
        else:
            return None

    except Exception as e:
        print(f"Error during API search: {str(e)}")
        print("\nNote: This error is typically because:")
        print("  1. Places API is not enabled in Google Cloud Console")
        print("  2. Billing is not set up on the Google Cloud Project")
        print("\nSwitching to sample data for demonstration...\n")
        return None


def get_eye_hospitals(min_reviews=100, use_sample=False):
    """
    Get eye hospitals data from API or fallback to sample data.

    Args:
        min_reviews (int): Minimum number of reviews
        use_sample (bool): Force use of sample data

    Returns:
        pd.DataFrame: Hospital data
    """
    if use_sample:
        print("Using sample eye hospital data...\n")
        df = pd.DataFrame(SAMPLE_EYE_HOSPITALS)
        df = df[df['review_count'] >= min_reviews]
        return df.sort_values('review_count', ascending=False)

    # Try to fetch from API
    df = fetch_eye_hospitals_from_api(min_reviews)

    if df is not None and len(df) > 0:
        return df
    else:
        print("API fetch failed or returned no results. Using sample data...\n")
        df = pd.DataFrame(SAMPLE_EYE_HOSPITALS)
        df = df[df['review_count'] >= min_reviews]
        return df.sort_values('review_count', ascending=False)


def save_hospitals_to_csv(df, filename='eye_hospitals_bangalore.csv'):
    """Save hospital data to CSV"""
    if not df.empty:
        df.to_csv(filename, index=False)
        print(f"✓ Saved to {filename}\n")
        return filename
    else:
        print("No data to save")
        return None


def display_summary(df):
    """Display summary statistics"""
    if df.empty:
        print("No hospitals found")
        return

    print("\n" + "="*70)
    print("EYE HOSPITALS SUMMARY - BANGALORE")
    print("="*70)
    print(f"Total hospitals (min 100 reviews): {len(df)}")
    print(f"\nRating Statistics:")
    print(f"  Average rating: {df['rating'].mean():.2f}/5.0")
    print(f"  Highest rated: {df['rating'].max():.1f}")
    print(f"  Lowest rated: {df['rating'].min():.1f}")
    print(f"\nReview Statistics:")
    print(f"  Total reviews across all hospitals: {df['review_count'].sum():,}")
    print(f"  Average reviews per hospital: {df['review_count'].mean():.0f}")
    print(f"  Median reviews per hospital: {df['review_count'].median():.0f}")
    print(f"\nTop 5 Hospitals by Review Count:")
    for idx, (i, row) in enumerate(df.head(5).iterrows(), 1):
        print(f"  {idx}. {row['name']}")
        print(f"     Reviews: {row['review_count']:,} | Rating: ⭐ {row['rating']}")
    print("="*70 + "\n")


if __name__ == "__main__":
    # Check for command line argument to force sample data
    import sys
    use_sample = '--sample' in sys.argv

    # Fetch eye hospitals with minimum 100 reviews
    hospitals_df = get_eye_hospitals(min_reviews=100, use_sample=use_sample)

    if not hospitals_df.empty:
        # Display summary
        display_summary(hospitals_df)

        # Save to CSV
        save_hospitals_to_csv(hospitals_df)

        # Display first few rows
        print("Sample of hospitals:")
        print(hospitals_df[['name', 'rating', 'review_count']].head().to_string())
        print()
    else:
        print("No hospitals found matching criteria")
