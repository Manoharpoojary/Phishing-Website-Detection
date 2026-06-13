# Phishing URL Detector App

A web application that analyzes URLs to detect phishing websites using machine learning.

## Features

- URL feature extraction from multiple sources
- Machine learning prediction using XGBoost
- Professional UI with glass morphism effects
- Real-time analysis with confidence scores

## Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the application:

```bash
cd src/App
python app.py
```

3. Open your browser and go to `http://127.0.0.1:5000`

## Usage

1. Enter a URL in the input field
2. Click "Analyze URL"
3. View the results showing whether the site is legitimate or phishing, along with confidence scores

## Architecture

- `feature_extraction.py`: Extracts 48 features from URLs including structural, content, and behavioral features
- `scaling.py`: Standardizes features using StandardScaler fitted on training data
- `predict.py`: Loads the trained XGBoost model and makes predictions
- `report.py`: Formats prediction results
- `app.py`: Flask web application with professional UI
- `templates/index.html`: HTML template with glass morphism styling

## Model

Uses XGBoost model trained on phishing dataset with 98.67% test accuracy.
