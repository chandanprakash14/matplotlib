import matplotlib.pyplot as plt
import numpy as np

stu_performace=np.array(["Excellent","Good","Avg","Poor"])
stu_values=np.array([15,25,12,8])
plt.pie(stu_values,labels=stu_performace,autopct='%1.1f%%')
plt.title("Students Performance")
plt.show()
