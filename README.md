# turbofan-degradation-analysis-rul-NASA
Aerospace predictive maintenance project using NASA CMAPSS turbofan engine data. It analyzes sensor readings, calculates Remaining Useful Life, visualizes degradation trends, and trains a machine learning model to predict engine failure risk, helping prioritize maintenance before breakdowns occur.
# Turbofan RUL Predictor

This project uses NASA’s CMAPSS Turbofan Engine Degradation Dataset to predict aircraft engine health and estimate Remaining Useful Life (RUL). The goal is to support aerospace predictive maintenance by identifying engines that may need inspection before failure.

## Project Goal

The main question this project answers is:

> Given turbofan engine sensor readings over time, how many cycles does an engine have left before failure?

## Dataset

The dataset used is NASA’s CMAPSS Turbofan Engine Degradation Dataset.

Key variables include:

- `unit`: engine ID
- `cycle`: operating cycle
- `setting1`, `setting2`, `setting3`: operating conditions
- `sensor1` through `sensor21`: engine sensor readings
- `RUL`: Remaining Useful Life

## Workflow

This project includes:

- Data loading and cleaning
- Remaining Useful Life calculation
- Exploratory data analysis
- RUL trend visualization
- Feature engineering with rolling sensor statistics
- Machine learning model training
- Model evaluation and recommendations

## Model

A Gradient Boosting Regressor was trained to predict RUL from engine sensor data.

Model results:

- RMSE: 34.15 cycles
- MAE: 24.77 cycles
- R²: 0.729

## Key Insight

Rolling sensor trends were more useful than single sensor readings. Sensors such as `sensor4`, `sensor11`, and `sensor15` were strong indicators of engine degradation.

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
