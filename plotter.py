import matplotlib.pyplot as plt
from brain import df, avg_prices

# 1. Create the figure
plt.figure(figsize=(10, 6))

# 2. Plot every single house as a green dot
# alpha=0.5 makes the dots semi-transparent so overlapping houses look darker
plt.scatter(df['Beds'], df['Price'], color='green', alpha=0.5, label='Individual Houses')

# 3. Plot the average price as a red line with markers
plt.plot(avg_prices.index, avg_prices.values, color='red', marker='o', linestyle='dashed', linewidth=2, label='Market Average')

# 4. Format the Price axis to be readable (not scientific notation)
plt.ticklabel_format(style='plain', axis='y')

# 5. Add Labels and Title
plt.title("Real Estate Market Detective: Price Distribution", fontsize=14)
plt.xlabel('Number of Bedrooms', fontsize=12)
plt.ylabel('Price (Naira)', fontsize=12)
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.7)

# 6. Show the plot
plt.tight_layout()
plt.show()