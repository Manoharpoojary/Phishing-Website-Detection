import pickle
import os
# from scaling import FeatureScaler  # Not needed

class PhishingPredictor:
    def __init__(self, model_path=None):
        if model_path is None:
            # Default path to XGBoost model
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            model_path = os.path.join(base_dir, 'models', 'xgb_model.pkl')

        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)

        # self.scaler = FeatureScaler()  # Not needed
        # self.scaler.fit()  # Not needed

    def predict(self, features_df):
        """Predict if URL is phishing (1) or legitimate (0)"""
        # Don't scale features - model expects raw features?
        # scaled_features = self.scaler.transform(features_df)

        # Predict
        prediction = self.model.predict(features_df)[0]
        probability = self.model.predict_proba(features_df)[0]

        return {
            'prediction': int(prediction),
            'probability_phishing': float(probability[1]),
            'probability_legitimate': float(probability[0])
        }