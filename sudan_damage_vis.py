"""
Sudan War Damage

This file implements a simple UI for visualizing the progression of war in Sudan using satellite imagery
Nighttime lights are a common proxy for general human well-being. By inspecting changes in nighttime lights,
it is possible to monitor destruction, migration, and other war effects such as fires

Currently, it is set up for using the NASA Black Marble Data for Sudan, but the project can be easily generalized
To change the coordinates of the map, change PRESET_COORD_LAYOUTS, or type your coordinates manually
If you download appropriate data, this tool will work for anywhere in the world
To change the data used, put your .h5 files into a folder lead to by PATH_DEFAULT
To view other, differently formatted satellite data with sufficiently similar interpretations, 
change the file navigation in load_available_dates and load_data_from_date to match the format of your data

This project is packaged with (stripped down) data from 1 year of the VNP46A3 dataset, the monthly Black Marble dataset from NASA
To download more, see https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/VNP46A3/#overview

The code finds its data in a folder lead to by PATH_DEFAULT. At the moment, the app assumes the data starts in data.zip in the same directory
as this app, extracts it, and creates such a folder. That way, it will work when deployed to streamlit or if you just download all of the files
in this repository. If you are running locally, feel free to just leave your files extracted in a folder of your choice and set PATH_DEFAULT manually,
commenting out and in the relevant lines at the top of the file

How to run:
  0. Either leave your data compressed as data.zip in the same directory as this script, or set PATH_DEFAULT to a folder containing your data manually
  1. Open the folder containing this file in your preferred terminal
  2. Use "streamlit run "./sudan_damage_vis.py"" in your terminal. 
     If streamlit is not in your PATH, you might need to use "py -m streamlit run "./sudan_damage_vis""
It will open in your browser

"""

import streamlit as st
import h5py
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import glob
from mpl_toolkits.axes_grid1 import make_axes_locatable
import os

# Config
APP_TITLE = "Sudan War Damage Visualizer"
PRESET_COORD_LAYOUTS = {
    "Sudan" : {"lat_min": 9, "lat_max": 23, "lon_min": 21, "lon_max": 39},
    "Khartoum": {"lat_min": 14.75, "lat_max": 16.5, "lon_min": 31.6, "lon_max": 33.5},
    "Darfur": {"lat_min": 8, "lat_max": 21, "lon_min": 21, "lon_max": 30},
    "Nile River": {"lat_min": 16, "lat_max": 23, "lon_min": 28, "lon_max": 36}
}

ROOT = os.path.dirname(__file__)
ZIP_PATH = os.path.join(ROOT, "data.zip")
DATA_DIR = os.path.join(ROOT, "data")

#for running the streamlit app with data off github
@st.cache_data
def decompress_data(path = ZIP_PATH):
    os.makedirs(DATA_DIR, exist_ok=True)
    with zipfile.ZipFile(path, 'r') as z:
        z.extractall(DATA_DIR)
    return DATA_DIR

PATH_DEFAULT = decompress_data()
#or set path manually
#PATH_DEFAULT = "C:..."

#load all available dates in a specified folder
def load_available_dates(path = PATH_DEFAULT):
    files = glob.glob(os.path.join(path, "*.h5"))
    dates = set()
    for file in files:
        with h5py.File(file, 'r') as f:
            date = f.attrs["RangeEndingDate"] #Black Marble data has this attribute
            if date not in dates:
                dates.add(date)  
    dates = list(dates)   
    dates.sort()           
    return dates

