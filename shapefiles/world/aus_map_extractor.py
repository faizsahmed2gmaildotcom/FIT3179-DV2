import geopandas as gp

# 1. Load the Natural Earth countries shapefile
gdf = gp.read_file("ne_50m_admin_0_countries.shp")

# 2. Filter for your target country (e.g., 'France' or 'ISO_A3' code like 'FRA')
country_name = "Australia"
country_gdf = gdf[gdf["ADMIN"] == country_name]

# 3. Save the extracted country to a new shapefile
country_gdf.to_file("../aus_shape/australia.shp")
