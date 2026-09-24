import pandas as pd
import os

# Les CSV-filen
df = pd.read_csv("./assignment 4/assignment3_data.csv")

# Skriv til Excel
df.to_excel("./assignment 4/assignment3_data.xlsx", index=False)

print("Filen er konvertert til assignment3_data.xlsx")

# print("Working directory:", os.getcwd())
# print("Filer her:", os.listdir())