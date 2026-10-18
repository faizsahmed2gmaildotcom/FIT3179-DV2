import glob
import os
import re
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# ==============================================================================
# CONFIGURATION
# ==============================================================================
SHAPEFILE_PATH = "../../aus_pha_shape/PHA_2021_Aust_GDA2020_Gen50.shp"
FILE_PATTERN = "estimated-smokers-above-18-*.csv"
OUTPUT_CSV = "australia_smokers_dot_density.csv"

# RATIO CONFIGURATION:
# 1 dot represents N estimated smokers.
# Adjust to balance visual clarity and file size (e.g., 500 or 1000).
DOT_RATIO = 500

# Shapefile attribute column name matching the 'Code' column in CSVs
# Common examples: 'PHA_CODE', 'SA2_CODE16', 'CODE', 'STATE_CODE', etc.
SHAPEFILE_CODE_COL = "Code"


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================
def generate_random_dots_in_polygon(geometry, num_dots):
    """
    Generates `num_dots` random geographic points within a Shapely polygon/multipolygon.
    """
    dots = []
    if geometry is None or geometry.is_empty or num_dots <= 0:
        return dots

    min_x, min_y, max_x, max_y = geometry.bounds
    count = 0

    # Rejection sampling algorithm for uniform dot distribution within polygon
    while count < num_dots:
        random_x = np.random.uniform(min_x, max_x)
        random_y = np.random.uniform(min_y, max_y)
        p = Point(random_x, random_y)

        if geometry.contains(p):
            # p.x is Longitude, p.y is Latitude
            dots.append((round(p.y, 5), round(p.x, 5)))
            count += 1

    return dots


# ==============================================================================
# MAIN CONCATENATION & SCATTER PIPELINE
# ==============================================================================
def process_smoker_datasets():
    # 1. Load Australia Shapefile
    print(f"Loading shapefile from {SHAPEFILE_PATH}...")
    try:
        gdf = gpd.read_file(SHAPEFILE_PATH)
        # Ensure EPSG:4326 WGS84 projection for latitude/longitude
        if gdf.crs and gdf.crs.to_string() != "EPSG:4326":
            gdf = gdf.to_crs(epsg=4326)
    except Exception as e:
        print(f"Error loading shapefile: {e}")
        return

    # Standardize shapefile code column for merging
    gdf[SHAPEFILE_CODE_COL] = gdf[SHAPEFILE_CODE_COL].astype(str).str.strip()

    # 2. Discover all CSV files matching the pattern
    csv_files = glob.glob(FILE_PATTERN)
    print(f"Found {len(csv_files)} dataset files: {csv_files}")

    all_dots = []

    for file_path in csv_files:
        # Extract 4-digit year from file name (e.g., estimated-smokers-above-18-2022.csv -> 2022)
        year_match = re.search(r"(\d{4})", os.path.basename(file_path))
        year = year_match.group(1) if year_match else "Unknown"

        print(f"\nProcessing {file_path} for Year: {year}...")
        df = pd.read_csv(file_path)

        # Standardize columns and filter out non-data summary rows
        df['Code'] = df['Code'].astype(str).str.strip()
        df['Number'] = pd.to_numeric(df['Number'], errors='coerce')
        df = df.dropna(subset=['Number', 'Code'])

        # Merge tabular dataset with GeoDataFrame polygon geometries
        merged = gdf.merge(df, left_on=SHAPEFILE_CODE_COL, right_on='Code', how='inner')

        # 3. Scatter points per region
        for _, row in merged.iterrows():
            smoker_count = row['Number']
            num_dots = int(round(smoker_count / DOT_RATIO))

            if num_dots > 0:
                dots = generate_random_dots_in_polygon(row['geometry'], num_dots)
                area_name = row.get('Name of Population Health Area of residence',
                                    row.get('Name of Population Health Areas of residence',
                                            row.get('Name', 'Unknown Region')))

                for lat, lon in dots:
                    all_dots.append({
                        'year': year,
                        'code': row['Code'],
                        'region_name': area_name,
                        'latitude': lat,
                        'longitude': lon
                    })

    # 4. Concatenate and Export
    dots_df = pd.DataFrame(all_dots)
    print(f"\nSuccessfully generated {len(dots_df):,} dot records across all years.")
    dots_df.to_csv(OUTPUT_CSV, index=False)
    print(f"Exported combined dot density dataset to '{OUTPUT_CSV}'.")


if __name__ == "__main__":
    process_smoker_datasets()
