import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, HeatMap
from streamlit_folium import st_folium

# Page config
st.set_page_config(
    page_title="Surgery Type Heatmap Dashboard",
    page_icon="🏥",
    layout="wide"
)

# Cache data loading
@st.cache_data
def load_data():
    """Load and prepare the surgery data"""
    # Load the surgery data
    surgery_df = pd.read_csv('BlrSurgeryOnly.csv')

    # Load Google Maps pincode coordinates
    pincode_coords = pd.read_csv('pincode_coordinates_google.csv')

    # Clean pincodes
    surgery_df['CPA_PIN_CODE'] = pd.to_numeric(surgery_df['CPA_PIN_CODE'], errors='coerce')
    surgery_df = surgery_df.dropna(subset=['CPA_PIN_CODE'])

    # Parse registration date to extract year
    surgery_df['RegistrationDate'] = pd.to_datetime(surgery_df['RegistrationDate'], format='%d/%m/%y', errors='coerce')
    surgery_df['Year'] = surgery_df['RegistrationDate'].dt.year

    # Clean patient type - handle variations
    surgery_df['BSM_MINOR_CD'] = surgery_df['BSM_MINOR_CD'].fillna('Unknown').astype(str).str.strip()

    # Merge with Google Maps coordinates
    merged_df = surgery_df.merge(
        pincode_coords[['pincode', 'latitude', 'longitude', 'city', 'state']],
        left_on='CPA_PIN_CODE',
        right_on='pincode',
        how='left'
    )

    # Rename columns to match expected format
    merged_df = merged_df.rename(columns={
        'latitude': 'Latitude',
        'longitude': 'Longitude',
        'state': 'StateName'
    })

    # Use Google Maps city if available, otherwise fall back to address city
    merged_df['CPA_ADDR_CITY'] = merged_df['city'].fillna(merged_df['CPA_ADDR_CITY'])

    # Drop rows without coordinates
    merged_df = merged_df.dropna(subset=['Latitude', 'Longitude'])

    return merged_df

@st.cache_data
def load_hospitals():
    """Load eye hospitals data"""
    try:
        hospitals_df = pd.read_csv('eye_hospitals_bangalore_comprehensive.csv')
        hospitals_df = hospitals_df.dropna(subset=['latitude', 'longitude'])
        return hospitals_df
    except FileNotFoundError:
        return pd.DataFrame()  # Return empty dataframe if file not found

# Load data
st.title("🏥 Surgery Type Distribution Heatmap Dashboard")
st.markdown("Interactive visualization of surgical patients across Bangalore by patient type")

with st.spinner("Loading data..."):
    df = load_data()

# Sidebar filters
st.sidebar.header("🔍 Filters")

# Get unique patient types and create user-friendly labels
patient_types = sorted(df['BSM_MINOR_CD'].unique())
patient_type_labels = {
    '0': '📋 OPD (Outpatient)',
    'CAT': '🏥 CATLAC Surgery',
    'LSK': '👁️ LASIK Surgery',
    'IP Others': '🔧 IP Others',
    'LRC': '🔬 LRC',
    'Unknown': '❓ Unknown'
}

# Create patient type filter
patient_type_options = ['All Patient Types'] + patient_types
selected_patient_type = st.sidebar.selectbox(
    "Select Patient Type",
    patient_type_options,
    format_func=lambda x: patient_type_labels.get(x, x) if x != 'All Patient Types' else x
)

# Year filter
years = sorted(df['Year'].dropna().unique())
year_options = ['All Years'] + [int(year) for year in years]
selected_year = st.sidebar.selectbox("Select Year", year_options)

# Visualization type
viz_type = st.sidebar.radio(
    "Visualization Type",
    ["Clustered Markers", "Heatmap", "Both"]
)

# Display mode toggle
display_mode = st.sidebar.radio(
    "Display Mode",
    ["Absolute Count", "Percentage"]
)

# Load hospitals data early
hospitals = load_hospitals()

# Hospital settings
st.sidebar.markdown("---")
st.sidebar.markdown("### 👁️ Eye Hospitals")

# Toggle to show/hide hospitals
show_hospitals = st.sidebar.checkbox(
    "Show Eye Hospitals on Map",
    value=True if not hospitals.empty else False,
    help="Toggle to display eye hospitals with 100+ reviews"
)

