import matplotlib.pyplot as plt
import numpy as np
a=np.array(['2016','2017','2018','2019','2020','2021','2022','2023','2024'])
b=np.array([989,1092,649,1022,899,784,988,1100,879])
plt.bar(a,b,color="hotpink")
plt.xlabel("Years",color="blue",size=20)
plt.ylabel("Runs",color="blue",size=20)
plt.suptitle("Virat Kohli Test Cricket Runs",color="red",size=30)
plt.show()
