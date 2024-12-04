import matplotlib.pyplot as plt
import numpy as np


x = np.arange(1, 10, 2)
print(x)
plt.subplot(3, 1, 1)
plt.plot(x, np.sin(x))
plt.subplot(3, 1, 2)
plt.plot(x, np.cos(x))
plt.subplot(3, 1, 3)
plt.plot(x, x)
plt.show()
