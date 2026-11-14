PATHOGENBREAK - disease-aware crop rotation planner for Indore (MP)

FIRST TIME ON A NEW LAPTOP (Command Prompt)
  py -m venv pbenv
  pbenv\Scripts\activate
  pip install pandas numpy matplotlib jupyterlab ipywidgets streamlit

EVERY TIME
  pbenv\Scripts\activate
  cd <this folder>            (right-click folder -> Copy as path)

A) NOTEBOOK (full analysis)
  jupyter lab
  -> open PathogenBreak_final.ipynb -> Kernel -> Restart Kernel and Run All Cells (~30 s)

B) FARMER APP (simple demo screen)
  streamlit run app.py
  -> opens in the browser; first load takes ~15 s (it runs the notebook's model)
  -> stop with Ctrl+C in the Command Prompt

NOTEBOOK CELLS
  1 Load 7 datasets        5 Calendar rules + water + 2-yr simulator   9  Validation vs real data
  2 Season climate         6 Uncertainty engine (16 scenarios, 81      10 Dashboard + export
  3 Pathogen carry-over      weight settings)                          11 Live sensor -> action -> LCD
  4 Crop suitability       7 Farmer check: income (MSP + mandi), water,      (slider + goal buttons)
                             3 options
                           8 Pathogen heat-map

OUTPUT FILES (made by the notebook)
  dashboard.png, validation.png, rotation_evidence.png, pathogen_heatmap.png, pathogenbreak_results.csv

LIVE SENSOR (Cell 11)
  SENSOR_PORT = None   -> demo mode (slider)
  SENSOR_PORT = "COM5" -> real Arduino / HC-05 (pip install pyserial)
  SENSOR_CSV  = "soil_data.csv" -> replay a logged file (set DRY_RAW / WET_RAW calibration first)
  Arduino code: hardware/pathogenbreak_sensor_node.ino

KEY RESULTS (normal year, Indore)
  Today            Soybean -> Wheat -> Soybean -> Wheat
  Keep income      Maize -> Wheat -> Soybean -> Wheat      disease -17%, income -2%
  Strongest break  Maize -> Gram -> Soybean -> Wheat       disease -45%, 200 mm less irrigation, income -21%
  Pilot plot       Groundnut -> Mustard -> Soybean -> Wheat disease -54%, 150 mm less irrigation, income +2%
