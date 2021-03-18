import cli_ui
import pickle
from my_predictor import MyPredictor
from arduino_converter import *
from pretty_prints import *
from serial import Serial

if __name__ == '__main__':
    count = int(cli_ui.ask_string('Wie viele Ausführungen werden Sie machen?', default=8))
    print_countdown_when_ready(0)
    recognition_data = read_from_arduino(count)
    with open('./test_data.pkl', 'wb') as file:
        pickle.dump(recognition_data, file)
