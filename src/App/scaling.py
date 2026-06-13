import pandas as pd
from sklearn.preprocessing import StandardScaler
import os

class FeatureScaler:
    def __init__(self):
        self.scaler = StandardScaler()
        self.is_fitted = False

    def fit(self, X_train_path=None):
        """Fit the scaler on training data"""
        if X_train_path is None:
            # Default path
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            X_train_path = os.path.join(base_dir, 'datasets', 'processedData', 'X_train.csv')

        X_train = pd.read_csv(X_train_path)
        self.scaler.fit(X_train)
        self.is_fitted = True
        return self

    def transform(self, features_df):
        """Transform features using fitted scaler"""
        if not self.is_fitted:
            raise ValueError("Scaler must be fitted before transforming")
        return pd.DataFrame(
            self.scaler.transform(features_df),
            columns=features_df.columns
        )

    def fit_transform(self, features_df):
        """Fit and transform in one step"""
        self.scaler.fit(features_df)
        self.is_fitted = True
        return pd.DataFrame(
            self.scaler.transform(features_df),
            columns=features_df.columns
        )