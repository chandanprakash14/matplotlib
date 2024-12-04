from matplotlib import pyplot as plt
marks=[90,50,40,60,55,44,30,10,34,84,69]
grade_intervals=[0,35,70,100]
plt.title("Student Grade")
plt.hist(marks,grade_intervals,color='red')
plt.xticks([0,35,70,100])
plt.xlabel("percentage")
plt.ylabel("No of Students")
plt.show()