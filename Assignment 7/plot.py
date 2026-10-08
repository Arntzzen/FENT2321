import pandas as pd

df = pd.read_csv("C:/Users/marku/Desktop/FENT2321/Assignment 7/power_rpm.csv", sep=";")

df = df.iloc[:, :2]

RPM = df["Rotational Speed [rpm]"]
P_W = df["Power [W]"]

