import pandas as pd
import matplotlib.pyplot as plt
import os

df = pd.read_csv('donations.csv')  # Make sure your CSV has data!

os.makedirs('static/charts', exist_ok=True)

# Chart 1: Safe vs Unsafe
safe_counts = df['Safe to Donate'].value_counts()
safe_counts.plot(kind='bar', color=['#4CAF50', '#F44336'])
plt.title('Safe vs Unsafe Donations')
plt.savefig('static/charts/safety_chart.png')
plt.clf()

# Chart 2: Food Types
food_counts = df['Food Type'].value_counts()
food_counts.plot(kind='bar', color='#2196F3')
plt.title('Most Donated Food Items')
plt.savefig('static/charts/food_chart.png')
plt.clf()

print("✅ Charts generated successfully!")