if show_hospitals and not hospitals.empty:
    st.sidebar.markdown("**Hospital Filters:**")

    # Hospital rating filter
    hospital_min_rating = st.sidebar.slider(
        "Minimum Hospital Rating",
        min_value=0.0,
        max_value=5.0,
        value=4.0,
        step=0.1,
        key="hospital_rating"
    )

    # Hospital review count filter
    hospital_min_reviews = st.sidebar.slider(
        "Minimum Hospital Reviews",
        min_value=int(hospitals['review_count'].min()),
        max_value=int(hospitals['review_count'].max()),
        value=500,
        step=100,
        key="hospital_reviews"
    )

    # Excluded hospitals (removed hospitals)
    if 'excluded_hospitals' not in st.session_state:
        st.session_state.excluded_hospitals = set()

    # Show count of available hospitals
    filtered_hospital_count = len(hospitals[
        (hospitals['rating'] >= hospital_min_rating) &
        (hospitals['review_count'] >= hospital_min_reviews)
    ])
    st.sidebar.markdown(f"**Available hospitals:** {filtered_hospital_count}/{len(hospitals)}")

    # Show removed hospitals count
    if st.session_state.excluded_hospitals:
        st.sidebar.markdown(f"**Removed hospitals:** {len(st.session_state.excluded_hospitals)}")
else:
    st.sidebar.info("No hospital data available")
    show_hospitals = False
    # Set default values for hospital filters
    hospital_min_rating = 4.0
    hospital_min_reviews = 500

# Apply filters
filtered_df = df.copy()

if selected_patient_type != 'All Patient Types':
    filtered_df = filtered_df[filtered_df['BSM_MINOR_CD'] == selected_patient_type]

if selected_year != 'All Years':
    filtered_df = filtered_df[filtered_df['Year'] == selected_year]

# Aggregate data by pincode
pincode_counts = filtered_df.groupby('CPA_PIN_CODE').size().reset_index(name='patient_count')

# For each pincode, get representative location and most common city/state
pincode_locations = filtered_df.groupby('CPA_PIN_CODE').agg({
    'Latitude': 'median',
    'Longitude': 'median',
    'CPA_ADDR_CITY': lambda x: x.mode()[0] if len(x.mode()) > 0 else x.iloc[0],
    'StateName': lambda x: x.mode()[0] if len(x.mode()) > 0 else x.iloc[0],
    'BSM_MINOR_CD': lambda x: x.mode()[0] if len(x.mode()) > 0 else x.iloc[0]  # Get the patient type
}).reset_index()

# Merge counts with locations
pincode_summary = pincode_counts.merge(pincode_locations, on='CPA_PIN_CODE')

# Calculate percentage of total patients
total_patients = len(filtered_df)
pincode_summary['percentage'] = (pincode_summary['patient_count'] / total_patients * 100)
pincode_summary = pincode_summary.sort_values('patient_count', ascending=False)

# Display statistics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Patients", f"{len(filtered_df):,}")
with col2:
    st.metric("Unique Pincodes", f"{len(pincode_summary):,}")
with col3:
    st.metric("Average per Pincode", f"{pincode_summary['patient_count'].mean():.1f}")
with col4:
    st.metric("Max at One Pincode", f"{pincode_summary['patient_count'].max():,}")

# Display patient type breakdown if showing all types
if selected_patient_type == 'All Patient Types':
    st.subheader("📊 Patient Type Breakdown")
    type_breakdown = df.groupby('BSM_MINOR_CD').size().reset_index(name='count')
    type_breakdown['percentage'] = (type_breakdown['count'] / len(df) * 100).round(1)
    type_breakdown = type_breakdown.sort_values('count', ascending=False)

    # Create columns for breakdown display
    cols = st.columns(len(type_breakdown))
    for col, (idx, row) in zip(cols, type_breakdown.iterrows()):
        with col:
            st.metric(
                patient_type_labels.get(row['BSM_MINOR_CD'], row['BSM_MINOR_CD']),
                f"{row['count']:,}",
                f"{row['percentage']:.1f}%"
            )

# Calculate map center
if len(pincode_summary) > 0:
    center_lat = pincode_summary['Latitude'].mean()
    center_lon = pincode_summary['Longitude'].mean()
else:
    center_lat = 12.9716  # Default to Bangalore
    center_lon = 77.5946

# Create map
st.subheader("🗺️ Map Visualization")

# Create base map
m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=11,
    tiles='OpenStreetMap',
    control_scale=True
)

