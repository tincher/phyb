import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits import mplot3d
import numpy as np
from matplotlib import cm
import matplotlib.pyplot as plt

def make_figure(x, y, z, path, exercise_count):
    fig = plt.figure()
    ax = plt.axes(projection='3d')
    ax.plot_surface(x, y, z, cmap=cm.coolwarm)
    ax.set_title('{} Übungen'.format(exercise_count))
    ax.set_xlim3d(2, 15)
    ax.set_ylim3d(2, 10)
    ax.set_zlim3d(0, 1)
    ax.set_xlabel('Clusteranzahl')
    ax.set_ylabel('Ausführungen in der Trainingsphase')
    ax.set_zlabel('% erkannt')

    plt.savefig(path)


def f(xs, ys, exercises, all_data):
    Z = []
    for x in set(xs[0]):
        x_accuracy = []
        for y in set(ys[:,0]):
            truth = []
            for i in range(exercises):
                truth.extend([i]*2)
            data = [something for something in all_data if something[1]==x and something[2]==y][0]
            recognition_data = data[-2*exercises:]
            accuracy = list(map(lambda elem: elem[0] == elem[1], list(zip(truth, recognition_data)))).count(True) / (exercises * 2)
            x_accuracy.append(accuracy)
        Z.append(x_accuracy)
    return np.array(Z).T

def load_data(path):
    with open(path) as file:
        content = file.read()
        lines = content.split('\n')
        result = []
        for line in lines:
            if line != '':
                result.append(list(map(int, line.split(','))))
    return result


if __name__ == '__main__':
    data = load_data('./timeline.csv')
    for exercises_count in range(2, 6):
        exercise_data = np.array([x for x in data if x[0] == exercises_count])
        x = exercise_data[:,1]
        y = exercise_data[:,2]
        X = list(set(x))
        Y = list(set(y))
        Xs, Ys = np.meshgrid(X, Y)

        Z = f(Xs, Ys, exercises_count, exercise_data)

        path = './{}_graph.png'.format(exercises_count)
        make_figure(Xs, Ys, Z, path, exercises_count)
