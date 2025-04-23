import joblib
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
import numpy as np

ML_MODEL_PATH = "lead_scoring_model.pkl"
VECTORIZER_PATH = "tfidf_vectorizer.pkl"

class LeadScorer:
    def __init__(self):
        # Initialize with dummy trained model
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.model = RandomForestClassifier(n_estimators=50, random_state=42)
        
        # Train with dummy data if no saved model exists
        if not os.path.exists(ML_MODEL_PATH):
            self._train_with_dummy_data()
        else:
            self.load_models()
    
    def _train_with_dummy_data(self):
        """Train with minimal dummy data to ensure basic functionality"""
        dummy_texts = ["business opportunity", "looking to buy", "seeking services"]
        dummy_labels = [1, 1, 1]  # All positive as dummy examples
        X = self.vectorizer.fit_transform(dummy_texts)
        self.model.fit(X, dummy_labels)
        self.save_models()
    
    def load_models(self):
        """Load trained models from disk"""
        try:
            self.model = joblib.load(ML_MODEL_PATH)
            self.vectorizer = joblib.load(VECTORIZER_PATH)
        except Exception as e:
            print(f"Error loading models: {e}")
            self._train_with_dummy_data()
    
    def save_models(self):
        """Save models to disk"""
        joblib.dump(self.model, ML_MODEL_PATH)
        joblib.dump(self.vectorizer, VECTORIZER_PATH)
    
    def train(self, X, y):
        """Train with actual data"""
        X_vec = self.vectorizer.fit_transform(X)
        self.model.fit(X_vec, y)
        self.save_models()
    
    def predict_proba(self, text):
        """Safe prediction with fallback"""
        try:
            if not hasattr(self.model, 'estimators_'):  # Check if model is trained
                return 0.5  # Neutral score if model isn't ready
            
            X_vec = self.vectorizer.transform([text])
            return self.model.predict_proba(X_vec)[0][1]  # Probability of positive class
        except Exception as e:
            print(f"Prediction error: {e}")
            return 0.5  # Fallback neutral score