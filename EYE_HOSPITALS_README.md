# Eye Hospitals Dashboard - Setup & Usage Guide

## Overview

The Eye Hospitals Dashboard allows you to visualize eye hospitals in Bangalore on an interactive map. The system includes:

1. **Automated data fetching** from Google Maps Places API (with sample data fallback)
2. **Interactive mapping** with hospital locations, ratings, and review counts
3. **Advanced filtering** by rating and review count
4. **Detailed hospital information** including phone, website, and address

## Files

### Main Files
- **`eye_hospital_dashboard.py`** - Streamlit dashboard for visualizing eye hospitals
- **`fetch_eye_hospitals.py`** - Script to fetch hospital data from Google Maps API
- **`eye_hospitals_bangalore.csv`** - Generated data file with hospital information

## Quick Start

### 1. Run the Eye Hospital Dashboard

```bash
# Make sure you're in the TEFHeatMap directory
cd "/Users/ashishlingamneni/Cursor Projects/TEFHeatMap"

# Run the dashboard
streamlit run eye_hospital_dashboard.py
```

This will open an interactive web dashboard at `http://localhost:8501`

### 2. Update Hospital Data (Optional)

To fetch the latest hospital data from Google Maps API:

```bash
python fetch_eye_hospitals.py
```

## Data Source

### Current Implementation
The system currently uses **sample data** of 10 well-known eye hospitals in Bangalore, all with 100+ reviews:

1. **Narayana Nethralaya** - 2,150 reviews ⭐4.5
2. **L V Prasad Eye Institute** - 1,850 reviews ⭐4.6
3. **Aditya Birla Aravind Eye Hospital** - 1,620 reviews ⭐4.7
4. **Center for Sight** - 1,340 reviews ⭐4.6
5. **Aster RV Eye Care** - 1,200 reviews ⭐4.6
6. **Apollo Spectra Eye Clinic** - 1,120 reviews ⭐4.5
7. **BGS Gleneagles Global Hospitals** - 980 reviews ⭐4.4
8. **Shroff Eye Centre** - 890 reviews ⭐4.4
9. **Fortis Eye Institute** - 1,050 reviews ⭐4.5
10. **Nandan Eye Care Centre** - 750 reviews ⭐4.3

**Average Rating:** 4.51/5.0
**Total Reviews:** 12,950

### Using Real Data from Google Maps API

To fetch live data from Google Maps API instead of sample data:

#### Step 1: Enable Google Maps Places API

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing one
3. Search for "Places API" in the search bar
4. Click "Places API" and enable it
5. Enable billing on the project
   - Click "Billing" in the left sidebar
   - Create a billing account and link it to your project
   - **Note:** Free tier provides $200/month credit; API calls are ~$7 per 1000 requests

#### Step 2: Already Configured

Your `.env` file already contains:
```
GOOGLE_MAPS_API_KEY=AIzaSyDUU8IQ6Y4_Dz8upL07ykhmMtmmBVzkRwM
```

Once billing is enabled on this API key, the system will automatically fetch real data.

#### Step 3: Fetch New Data

```bash
python fetch_eye_hospitals.py
```

The script will:
- Try to fetch from Google Maps API
- Search for eye hospitals in a 30km radius around Bangalore center (12.9716, 77.5946)
- Filter results to show only hospitals with ≥100 reviews
- Save data to `eye_hospitals_bangalore.csv`
- Fall back to sample data if API is unavailable

## Dashboard Features

### Map Visualization
- **Interactive map** with hospital markers
- **Color-coded markers** based on rating:
  - 🟢 **Dark Green** - Excellent (≥4.6 rating)
  - 🟢 **Green** - Very Good (4.4-4.5 rating)
  - 🔵 **Blue** - Good (4.2-4.3 rating)
  - 🟠 **Orange** - Fair (<4.2 rating)
- **Hover tooltips** showing hospital name and rating
- **Click popups** with complete hospital details

### Filtering
- **Rating filter** - Show only hospitals with minimum rating
- **Review count filter** - Show only hospitals with minimum reviews
- Real-time filtering updates both map and table

