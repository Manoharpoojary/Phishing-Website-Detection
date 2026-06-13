from flask import Flask, render_template, request, jsonify
from feature_extraction import extract_all_features
from predict import PhishingPredictor
from report import ReportGenerator
import traceback

app = Flask(__name__)

# Initialize predictor
predictor = PhishingPredictor()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        url = request.form.get('url', '').strip()

        if not url:
            return jsonify(ReportGenerator.generate_error_report(url, "URL is required"))

        # Extract features
        features_df = extract_all_features(url)

        # Predict
        prediction_result = predictor.predict(features_df)

        # Generate report
        report = ReportGenerator.generate_report(url, prediction_result)

        return jsonify(report)

    except Exception as e:
        error_msg = f"Error processing URL: {str(e)}"
        print(traceback.format_exc())
        return jsonify(ReportGenerator.generate_error_report(url, error_msg))

if __name__ == '__main__':
    app.run(debug=True)