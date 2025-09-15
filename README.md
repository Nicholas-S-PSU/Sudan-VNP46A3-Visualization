# Sudan-VNP46A3-Visualization
A simple streamlit app for extracting data from NASA's VNP46A3 dataset and building relevant visualizations, centered around Sudan

See https://sudan-vnp46a3-visualization-7vuekplxzvnave7k5wotpm.streamlit.app/ to see the app running

This file implements a simple UI for visualizing the progression of war in Sudan using satellite imagery
Nighttime lights are a common proxy for general human well-being. By inspecting changes in nighttime lights,
it is possible to monitor destruction, migration, and other war effects such as fires

Currently, it is set up for using the NASA Black Marble Data for Sudan, but the project can be easily generalized

To change the coordinates of the map, change PRESET_COORD_LAYOUTS, or type your coordinates manually. If you download appropriate data, this tool will work for anywhere in the world

Any .h5 data in the folder lead to by PATH_DEFAULT will be parsed and plotted by the program

To view other, differently formatted satellite data with sufficiently similar interpretations, change the file navigation in load_available_dates and load_data_from_date to match the format of your data. The remainder of the functionality should work fine

This project is packaged with (stripped down) data from February and March in 2023 and 2024 of the VNP46A3 dataset, the monthly Black Marble dataset from NASA. To download more, see https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/VNP46A3/#overview. The project should also work with the daily and yearly Black Marble uploads.

The code finds its data in a folder lead to by PATH_DEFAULT. At the moment, the app assumes the data starts in data.zip in the same directory as this app, extracts it, creates a folder /data, which PATH_DEFAULT is then set to. That way, it will work when deployed to streamlit or if you just download all of the files in this repository and run them. If you are running locally, feel free to just leave your files extracted in a folder of your choice and set PATH_DEFAULT manually,
commenting out and in the relevant lines at the top of the script

How to run:
  
  0. Either leave your data as data.zip in the same directory as the script, or set PATH_DEFAULT to the folder containing your datasets manually
  1. Open the folder containing this file in your preferred terminal
  2. Use "streamlit run "./sudan_damage_vis.py"" in your terminal.
  3. If streamlit is not in your PATH, you might need to use "py -m streamlit run "./sudan_damage_vis""

It will open in your browser