### Hospital Details Table
- **Sortable** by review count, rating, or name
- **Detailed information** for each hospital
- **Download option** to export filtered results as CSV

## Command Line Usage

### Fetch Hospitals (with Sample Data Fallback)
```bash
python fetch_eye_hospitals.py
```

### Force Sample Data
```bash
python fetch_eye_hospitals.py --sample
```

### Output
```
======================================================================
EYE HOSPITALS SUMMARY - BANGALORE
======================================================================
Total hospitals (min 100 reviews): 10

Rating Statistics:
  Average rating: 4.51/5.0
  Highest rated: 4.7
  Lowest rated: 4.3

Review Statistics:
  Total reviews across all hospitals: 12,950
  Average reviews per hospital: 1,295
  Median reviews per hospital: 1,160

Top 5 Hospitals by Review Count:
  1. Narayana Nethralaya
     Reviews: 2,150 | Rating: ⭐ 4.5
  ...
```

## Data Fields

The `eye_hospitals_bangalore.csv` file contains:

| Field | Description | Example |
|-------|-------------|---------|
| `name` | Hospital name | "Narayana Nethralaya" |
| `address` | Full address | "#121, Chord Road, Bangalore 560001" |
| `latitude` | Latitude coordinate | 13.0065 |
| `longitude` | Longitude coordinate | 77.5956 |
| `rating` | Google Maps rating | 4.5 |
| `review_count` | Number of reviews | 2150 |
| `phone` | Contact phone number | "+91 80 4055 2000" |
| `website` | Hospital website | "https://www.narayananethralaya.org" |
| `place_id` | Google Maps place ID | "ChIJ..." |
| `open_now` | Currently open? | true/false |

## Integration with Main Dashboard

Both dashboards are **independent**:

1. **`app.py`** - Customer address heatmap (existing)
2. **`eye_hospital_dashboard.py`** - Eye hospital visualization (new)

You can run either dashboard:
```bash
# Customer addresses
streamlit run app.py

# Eye hospitals
streamlit run eye_hospital_dashboard.py
```

### To Create a Combined Dashboard

If you want both visualizations in one app, you can use Streamlit's multi-page feature:

1. Create a `pages/` directory
2. Move each dashboard to a separate file in `pages/`
3. Run the main app

Example structure:
```
TEFHeatMap/
├── app.py (main)
├── pages/
│   ├── customer_addresses.py
│   └── eye_hospitals.py
```

## Troubleshooting

### "FileNotFoundError: eye_hospitals_bangalore.csv not found"
- Run `python fetch_eye_hospitals.py` first to generate the CSV

### API Returns "REQUEST_DENIED"
- **Cause:** Places API not enabled or billing not configured
- **Solution:** Follow "Using Real Data" section above
- **Workaround:** System automatically uses sample data

### Streamlit not found
```bash
pip install streamlit==1.51.0
```

### Google Maps API returns zero results
- Check that Bangalore center coordinates are correct: (12.9716, 77.5946)
- Search radius is 30km - this covers greater Bangalore area
- Filter is set to ≥100 reviews minimum

## API Cost Estimation

Google Maps Places API pricing (as of 2024):
- **Nearby Search**: $7 per 1000 requests
- **Place Details**: $7 per 1000 requests

Fetching 50 hospitals (example):
- 1 nearby search request: $0.007
- 50 detail requests: $0.35
- **Total: ~$0.36 per fetch**

Google Cloud free tier: **$200/month** - typically sufficient for regular updates.

## Features Roadmap

- [ ] Add nearby clinics/optometrists
- [ ] Display opening hours
- [ ] Show average wait times (when available)
- [ ] Display specializations
- [ ] Insurance accepted filter
- [ ] Price range filtering
- [ ] Appointment booking integration

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify `.env` file has GOOGLE_MAPS_API_KEY
3. Ensure all dependencies are installed: `pip install -r requirements.txt`
4. Check Google Cloud Console for API errors

## Notes

- Sample data is sourced from well-known eye hospitals in Bangalore
- Hospitals are filtered to show only those with ≥100 Google Maps reviews
- Data is cached locally to reduce API calls
- Hospital ratings and review counts can be updated by re-running the fetch script
