# Turbofan RUL Predictor

Aerospace predictive maintenance project using NASA's CMAPSS Turbofan Engine Degradation Dataset. This project analyzes turbofan engine sensor readings, calculates Remaining Useful Life (RUL), and identifies engines that should be prioritized for maintenance before failure.

## Project Goal

The main question this project answers is:

> Given turbofan engine sensor readings over time, how many cycles does an engine have left before failure?

## Dataset

The dataset is based on NASA's CMAPSS Turbofan Engine Degradation Dataset.

Key variables include:

- `unit`: engine ID
- `cycle`: operating cycle
- `setting1`, `setting2`, `setting3`: engine operating conditions
- `sensor1` through `sensor21`: engine sensor measurements
- `RUL`: Remaining Useful Life

This repo includes a small sample CMAPSS-style CSV so the project can run quickly. For a full project, replace the sample data with NASA's FD001 training data.

## Workflow

This project includes:

- Data loading and cleaning
- Remaining Useful Life calculation
- Engine health scoring
- Risk labeling for maintenance priority
- Exploratory analysis and summary reporting
- Results export to CSV and Markdown

The larger Zerve workflow also included RUL trend visualization, rolling-window feature engineering, and a Gradient Boosting model for RUL prediction.

## Model Result From Zerve Workflow

A Gradient Boosting Regressor was trained to predict RUL from engine sensor data.

Model results:

- RMSE: 34.15 cycles
- MAE: 24.77 cycles
- R2: 0.729

## Key Insight

Rolling sensor trends were more useful than single sensor readings. Sensors such as `sensor4`, `sensor11`, and `sensor15` were strong indicators of engine degradation.

## Run The Mini Project

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the standalone Python demo:

```bash
python turbofan_project.py
```

Run the CSV-based analysis:

```bash
python src/analyze_turbofan.py
```

Generated outputs are saved in the `results/` folder.

## Project Structure

```text
.
├── README.md
├── requirements.txt
├── turbofan_project.py
├── data/
│   └── sample_turbofan.csv
├── src/
│   └── analyze_turbofan.py
└── results/
    ├── latest_engine_scores.csv
    └── summary.md
```

## Recommendation

Engines with low predicted RUL should be prioritized for inspection or maintenance. This helps reduce unexpected failures, improve safety, and support better maintenance planning.

## Tech Stack

- Python
- Pandas
- NumPy
- Matplotlib
- Scikit-learn
- Zerve

## License

This project is licensed under the MIT License.

NASA CMAPSS data belongs to its original source and is used for educational purposes.
