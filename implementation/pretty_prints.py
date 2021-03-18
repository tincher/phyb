import cli_ui
from num2words import num2words


def print_prediction(predictions):
    print('Ergebnis:')
    for i, prediction in enumerate(predictions):
        number_name = num2words(i + 1, lang='de', to='ordinal')
        print('{} Übung: {}'.format(number_name, prediction))


def print_countdown_when_ready(seconds=3):
    user_is_ready = False
    while not user_is_ready:
        user_is_ready = cli_ui.ask_yes_no('Bereit?', default=True)
    for i in range(seconds)[::-1]:
        time.sleep(1)
        print(i + 1)
    print_circle(cli_ui.yellow)


def print_learning_for_activity(counter, learning_runs_per_exercise):
    number_name = num2words(counter + 1, lang='de', to='ordinal')
    print('Führen Sie sobald der grüne Kreis erscheint die {} Übung {} mal aus'.format(number_name, learning_runs_per_exercise))
    print('Nach der Ausführung jeder Ausführung drücken Sie STRG-C')


def print_circle(color):
    big_dot = cli_ui.UnicodeSequence(color, '⬤', 'O')
    cli_ui.info(big_dot)
