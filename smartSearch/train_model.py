import pandas as pd
from ml_filter import LeadScorer
import numpy as np

# Sample training data - replace with your actual lead conversion data
data = {
    'text': [
        "Looking for IoT solutions for our factory",
        "Student project about sensors",
        "Need freelance developer for industrial automation",
        "Research paper about manufacturing"
    ],
    'is_good_lead': [1, 0, 1, 0]  # 1 = good lead, 0 = bad lead
}

def train_model():
    df = pd.DataFrame(data)
    scorer = LeadScorer()
    scorer.train(df['text'], df['is_good_lead'])
    print("Model trained and saved!")

if __name__ == "__main__":
    train_model()