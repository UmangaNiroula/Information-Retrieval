import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

# Load data from CSV file
df = pd.read_csv('filtered_data.csv')

# Drop rows with missing values in 'Title' or 'Excerpt' columns
df = df.dropna(subset=['Title', 'Excerpt'])

# TF-IDF vectorization
vectorizer = TfidfVectorizer(max_df=0.5, min_df=2, stop_words='english', use_idf=True)
tfidf_matrix = vectorizer.fit_transform(df['Title'] + ' ' + df['Excerpt'])

# Clustering (K-means)
n_clusters = 3  # Number of clusters
kmeans = KMeans(n_clusters=n_clusters, random_state=42)

# Add cluster labels to DataFrame
df['Cluster'] = kmeans.fit_predict(tfidf_matrix)

# Create a dictionary mapping cluster labels to categories
cluster_to_category = {cluster: df[df['Cluster'] == cluster]['Category'].iloc[0] for cluster in range(n_clusters)}

# Predict cluster for user input
def predict_cluster(input_text):
    input_vector = vectorizer.transform([input_text])
    cluster = kmeans.predict(input_vector)[0]
    category = cluster_to_category[cluster]
    return cluster, category

def process_input():
    input_text = text_box.get("1.0", tk.END).strip()  # Remove leading/trailing whitespaces
    if not input_text:  # Check if input is empty
        # Show error message
        predicted_cluster_label.config(text="No input provided!", fg="red")
        predicted_category_label.config(text="")
        print("Error: No input provided!")
    else:
        # Show buffering message
        predicted_cluster_label.config(text="Predicting cluster...", fg="blue")
        predicted_category_label.config(text="")
        window.update()  # Update the GUI to display the message
        
        cluster, category = predict_cluster(input_text)
        predicted_cluster_label.config(text=f"Predicted Cluster: {cluster}", fg="green")
        predicted_category_label.config(text=f"Predicted Category: {category}", fg="green")
        print("Predicted Cluster:", cluster)
        print("Category Name:", category)

# Tkinter GUI
window = tk.Tk()
window.title("Document Clustering - Task 2")
window.geometry("590x480")  # Set window size

# Set background color
window.configure(bg="#f0f0f0")

# Set font styles
font_style = ("Helvetica", 12)

text_box = ScrolledText(window, font=font_style)
text_box.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

# Add 3D effect to labels
predicted_cluster_label = tk.Label(window, text="Cluster No Prediction:", relief="groove", font=font_style)
predicted_cluster_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")

predicted_category_label = tk.Label(window, text="Cluster Category Prediction:", relief="groove", font=font_style)
predicted_category_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")

# Customize button appearance
btn = tk.Button(window, text="Submit", command=process_input, relief="raised", bd=3, font=font_style)
btn.grid(row=3, column=0, padx=10, pady=10)

window.mainloop()
