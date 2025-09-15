# Sudan-VNP46A3-Visualization
A simple streamlit app for extracting data from NASA's VNP46A3 dataset and building relevant visualizations, centered around Sudan

This file implements a simple UI for visualizing the progression of war in Sudan using satellite imagery
Nighttime lights are a common proxy for general human well-being. By inspecting changes in nighttime lights,
it is possible to monitor destruction, migration, and other war effects such as fires

Currently, it is set up for using the NASA Black Marble Data for Sudan, but the project can be easily generalized

To change the coordinates of the map, change PRESET_COORD_LAYOUTS, or type your coordinates manually. If you download appropriate data, this tool will work for anywhere in the world

Any data in the folder lead to by PATH_DEFAULT will be parsed and plotted by the program

To view other, differently formatted satellite data with sufficiently similar interpretations, change the file navigation in load_available_dates and load_data_from_date to match the format of your data. The remainder of the functionality should work fine

This project is packaged with (stripped down) data from March 2023 and 2024 of the VNP46A3 dataset, the monthly Black Marble dataset from NASA. To download more, see https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/VNP46A3/#overview. GitHub doesn't allow large uploads, hence why I only included 2 months worth. The project should also work with the daily and yearly Black Marble uploads

How to run:
  
  0. Set PATH_DEFAULT to the folder containing your datasets
  1. Open the folder containing this file in your preferred terminal
  2. Use "streamlit run "./sudan_damage_vis.py"" in your terminal.
  3. If streamlit is not in your PATH, you might need to use "py -m streamlit run "./sudan_damage_vis""

It will open in your browser
