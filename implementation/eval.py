import pickle
from my_predictor import MyPredictor
from arduino_converter import *
from pretty_prints import *
from serial import Serial
import numpy as np
from tqdm import trange


with open('./results_evaluation/5_learn_data.pkl', 'rb') as file:
    learn_data = pickle.load(file)

with open('./results_evaluation/5_test_data.pkl', 'rb') as file:
    test_data = pickle.load(file)

for exercises in trange(2, 6):
    for training_length in trange(4, 16, leave=False):
        current_learn_data = np.array(learn_data[:exercises], dtype=object)[:, :training_length]
        current_test_data = test_data[:exercises * 2]
        for cluster in trange(2, 10, leave=False):
            predictor = MyPredictor(current_learn_data, cluster_count=cluster,
                                    components_counts=[5] * exercises, init_count=3)
            prediction, timeline = predictor.predict(current_test_data, exercises)
            with open('./only_length_timeline.csv', 'a') as file:
                file.write(','.join(map(str, (exercises, training_length, cluster, 5))))
                file.write(',')
                file.write(','.join(map(str, timeline)))
                file.write('\n')
            with open('./only_length_prediction.csv', 'a') as file:
                file.write(','.join(map(str, (exercises, training_length, cluster, 5))))
                file.write(',')
                file.write(','.join(map(str, prediction)))
                file.write('\n')
