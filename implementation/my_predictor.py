import numpy as np
import pickle
from hmmlearn import hmm
import sys
from sklearn.cluster import KMeans
import math

class MyPredictor:
    '''Predictor handles the learning and the prediction.

    Parameters
    ----------
    exercise_data : array_like
        The data from the learning phase
    cluster_count : int
        k for the k-means (the default is 5).
    components_counts : array_like
        how many hidden states the HMMs will have (the default is [3, 3]).
    init_count : int
        how often the HMMs are initialized (the default is 5).

    Attributes
    ----------
    all_exercises_data : array_like
        the data points grouped by the exercises and executions
    all_data : array_like
        all data in a flat structure
    kmeans : sklearn.cluster.KMeans
        object containing the k-means
    HMMs : array_like
        HMMs for each exercise which will be recognized.
    components_counts

    '''
    def __init__(self, exercise_data, cluster_count=5, components_counts=[3, 3], init_count=5):
        self.all_exercises_data = exercise_data
        self.all_data = None
        for exercise in self.all_exercises_data:
            for run in exercise:
                run = np.array(run)
                self.all_data = run if self.all_data is None else np.concatenate((self.all_data, run))
        self.kmeans = KMeans(n_clusters=cluster_count).fit(self.all_data)
        self.HMMs = [None] * len(exercise_data)
        self.components_counts = components_counts
        self.learn(cluster_count, init_count)

    def learn(self, cluster_count, init_count):
        ''''Set the k-means and learn the HMMs

        Parameters
        ----------
        cluster_count : int
            k for the k-means
        init_count : int
            how often the HMMs should be initialized

        Returns
        -------
        None
        '''
        best_score = -sys.maxsize
        for i, exercise_data in enumerate(self.all_exercises_data):
            exercise_labels = []
            for run in exercise_data:
                run_labels = self.kmeans.predict(np.array(run).reshape(-1, 6))
                exercise_labels.append(run_labels)
            lengths = [len(run_labels) for run_labels in exercise_labels]
            exercise_labels = np.concatenate(exercise_labels).reshape((-1, 1))
            for j in range(init_count):
                current_hmm = hmm.MultinomialHMM(n_components=self.components_counts[i], n_iter=100)
                current_hmm.fit(exercise_labels, lengths)
                current_score = current_hmm.score(exercise_labels, lengths)
                if j < 1:
                    self.HMMs[i] = current_hmm
                    best_score = current_score
                    continue
                if current_score > best_score:
                    self.HMMs[i] = current_hmm
                    best_score = current_score
        for i, current_hmm in enumerate(self.HMMs):
            if current_hmm.emissionprob_.shape[1] < cluster_count:
                additional_columns = np.zeros((self.components_counts[i], cluster_count -
                                               current_hmm.emissionprob_.shape[1])) + 1e-2
                current_hmm.n_features = cluster_count
                current_hmm.emissionprob_ = np.hstack((current_hmm.emissionprob_, additional_columns))

    def predict(self, data, exercise_count):
        '''Predict which exercises are done.

        Parameters
        ----------
        data : array_like
            Data points captured for the exercises.
        exercise_count : int
            Number of exercises that could be recognised.

        Returns
        -------
        tuple
            counter: array_like of how often the exercises are recognised
            timeline: for each execution: what exercise this is recognised as
        '''
        counter = [0] * exercise_count
        timeline = []
        for run in data:
            labels = self.kmeans.predict(run)
            labels = labels.reshape((-1, 1))
            current_score, best_score, best_fit_index = 0, -math.inf, exercise_count
            for i, current_hmm in enumerate(self.HMMs):
                current_score = current_hmm.score(labels)
                if current_score > best_score:
                    best_score = current_score
                    best_fit_index = i
            counter[best_fit_index] += 1
            timeline.append(best_fit_index)
        return counter, timeline

    def save_model(self, path='./predictor.pkl'):
        '''Saves the current model.

        Parameters
        ----------
        path : string
            Path where to save the model (the default is './predictor.pkl').

        Returns
        -------
        None
        '''
        with open(path, 'wb') as file:
            pickle.dump(self, file)

    def load_model(self, path='./predictor.pkl'):
        '''Loads a saved model.

        Parameters
        ----------
        path : string
            Path to the saved model (the default is './predictor.pkl').
        Returns
        -------
        None
        '''
        with open(path, 'rb') as file:
            self = pickle.load(file)