# Define colors for patient types
type_colors = {
    '0': '#1f77b4',        # Blue for OPD
    'CAT': '#ff7f0e',      # Orange for CATLAC
    'LSK': '#2ca02c',      # Green for LASIK
    'IP Others': '#d62728', # Red for IP Others
    'LRC': '#9467bd',      # Purple for LRC
    'Unknown': '#7f7f7f'   # Gray for Unknown
}

# Add markers with clustering
if viz_type in ["Clustered Markers", "Both"]:
    is_percentage_mode = display_mode == "Percentage"

    # Custom cluster function
    if is_percentage_mode:
        icon_create_function = f"""
        function(cluster) {{
            var markers = cluster.getAllChildMarkers();
            var sumCount = 0;
            var sumPct = 0;
            var totalPatients = {total_patients};
            for (var i = 0; i < markers.length; i++) {{
                if (markers[i].options.customCount) {{
                    sumCount += markers[i].options.customCount;
                }}
                if (markers[i].options.customPercentage) {{
                    sumPct += markers[i].options.customPercentage;
                }}
            }}

            var displayText = sumPct < 1 ? '<1%' : sumPct.toFixed(1) + '%';

            var size = 'small';
            if (sumPct >= 10) size = 'large';
            else if (sumPct >= 5) size = 'medium';

            var color = 'lightblue';
            if (sumPct >= 10) color = 'red';
            else if (sumPct >= 5) color = 'orange';
            else if (sumPct >= 1) color = 'lightgreen';

            return L.divIcon({{
                html: '<div style="background-color:' + color + '; border-radius: 50%; text-align: center; color: black; font-weight: bold; border: 3px solid white; box-shadow: 0 0 10px rgba(0,0,0,0.5);"><span>' + displayText + '</span></div>',
                className: 'marker-cluster marker-cluster-' + size,
                iconSize: new L.Point(40, 40)
            }});
        }}
        """
    else:
        icon_create_function = """
        function(cluster) {
            var markers = cluster.getAllChildMarkers();
            var sum = 0;
            for (var i = 0; i < markers.length; i++) {
                if (markers[i].options.customCount) {
                    sum += markers[i].options.customCount;
                }
            }
            var size = 'small';
            if (sum >= 5000) size = 'large';
            else if (sum >= 1000) size = 'medium';

            var color = 'lightblue';
            if (sum > 1000) color = 'red';
            else if (sum > 500) color = 'orange';
            else if (sum >= 100) color = 'lightgreen';

            return L.divIcon({
                html: '<div style="background-color:' + color + '; border-radius: 50%; text-align: center; color: black; font-weight: bold; border: 3px solid white; box-shadow: 0 0 10px rgba(0,0,0,0.5);"><span>' + sum + '</span></div>',
                className: 'marker-cluster marker-cluster-' + size,
                iconSize: new L.Point(40, 40)
            });
        }
        """

    marker_cluster = MarkerCluster(
        name="Patient Locations",
        overlay=True,
        control=True,
        icon_create_function=icon_create_function
    )

    for idx, row in pincode_summary.iterrows():
        pct_display = "<1%" if row['percentage'] < 1 else f"{row['percentage']:.1f}%"

        # Get patient type from the row
        patient_type = row['BSM_MINOR_CD']
        patient_label = patient_type_labels.get(patient_type, patient_type)

        popup_html = f"""
        <div style="font-family: Arial; width: 220px;">
            <h4 style="margin: 0; color: #1f77b4;">📍 {row['CPA_ADDR_CITY']}</h4>
            <hr style="margin: 5px 0;">
            <b>Patient Type:</b> {patient_label}<br>
            <b>Pincode:</b> {int(row['CPA_PIN_CODE'])}<br>
            <b>State:</b> {row['StateName']}<br>
            <b>Patients:</b> <span style="color: #d62728; font-weight: bold;">{row['patient_count']}</span><br>
            <b>Percentage:</b> <span style="color: #d62728; font-weight: bold;">{pct_display}</span><br>
            <b>Coordinates:</b> {row['Latitude']:.4f}, {row['Longitude']:.4f}
        </div>
        """

        if is_percentage_mode:
            display_text = pct_display
            if row['percentage'] >= 10:
                color = 'red'
            elif row['percentage'] >= 5:
                color = 'orange'
            elif row['percentage'] >= 1:
                color = 'lightgreen'
            else:
                color = 'lightblue'
            tooltip_text = f"{row['CPA_ADDR_CITY']} - {pct_display} ({row['patient_count']} patients)"
        else:
            display_text = str(row['patient_count'])
            if row['patient_count'] > 1000:
                color = 'red'
            elif row['patient_count'] > 500:
                color = 'orange'
            elif row['patient_count'] > 100:
                color = 'lightgreen'
            else:
                color = 'lightblue'
            tooltip_text = f"{row['CPA_ADDR_CITY']} - {row['patient_count']} patients"

        custom_icon = folium.DivIcon(
            html=f'''
            <div style="
                background-color: {color};
                border-radius: 50%;
                width: 35px;
                height: 35px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: black;
                font-weight: bold;
                font-size: 11px;
                border: 3px solid white;
                box-shadow: 0 0 10px rgba(0,0,0,0.5);
            ">{display_text}</div>
            '''
        )

        marker = folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=tooltip_text,
            icon=custom_icon
        )
        marker.options['customCount'] = int(row['patient_count'])
        marker.options['customPercentage'] = float(row['percentage'])
        marker.add_to(marker_cluster)

    marker_cluster.add_to(m)

