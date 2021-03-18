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
    exercise_count = 2
    learning_runs_per_exercise = 5
    learn_data = []

    print('LERNPHASE')
    for i in range(exercise_count):
        print_learning_for_activity(i, learning_runs_per_exercise)
        print_countdown_when_ready(0)
        exercise_data = read_from_arduino(learning_runs_per_exercise)
        learn_data.append(exercise_data)

    predictor = MyPredictor(learn_data, cluster_count=5, components_counts=[5, 5])

    print('Lernphase beendet')
    print()
    print('Erkennen ab jetzt möglich!')

    count = int(cli_ui.ask_string('Wie viele Ausführungen werden Sie machen?', default=5))
    print_countdown_when_ready(0)
    recognition_data = read_from_arduino(count)
    prediction, _ = predictor.predict(recognition_data, exercise_count)
    print_prediction(exercise_count, prediction)