#load the data for a specified data, trimming areas outside of the desired coordinates
def load_data_for_date(date_wanted: np.bytes_, coords = (9, 23, 21, 39), path = PATH_DEFAULT):
    (southBound, northBound, westBound, eastBound) = coords
    files = glob.glob(os.path.join(path, "*.h5"))
    data_list = list()
    for f in files:
        with h5py.File(f, 'r') as f:
            date = f.attrs["RangeEndingDate"]
            if date == date_wanted:
                #If you wish to use non-Black Marble data, change these two accesses to accomodate the relevant file structure 
                data = f['HDFEOS/GRIDS/VIIRS_Grid_DNB_2d/Data Fields']
                light_data = data['NearNadir_Composite_Snow_Free'][:] 
                light_data = np.where(light_data < 0, np.nan, light_data)
                lat_data = data['lat'][:]
                lon_data = data['lon'][:]

                valid_lon = np.where((westBound <= lon_data) & (lon_data <= eastBound))
                valid_lat = np.where((southBound <= lat_data) & (lat_data <= northBound))
                if valid_lon[0].size == 0 or valid_lat[0].size == 0:
                    #if no valid values, np.where returns (np.array([], dtype = ...),) as a tuple, which the above checks against
                    continue
                first_lon = np.min(valid_lon)
                last_lon = np.max(valid_lon)
                first_lat = np.min(valid_lat)
                last_lat = np.max(valid_lat)
                light_data = light_data[first_lat:last_lat+1, first_lon:last_lon+1]
                lat_data = lat_data[first_lat:last_lat+1]
                lon_data = lon_data[first_lon:last_lon+1]
                data_list.append((light_data, lat_data, lon_data))     
    sorted_list = sorted(data_list, key=lambda data: (data[-2][0], data[-1][0]))
    return sorted_list

#loads the data for two specified dates, chunks and normalizes them if necessary, and returns relevant difference information
def get_difference_data(dateEarly, dateLater, coords = (9, 23, 21, 39), relative = False, chunk_size = 1, normalize = False):
    data_list1 = load_data_for_date(dateEarly, coords)
    data_list2 = load_data_for_date(dateLater, coords)
    if chunk_size > 1:
        chunk_data(data_list1, chunk_size)
        chunk_data(data_list2, chunk_size)
    if normalize:
        data_list1 = normalize_data(data_list1)
        data_list2 = normalize_data(data_list2)
    difference_list = list()
    for data1, data2 in zip(data_list1, data_list2):
        (light1, lat, lon) = data1
        (light2, _, _) = data2
        if relative:
            #light in areas that previously had 0 light are recorded as negative, otherwise unmodified values
            #light in areas that previosly had non-zero light are recorded as a ratio
            difference = light2 / np.where(light1 == 0, -1, light1)
        else:
            difference = light2 - light1
        difference_list.append((difference, lat, lon))
    return difference_list

#normalizes data for a date by dividing each entry by the sum of entries. Yields proportion data
def normalize_data(data_list):
    sumLights = 0
    data_list_normalized = list()
    for data in data_list:
        sumLights += np.sum(data[0])
    for data in data_list:
        (values, *other) = data
        values = values / sumLights
        data_list_normalized.append((values, *other))
    return data_list_normalized

#chunks data into squares of dimensions chunk_size x chunk_size, averaging values in the square
def chunk_data(data_list, chunk_size):
    list_length = len(data_list)
    i = list_length
    while i > 0:
        values, lat, lon = data_list[i-1]
        try:
            values = block_average(values, chunk_size) #can throw Exception if trimming reduces size of area to 0
            lat = lat[::chunk_size]
            lon = lon[::chunk_size]
            data_list[i-1] = (values, lat, lon)
        except ValueError:
            del data_list[i-1]
        finally:
            i -= 1

        
#helper function for doing block averages
def block_average(matrix, n):
    ny, nx = matrix.shape
    ny_trim, nx_trim = ny - ny % n, nx - nx % n
    if ny_trim == 0 or nx_trim == 0:
        raise ValueError("Data Matrix is reduced to size 0 by trimming")
    trimmed = matrix[:ny_trim, :nx_trim]
    # Reshape into 4D and average apparently. It actually makes sense if you think about it
    return trimmed.reshape(ny_trim//n, n, nx_trim//n, n).mean(axis=(1,3))

#plot a single date of data
def plot_single(plot_container, data_list, coords = (9, 23, 21, 39), normalized = False):
    (southBound, northBound, westBound, eastBound) = coords
    
    tracked_min = 1
    tracked_max = 10 ** -18
    for values, _, _ in data_list:
        tile_min = np.min(np.where(values == 0, 1, values))
        tracked_min = tracked_min if tracked_min <= tile_min else tile_min
        tile_max = np.max(values)
        tracked_max = tracked_max if tracked_max >= tile_max else tile_max
    color_norm = colors.LogNorm(vmin = tracked_min, vmax = tracked_max)

    fig, ax = plt.subplots(figsize=(10,10), subplot_kw={"projection": ccrs.PlateCarree()})
    ax.coastlines()
    ax.add_feature(cfeature.BORDERS, edgecolor="black")
    ax.set_extent([westBound, eastBound, southBound, northBound])
    for values, lat, lon in data_list:
        mesh = ax.pcolormesh(
            lon, lat, np.where(values == 0, np.nan, values),
            cmap="inferno",  
            norm = color_norm, 
            shading="auto"
        )
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05, axes_class=plt.Axes)
    plt.colorbar(mesh, ax=ax, label="Brightness (nW/cm^2)" if not normalized else "Brightness (prop. of total)", cax = cax)
    plot_container.pyplot(fig)

