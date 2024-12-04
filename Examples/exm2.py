#subplot
import matplotlib.pyplot as plt
import numpy as np

#plot 1
x = np.array([4, 1, 2, 3])
y = np.array([3, 8, 1, 10])

plt.subplot(1, 3, 1)
plt.title("plot 1")
plt.plot(x,y)

#plot 2
x = np.array([2, 1, 2, 3])
y = np.array([10, 20, 30, 40])

plt.subplot(1, 3, 2)
plt.title("plot 2")
plt.plot(x,y)

#plot 3
x=np.array([3,4,2,8])
y=np.array([23,54,98,23])
plt.subplot(1,3,3)
plt.title("plot 3")
plt.plot(x,y)
plt.suptitle("Subplot",color="red",size=20)
plt.show()