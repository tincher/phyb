with open('./states_0.txt') as states_file:
    states_0 = list(map(int, states_file.read().replace('\n', '').replace('[', '').replace(']', '').split(' ')))
with open('./states_1.txt') as states_file:
    states_1 = list(map(int, states_file.read().replace('\n', '').replace('[', '').replace(']', '').split(' ')))
with open('./prediction.txt') as pred_file:
    prediction = list(map(int, pred_file.read().replace('\n', '').replace('[', '').replace(']', '').split(' ')))


def clean(states):
    result = []
    last = None
    for state in states:
        if state != last:
            last = state
            result.append(state)
    return result


print(clean(states_0))
print(clean(states_1))
print(clean(prediction))