#plot the difference between two dates of data
def plot_difference(plot_container, data_list, coords = (9, 23, 21, 39), normalized = False):
    (southBound, northBound, westBound, eastBound) = coords

    tracked_min = 1
    tracked_max = 10 ** -18
    tracked_abs_min = 1
    for values, _, _ in data_list:
        tile_min = np.min(np.where(values == 0, 1, values))
        tracked_min = tracked_min if tracked_min <= tile_min else tile_min
        tile_max = np.max(values)
        tracked_max = tracked_max if tracked_max >= tile_max else tile_max
        tile_abs_min = np.min(np.where(values == 0, 1, np.abs(values)))
        tracked_abs_min = tracked_abs_min if tracked_abs_min <= tile_abs_min else tile_abs_min
    color_norm = colors.SymLogNorm(linthresh= tracked_abs_min, linscale = 1, vmin = tracked_min, vmax = tracked_max)
        
    fig, ax = plt.subplots(figsize=(10,10), subplot_kw={"projection": ccrs.PlateCarree()})
    ax.coastlines()
    ax.add_feature(cfeature.BORDERS, edgecolor="black")
    ax.set_extent([westBound, eastBound, southBound, northBound])
    for values, lat, lon in data_list:
        mesh = ax.pcolormesh(
            lon, lat, np.where(values == 0, np.nan, values),
            cmap="inferno",  
            norm = color_norm, 
            shading="auto"
        )
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05, axes_class=plt.Axes)
    plt.colorbar(mesh, ax=ax, label="Difference in Brightness (nW/cm^2)" if not normalized else "Difference in Proportions of Brightness", cax = cax)
    plot_container.pyplot(fig)

#plot the relative difference between two dates of data
def plot_rel_difference(plot_container, data_list, coords = (9, 23, 21, 39), normalized = False):
    (southBound, northBound, westBound, eastBound) = coords

    tracked_min = 1
    tracked_max = 10 ** -18
    tracked_rel_max = 1
    tracked_rel_min = 10 ** -18

    for values, _, _ in data_list:
        tile_min = np.min(np.where(-values <= 0, 1, -values))
        tracked_min = tracked_min if tracked_min <= tile_min else tile_min
        tile_max = np.max(-values)
        tracked_max = tracked_max if tracked_max >= tile_max else tile_max
        tile_rel_max = np.max(values)
        tracked_rel_max = tracked_rel_max if tracked_rel_max >= tile_rel_max else tile_rel_max
        tile_rel_min = np.min(np.where(values <= 0, 1, values))
        tracked_rel_min = tracked_rel_min if tracked_rel_min <= tile_rel_min else tile_rel_min

    #plot two layers on the same map, one for the percent differences where starting data != 0, and one for the raw data with "new light"
    
    #map of new light
    fig, ax = plt.subplots(figsize=(10,10), subplot_kw={"projection": ccrs.PlateCarree()})
    ax.coastlines()
    ax.add_feature(cfeature.BORDERS, edgecolor="black")
    ax.set_extent([westBound, eastBound, southBound, northBound])
    for values, lat, lon in data_list:
        mesh_new = ax.pcolormesh(
            lon, lat, np.where(values >= 0, np.nan, -values),
            cmap="Greens",  
            norm = colors.LogNorm(vmin = tracked_min, vmax = tracked_max), 
            shading="auto"
        )
    divider = make_axes_locatable(ax)
    cax1 = divider.append_axes("left", size="5%", pad = .05, axes_class=plt.Axes)
    cbar1 = plt.colorbar(mesh_new, ax=ax, label="New Brightness (nW/cm^2)" if not normalized else "New Brightness (prop. of total)", cax=cax1)
    cbar1.ax.yaxis.set_label_position("left")
    cbar1.ax.yaxis.tick_left()

    #map of changed light
    for values, lat, lon in data_list:
        mesh_rel = ax.pcolormesh(
            lon, lat, np.where(values <= 0, np.nan, values),
            cmap="RdBu_r",  
            norm = colors.TwoSlopeNorm(vcenter = 1, vmin = 0, vmax = 3),
            shading="auto"
        )
    cax2 = divider.append_axes("right", size="5%", pad= .05, axes_class=plt.Axes)
    plt.colorbar(mesh_rel, ax=ax, label="Brightness Ratio", cax = cax2)

    plot_container.pyplot(fig)



