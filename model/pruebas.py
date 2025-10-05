import pandas as pd

df = pd.read_csv("koi_table.csv", sep=",", comment="#")

print(df.shape)
print(df.columns.tolist())
print(df.head())
