# PathogenBreak 🌾
**Disease-aware crop-rotation advisor for Indore (Malwa), Madhya Pradesh** — built on NASA Earth observation data, pathogen databases and a live soil sensor.

Indore is sliding into a soybean–wheat monoculture (gram area −89% since 2019, UPAg). Growing the same hosts every year lets soil-borne fungi (*Fusarium*, *Rhizoctonia*, *Macrophomina*) build up. PathogenBreak scores every feasible 2-year rotation on crop fit, disease carry-over, nitrogen benefit and irrigation need, stress-tests it across 13 real crop years + 3 climate shocks, and tells the farmer what to sow **today** — in English or Hindi.

## Key results (Indore, normal year)
| Option | Rotation | Disease vs today | Irrigation | Income vs today (MSP) |
|---|---|---|---|---|
| Today | Soybean → Wheat → Soybean → Wheat | — | 500 mm | — |
| Keep income | Maize → Wheat → Soybean → Wheat | −17% | 500 mm | −2% |
| Strongest break | Maize → Gram → Soybean → Wheat | −45% | 300 mm | −21% |
| Pilot plot | Groundnut → Mustard → Soybean → Wheat | −54% | 350 mm | +2% |

## How NASA data is used
| Dataset | Use |
|---|---|
| NASA POWER `T2M`, `PRECTOTCORR`, `RH2M` | Season climate → crop fit, irrigation need, humid-year disease pressure, 16 stress scenarios |
| NASA POWER `GWETTOP` | Live sensor reading ranked against 13 years of soil wetness → field action |
| GPM IMERG (NASA/JAXA) | Satellite rainfall, cross-checked with POWER (r = 0.98) |
| MODIS MOD13A3 EVI | Validates the crop calendar and tracks real wheat production |

Other data: SoilGrids 2.0, UPAg (Govt. of India), USDA Fungus–Host Distributions, PHI-base v5.7, MSP 2026-27.

## Run it
```bash
pip install -r requirements.txt jupyterlab ipywidgets
jupyter lab              # open PathogenBreak_final.ipynb -> Restart & Run All
streamlit run app.py     # farmer app (English / हिंदी)
```

## Repository
- `PathogenBreak_final.ipynb` – full analysis (11 cells)
- `app.py` – farmer advisory app (runs the notebook's model)
- `data/` – cleaned datasets
- `hardware/pathogenbreak_sensor_node.ino` – Arduino soil sensor + LCD + HC-05 Bluetooth

## Limitations
USDA records mean "found on", not "proven to cause disease"; suitability curves, weights, sowing windows and field actions are literature-based assumptions (sensitivity-tested); across 55 MP districts more repetition goes with slightly lower yields but not significantly — a field trial is the next step; the sensor needs field calibration.

**Use of AI:** Code and text were developed with the help of an AI assistant (Claude, Anthropic); data choices, testing and decisions were made by the team.
