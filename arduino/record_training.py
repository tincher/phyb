import cli_ui
import pickle
from my_predictor import MyPredictor
from arduino_converter import *
from pretty_prints import *
from serial import Serial

# -------------------------------------------------
# TODO documentation
# -------------------------------------------------


if __name__ == '__main__':
    exercise_count = 5
    learning_runs_per_exercise = 15
    learn_data = []

    print('Recording')
    for i in range(exercise_count):
        print_learning_for_activity(i, learning_runs_per_exercise)
        print_countdown_when_ready(0)
        exercise_data = read_from_arduino(learning_runs_per_exercise)
        learn_data.append(exercise_data)
        with open('./learn_data.pkl', 'wb') as file:
            pickle.dump(learn_data, file)

    # predictor = MyPredictor(learn_data, cluster_count=5, components_counts=[5, 5])
