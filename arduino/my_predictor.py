import numpy as np
import pickle
from hmmlearn import hmm
import sys
from sklearn.cluster import KMeans
import pdb


class MyPredictor:
    def __init__(self, exercise_data, cluster_count=4, components_counts=[3, 3]):
        self.all_exercises_data = exercise_data
        self.all_data = np.concatenate(exercise_data, axis=None).reshape(-1, 1)
        print(self.all_data.shape)
        self.kmeans = KMeans(n_clusters=cluster_count).fit(self.all_data)
        self.HMMs = [None] * len(exercise_data)
        self.components_counts = components_counts
        self.learn()

    def learn(self, components_count=10, cluster_count=10):
        best_score = sys.maxsize

        for i, exercise_data in enumerate(self.all_exercises_data):
            pdb.set_trace()
            exercise_labels = self.kmeans.predict(exercise_data.reshape(-1, 6))
            X = exercise_labels.reshape((-1, 1))
            # TODO nicht korrekt
            lengths = [len(run) for run in exercise_data]
            for j in range(5):
                current_hmm = hmm.MultinomialHMM(n_components=self.components_counts[i], n_iter=100)
                current_hmm.fit(X)
                if j < 1:
                    self.HMMs[i] = current_hmm
                    continue
                score = self.HMMs[i].score(exercise_data, lengths)
                if score < best_score:
                    self.HMMs[i] = current_hmm

    def predict(self, data):
        result = {'Kniebeuge': 0, 'Situp': 0}

        labels = self.kmeans.predict(data)
        labels = labels.reshape((-1, 1))
        prediction = model.predict(labels)
        with open('prediction.txt', 'w') as prediction_file:
            prediction_file.write(str(prediction))
        # TODO really count
        return result

    def save_model(self, path='./model.pkl'):
        with open(path, 'wb') as file:
            pickle.dump(self.HMM, file)

    def load_model(self, path='./model.pkl'):
        with open(path, 'rb') as file:
            self.HMM = pickle.load(file)
