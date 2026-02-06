# import matplotlib.pyplot as plt
# from brain import run_analysis
# import sys

# def main():
#     # 1. Run the data analysis engine
#     print("Starting Market Detective analysis...")
#     df, avg_prices = run_analysis(num_pages=1) # Quick run for now
    
#     if df.empty:
#         print("No data found to plot. Exiting.")
#         sys.exit(0)

#     # 2. Create the figure
#     print("Generating market visualizations...")
#     plt.figure(figsize=(10, 6))

#     # 3. Plot every single house as a green dot
#     # alpha=0.5 makes the dots semi-transparent so overlapping houses look darker
#     plt.scatter(df['Bedrooms'], df['Price'], color='green', alpha=0.5, label='Individual Houses')

#     # 4. Plot the average price as a red line with markers
#     plt.plot(avg_prices.index, avg_prices.values, color='red', marker='o', linestyle='dashed', linewidth=2, label='Market Average')

#     # 5. Format the Price axis to be readable (not scientific notation)
#     plt.ticklabel_format(style='plain', axis='y')

#     # 6. Add Labels and Title
#     plt.title("Real Estate Market Detective: Price Distribution", fontsize=14)
#     plt.xlabel('Number of Bedrooms', fontsize=12)
#     plt.ylabel('Price (Naira)', fontsize=12)
#     plt.legend()
#     plt.grid(axis='y', linestyle='--', alpha=0.7)

#     # 7. Show the plot
#     plt.tight_layout()
#     print("Plot displayed. Please close the plot window to finish.")
#     plt.show()

#     # 8. Clean exit
#     print("\n[✔] Analysis complete. Terminal closing cleanly.")
#     sys.exit(0)

# if __name__ == "__main__":
#     main()