import matplotlib.pyplot as plt

turns = [20, 30, 40, 50, 60, 70, 80, 90, 100]
efficiency = [12.8, 21.0, 25.1, 27.6, 29.3, 30.4, 31.3, 32.0, 32.6]

plt.plot(turns, efficiency, marker='o')

plt.xlabel("Number of Turns")
plt.ylabel("Efficiency (%)")
plt.title("Efficiency vs. Number of Turns")
plt.grid(True)

plt.show()
