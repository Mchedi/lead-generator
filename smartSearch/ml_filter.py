import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

ML_MODEL_PATH = "lead_scoring_model.pkl"
VECTORIZER_PATH = "tfidf_vectorizer.pkl"

class LeadScorer:
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.load_models()
        
    def load_models(self):
        """Load pre-trained models or initialize new ones"""
        if os.path.exists(ML_MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
            self.model = joblib.load(ML_MODEL_PATH)
            self.vectorizer = joblib.load(VECTORIZER_PATH)
        else:
            self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            self.model = RandomForestClassifier(n_estimators=100)
            # You'll need to train these with actual data
    
    def train(self, X, y):
        """Train the model with labeled data"""
        X_vec = self.vectorizer.fit_transform(X)
        self.model.fit(X_vec, y)
        joblib.dump(self.model, ML_MODEL_PATH)
        joblib.dump(self.vectorizer, VECTORIZER_PATH)
    
    def predict_proba(self, text):
        """Predict probability of being a good lead"""
        if not self.model or not self.vectorizer:
            return 0.5  # Neutral score if models not loaded
        
        X_vec = self.vectorizer.transform([text])
        return self.model.predict_proba(X_vec)[0][1]  # Probability of being positive class
    
    def calculate_similarity(self, text1, text2):
        """Calculate semantic similarity between two texts"""
        vecs = self.vectorizer.transform([text1, text2])
        return cosine_similarity(vecs[0:1], vecs[1:2])[0][0]