import pickle
from my_predictor import MyPredictor
from arduino_converter import *
from pretty_prints import *
from serial import Serial
from tqdm import trange


with open('./results_evaluation/5_learn_data.pkl', 'rb') as file:
    learn_data = pickle.load(file)

with open('./results_evaluation/5_test_data.pkl', 'rb') as file:
    test_data = pickle.load(file)

for exercises in trange(2, 6):
    current_learn_data = learn_data[:exercises]
    current_test_data = test_data[:exercises * 2]
    for cluster in trange(2, 16, leave=False):
        for components in trange(2, 16, leave=False):
            predictor = MyPredictor(current_learn_data, cluster_count=cluster,
                                    components_counts=[components] * exercises, init_count=3)
            prediction, timeline = predictor.predict(current_test_data, exercises)
            with open('./timeline.csv', 'a') as file:
                file.write(','.join(map(str, (exercises, cluster, components))))
                file.write(',')
                file.write(','.join(map(str, timeline)))
                file.write('\n')
            with open('./prediction.csv', 'a') as file:
                file.write(','.join(map(str, (exercises, cluster, components))))
                file.write(',')
                file.write(','.join(map(str, prediction)))
                file.write('\n')