# Add heatmap layer
if viz_type in ["Heatmap", "Both"]:
    heat_data = [
        [row['Latitude'], row['Longitude'], row['patient_count']]
        for _, row in pincode_summary.iterrows()
    ]

    HeatMap(
        heat_data,
        name="Heatmap",
        min_opacity=0.3,
        max_zoom=18,
        radius=15,
        blur=20,
        gradient={
            0.0: 'blue',
            0.5: 'lime',
            0.7: 'yellow',
            1.0: 'red'
        }
    ).add_to(m)

# Add hospital markers
if show_hospitals and not hospitals.empty:
    # Filter hospitals by rating and review count
    filtered_hospitals = hospitals[
        (hospitals['rating'] >= hospital_min_rating) &
        (hospitals['review_count'] >= hospital_min_reviews)
    ].copy()

    # Remove excluded hospitals
    filtered_hospitals = filtered_hospitals[
        ~filtered_hospitals['name'].isin(st.session_state.excluded_hospitals)
    ]

    # Create hospital marker group
    hospital_group = folium.FeatureGroup(name='Eye Hospitals', show=True)

    # Define color based on hospital rating
    def get_hospital_color(rating):
        """Get marker color based on rating"""
        if rating >= 4.6:
            return "darkgreen"  # Excellent
        elif rating >= 4.4:
            return "green"  # Very Good
        elif rating >= 4.2:
            return "blue"  # Good
        else:
            return "orange"  # Fair

    # Add hospital markers
    for idx, hospital in filtered_hospitals.iterrows():
        color = get_hospital_color(hospital['rating'])

        # Create popup with hospital info
        website_html = ''
        if pd.notna(hospital['website']) and str(hospital['website']) != 'N/A':
            website_html = f'<b>Website:</b> <a href="{hospital["website"]}" target="_blank">Visit</a><br>'

        popup_text = f"""
        <div style="font-family: Arial; font-size: 12px; width: 260px;">
            <h4 style="margin: 5px 0; color: {color};">👁️ {hospital['name']}</h4>
            <hr style="margin: 3px 0;">
            <b>Rating:</b> ⭐ {hospital['rating']}/5.0<br>
            <b>Reviews:</b> {hospital['review_count']:,}<br>
            <b>Address:</b> {hospital['address']}<br>
            <b>Phone:</b> {hospital['phone']}<br>
            {website_html}
            <hr style="margin: 3px 0;">
        </div>
        """

        # Create circular marker
        folium.CircleMarker(
            location=[hospital['latitude'], hospital['longitude']],
            radius=6,
            popup=folium.Popup(popup_text, max_width=300),
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
            weight=2,
            tooltip=f"👁️ {hospital['name']} ({hospital['rating']} ⭐)"
        ).add_to(hospital_group)

    hospital_group.add_to(m)

# Add layer control
folium.LayerControl().add_to(m)

# Display map
st_folium(m, width=1400, height=600)