#UI controls

st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)

#Coordinate Selection
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    preset_choice = st.selectbox("Preset coordinate layout", list(PRESET_COORD_LAYOUTS.keys()))
with col2:
    custom_coords_text = st.text_input("Or type coordinates as South, North, East, West", "")
with col3:
    st.markdown("<div style='margin-top: 1.8em;'></div>", unsafe_allow_html=True) #spacing
    apply_button = st.button("Apply")


col1, col2, col3 = st.columns([1, 2, 1])
with col1: #Mode selection
    mode = st.radio("Mode", ["Single", "Difference", "Relative"], index=0, horizontal=True)
with col2: #Downsampling
    downsample = st.number_input("Downsampling Factor: ", min_value=1, max_value=32, value=1, step=1)
    downsample_val = downsample
with col3: #Normalization
    st.markdown("<div style='margin-top: 2.2em;'></div>", unsafe_allow_html=True)
    normalize = st.checkbox("Normalize data", value=False)


# Date selectors depending on mode
available_dates = load_available_dates()
date_strings = [d.decode('utf-8') for d in available_dates]

if mode == "Single":
    sel_date = st.selectbox("Select date", date_strings, index=0)
    sel_date_obj = np.bytes_(sel_date)
    sel_date_obj_b = None
else:
    # For both Difference and Relative Difference, choose two dates
    col_a, col_b = st.columns(2)
    with col_a:
        sel_date_a = st.selectbox("Date A", date_strings, index=0, key="date_a")
        sel_date_obj = np.bytes_(sel_date_a)
    with col_b:
        sel_date_b = st.selectbox("Date B", date_strings, index=min(1, len(date_strings)-1), key="date_b")
        sel_date_obj_b = np.bytes_(sel_date_b)


# Coordinate selection handling
if custom_coords_text.strip():
    try:
        coords_vals = [float(x.strip()) for x in custom_coords_text.split(",")]
        if len(coords_vals) != 4:
            raise ValueError()
        coords = tuple(coords_vals)
    except Exception:
        st.error("Couldn't parse custom coordinates. Use: lat_min, lat_max, lon_min, lon_max")
        coords = tuple(PRESET_COORD_LAYOUTS[preset_choice].values())
else:
    p = PRESET_COORD_LAYOUTS[preset_choice]
    coords = (p["lat_min"], p["lat_max"], p["lon_min"], p["lon_max"])



# The placeholder that will contain the plot
plot_container = st.container()

# Controls specific to modes
if mode == "Single":
    if st.button("Render single plot"):
        data = load_data_for_date(sel_date_obj, coords)
        if downsample_val > 1:
            chunk_data(data, downsample_val)
        if normalize:
            data = normalize_data(data)
        plot_single(plot_container, data, coords = coords, normalized=normalize)
elif mode == "Difference":
    if st.button("Render difference plot"):
        data_list = get_difference_data(sel_date_obj, sel_date_obj_b, coords, chunk_size=downsample_val, normalize=normalize)
        plot_difference(plot_container, data_list, coords = coords, linThreshCoefficient=downsample_val if not normalize else 10**9, normalized=normalize)
else:  # Relative Comparison
    if st.button("Render relative plot"):
        data_list = get_difference_data(sel_date_obj, sel_date_obj_b, coords, chunk_size=downsample_val, normalize=normalize, relative=True)
        plot_rel_difference(plot_container, data_list, coords = coords, normalized=normalize)
