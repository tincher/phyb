import numpy as np
x = np.linspace(-6, 6, 20)
y = np.linspace(-6, 6, 30)
def f(x, y):
   return np.sin(np.sqrt(x ** 2 + y ** 2))

X, Y = np.meshgrid(x, y)
Z = f(X, Y)
print(Z.shape)
