import cli_ui


def print_prediction(names, predictions):
    print('Ergebnis:')
    for name, prediction in zip(names, predictions):
        print('Übung: {}, Anzahl: {}'.format(name, prediction))


def print_countdown_when_ready(seconds=3):
    user_is_ready = False
    while not user_is_ready:
        user_is_ready = cli_ui.ask_yes_no('Bereit?', default=True)
    for i in range(seconds)[::-1]:
        time.sleep(1)
        print(i + 1)
    print_circle(cli_ui.yellow)


def print_learning_for_activity(activity, learning_runs_per_exercise):
    print('Führen Sie sobald der grüne Kreis erscheint {} {} aus'.format(learning_runs_per_exercise, activity))
    print('Nach der Ausführung der {} drücken Sie STRG-C'.format(activity))


def print_circle(color):
    big_dot = cli_ui.UnicodeSequence(color, '⬤', 'O')
    cli_ui.info(big_dot)
