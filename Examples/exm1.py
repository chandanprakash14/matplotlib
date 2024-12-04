
import matplotlib.pyplot as plt
import numpy as np
x1 = np.array([25, 27, 28, 27, 22, 17, 32, 39, 44, 22, 32, 49, 61])
y1 = np.array([99, 86, 87, 88, 111, 86, 103, 87, 94, 78, 77, 85, 86])
plt.scatter(x1, y1, color='blue', label='Day 1')
x2 = np.array([22, 34, 58, 21, 15, 48, 12, 39, 27, 43, 11, 34, 27, 14, 12])
y2 = np.array([100, 105, 84, 105, 90, 99, 90, 95, 94, 100, 79, 112, 91, 80, 85])
plt.scatter(x2, y2, color='red', label='Day 2')
plt.xlabel("Age")
plt.ylabel("Speed")
plt.legend()
plt.show()