# Hospital management section
if show_hospitals and not hospitals.empty:
    st.subheader("👁️ Hospital Management")

    # Filter hospitals for display
    filtered_hospitals_display = hospitals[
        (hospitals['rating'] >= hospital_min_rating) &
        (hospitals['review_count'] >= hospital_min_reviews)
    ].copy()

    filtered_hospitals_display = filtered_hospitals_display[
        ~filtered_hospitals_display['name'].isin(st.session_state.excluded_hospitals)
    ].sort_values('review_count', ascending=False)

    if not filtered_hospitals_display.empty:
        col1, col2 = st.columns([3, 1])

        with col1:
            # Display hospitals table with removal option
            st.markdown("**Click 'Remove Hospital' to filter it out from the map:**")

            # Create columns for the table
            hosp_col1, hosp_col2, hosp_col3, hosp_col4, hosp_col5 = st.columns([3, 1, 1, 1, 1])

            with hosp_col1:
                st.markdown("**Hospital Name**")
            with hosp_col2:
                st.markdown("**Rating**")
            with hosp_col3:
                st.markdown("**Reviews**")
            with hosp_col4:
                st.markdown("**City**")
            with hosp_col5:
                st.markdown("**Action**")

            # Display each hospital with remove button
            for idx, hospital in filtered_hospitals_display.iterrows():
                hosp_col1, hosp_col2, hosp_col3, hosp_col4, hosp_col5 = st.columns([3, 1, 1, 1, 1])

                with hosp_col1:
                    st.text(hospital['name'][:30] + "..." if len(hospital['name']) > 30 else hospital['name'])
                with hosp_col2:
                    st.text(f"⭐ {hospital['rating']}")
                with hosp_col3:
                    st.text(f"{hospital['review_count']:,}")
                with hosp_col4:
                    # Try to extract city from address
                    address_parts = hospital['address'].split(',')
                    city = address_parts[-3].strip() if len(address_parts) >= 3 else "Unknown"
                    st.text(city[:15] + "..." if len(city) > 15 else city)
                with hosp_col5:
                    if st.button("Remove", key=f"remove_{hospital['name']}_{idx}"):
                        st.session_state.excluded_hospitals.add(hospital['name'])
                        st.rerun()

        with col2:
            st.info(f"📊 Showing {len(filtered_hospitals_display)}/{len(hospitals)} hospitals")
    else:
        st.info("No hospitals match the selected filters")
else:
    if show_hospitals:
        st.info("No hospital data available. Please ensure 'eye_hospitals_bangalore_comprehensive.csv' exists.")

# Display top locations table
st.subheader("📊 Top 20 Locations by Patient Count")
if len(pincode_summary) > 0:
    top_locations = pincode_summary.head(20)[['CPA_ADDR_CITY', 'CPA_PIN_CODE', 'StateName', 'patient_count', 'percentage']].copy()
    top_locations.columns = ['City', 'Pincode', 'State', 'Patient Count', 'Percentage']
    top_locations['Pincode'] = top_locations['Pincode'].astype(int)
    top_locations['Percentage'] = top_locations['Percentage'].apply(lambda x: "<1%" if x < 1 else f"{x:.1f}%")
    top_locations.index = range(1, len(top_locations) + 1)
    st.dataframe(top_locations, width='stretch')
else:
    st.info("No data available for the selected filters.")

# Add color legend
st.sidebar.markdown("---")
st.sidebar.markdown("### 🎨 Marker Colors")

if display_mode == "Percentage":
    st.sidebar.markdown("**Individual Pincodes & Clusters:**")
    st.sidebar.markdown("🔴 **Red:** ≥ 10%")
    st.sidebar.markdown("🟠 **Orange:** 5-10%")
    st.sidebar.markdown("🟢 **Green:** 1-5%")
    st.sidebar.markdown("🔵 **Blue:** < 1%")
else:
    st.sidebar.markdown("**Individual Pincodes & Clusters:**")
    st.sidebar.markdown("🔴 **Red:** > 1,000 patients")
    st.sidebar.markdown("🟠 **Orange:** 500-1,000 patients")
    st.sidebar.markdown("🟢 **Green:** 100-499 patients")
    st.sidebar.markdown("🔵 **Blue:** < 100 patients")

# Patient type information
st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 Patient Types")
st.sidebar.markdown("- **0:** OPD (Outpatient)")
st.sidebar.markdown("- **CAT:** CATLAC Surgery")
st.sidebar.markdown("- **LSK:** LASIK Surgery")
st.sidebar.markdown("- **IP Others:** Other Inpatient Procedures")
st.sidebar.markdown("- **LRC:** LRC (Low Resource Center?)")
