# RFM Analysis with K-Means Clustering - Customer Segmentation
# Simplified version assuming clean data with required columns

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set plotting style
plt.style.use('default')
sns.set_palette("husl")

print("🚀 Starting RFM Analysis with K-Means Clustering")
print("=" * 60)

# STEP 1: Load Data
print("STEP 1: Loading Data")
print("-" * 30)
df = pd.read_csv('customer_segment_agg.csv')
print(f"✓ Data loaded: {df.shape[0]} rows, {df.columns.tolist()}")
print(df.head())

# STEP 2: Calculate RFM Metrics
print("\nSTEP 2: Calculating RFM Metrics")
print("-" * 30)

# Convert purchase_date to datetime
df['purchase_date'] = pd.to_datetime(df['purchase_date'])

# Set analysis date (current date or max date + 1)
analysis_date = df['purchase_date'].max() + pd.Timedelta(days=1)
print(f"Analysis date: {analysis_date.strftime('%Y-%m-%d')}")

# Calculate RFM for each customer
rfm = df.groupby('customer_id').agg({
    'purchase_date': lambda x: (analysis_date - x.max()).days,  # Recency
    'customer_id': 'count',                                     # Frequency  
    'amount': 'sum'                                            # Monetary
}).reset_index()

# Rename columns
rfm.columns = ['customer_id', 'recency', 'frequency', 'monetary']

print(f"✓ RFM calculated for {len(rfm)} customers")
print("\nRFM Summary:")
print(rfm.describe())

# STEP 3: Visualize RFM Distributions
print("\nSTEP 3: Visualizing RFM Distributions")
print("-" * 30)

fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle('RFM Distributions', fontsize=16)

# Recency
axes[0].hist(rfm['recency'], bins=30, alpha=0.7, color='skyblue')
axes[0].set_title('Recency (Days since last purchase)')
axes[0].set_xlabel('Days')

# Frequency  
axes[1].hist(rfm['frequency'], bins=30, alpha=0.7, color='lightgreen')
axes[1].set_title('Frequency (Number of purchases)')
axes[1].set_xlabel('Purchases')

# Monetary
axes[2].hist(rfm['monetary'], bins=30, alpha=0.7, color='salmon')
axes[2].set_title('Monetary (Total spent)')
axes[2].set_xlabel('Amount ($)')

plt.tight_layout()
plt.show()

# STEP 4: Normalize RFM Values
print("\nSTEP 4: Normalizing RFM Values")
print("-" * 30)

# Apply log transformation to reduce skewness
rfm_log = rfm.copy()
rfm_log['recency_log'] = np.log1p(rfm_log['recency'])
rfm_log['frequency_log'] = np.log1p(rfm_log['frequency']) 
rfm_log['monetary_log'] = np.log1p(rfm_log['monetary'])

# Standardize the values
scaler = StandardScaler()
rfm_scaled = scaler.fit_transform(rfm_log[['recency_log', 'frequency_log', 'monetary_log']])
rfm_normalized = pd.DataFrame(rfm_scaled, columns=['recency_scaled', 'frequency_scaled', 'monetary_scaled'])

print("✓ RFM values normalized using log transformation + StandardScaler")
print("Normalized data shape:", rfm_normalized.shape)

# STEP 5: Find Optimal Number of Clusters (Elbow Method)
print("\nSTEP 5: Finding Optimal Number of Clusters")
print("-" * 30)

# Calculate WCSS for different k values
k_range = range(2, 11)
wcss = []
silhouette_scores = []

for k in k_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(rfm_normalized)
    wcss.append(kmeans.inertia_)
    silhouette_scores.append(silhouette_score(rfm_normalized, kmeans.labels_))

# Plot Elbow Method
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# WCSS Plot
ax1.plot(k_range, wcss, 'bo-')
ax1.set_title('Elbow Method - WCSS')
ax1.set_xlabel('Number of Clusters (k)')
ax1.set_ylabel('WCSS')
ax1.grid(True)

# Silhouette Score Plot
ax2.plot(k_range, silhouette_scores, 'ro-')
ax2.set_title('Silhouette Score')
ax2.set_xlabel('Number of Clusters (k)')
ax2.set_ylabel('Silhouette Score')
ax2.grid(True)

plt.tight_layout()
plt.show()

# Choose optimal k (you can adjust this based on the plots)
optimal_k = 4
print(f"✓ Optimal number of clusters selected: {optimal_k}")

# STEP 6: Apply K-Means Clustering
print("\nSTEP 6: Applying K-Means Clustering") 
print("-" * 30)

# Fit K-Means with optimal k
kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
cluster_labels = kmeans.fit_predict(rfm_normalized)

# Add cluster labels to original RFM dataframe
rfm['cluster'] = cluster_labels

print(f"✓ K-Means clustering completed with {optimal_k} clusters")
print(f"Silhouette Score: {silhouette_score(rfm_normalized, cluster_labels):.3f}")

# STEP 7: Analyze Clusters
print("\nSTEP 7: Analyzing Clusters")
print("-" * 30)

# Calculate cluster statistics
cluster_summary = rfm.groupby('cluster').agg({
    'recency': ['mean', 'median'],
    'frequency': ['mean', 'median'], 
    'monetary': ['mean', 'median'],
    'customer_id': 'count'
}).round(2)

cluster_summary.columns = ['recency_mean', 'recency_median', 'frequency_mean', 'frequency_median', 
                          'monetary_mean', 'monetary_median', 'customer_count']

print("Cluster Summary:")
print(cluster_summary)

# STEP 8: Label Clusters Based on RFM Characteristics
print("\nSTEP 8: Labeling Clusters")
print("-" * 30)

# Create a function to assign meaningful labels
def assign_cluster_labels(row):
    if row['recency_mean'] <= rfm['recency'].median() and row['frequency_mean'] >= rfm['frequency'].median() and row['monetary_mean'] >= rfm['monetary'].median():
        return 'Champions'
    elif row['recency_mean'] <= rfm['recency'].median() and row['frequency_mean'] < rfm['frequency'].median():
        return 'Potential Loyalists'
    elif row['recency_mean'] > rfm['recency'].median() and row['frequency_mean'] >= rfm['frequency'].median():
        return 'At Risk'
    else:
        return 'Lost'

# Apply labels
cluster_summary['segment_label'] = cluster_summary.apply(assign_cluster_labels, axis=1)

print("Cluster Labels:")
for idx, row in cluster_summary.iterrows():
    print(f"Cluster {idx}: {row['segment_label']} ({row['customer_count']} customers)")

# STEP 9: Visualize Clusters
print("\nSTEP 9: Visualizing Clusters")
print("-" * 30)

# 3D Scatter Plot
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

colors = ['red', 'blue', 'green', 'orange', 'purple']
for i in range(optimal_k):
    cluster_data = rfm[rfm['cluster'] == i]
    ax.scatter(cluster_data['recency'], cluster_data['frequency'], cluster_data['monetary'], 
              c=colors[i], label=f'Cluster {i}: {cluster_summary.loc[i, "segment_label"]}', alpha=0.6)

ax.set_xlabel('Recency (Days)')
ax.set_ylabel('Frequency (Purchases)')
ax.set_zlabel('Monetary (Amount)')
ax.set_title('RFM Customer Segments - 3D View')
ax.legend()
plt.show()

# 2D Plots
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Recency vs Frequency
for i in range(optimal_k):
    cluster_data = rfm[rfm['cluster'] == i]
    axes[0].scatter(cluster_data['recency'], cluster_data['frequency'], 
                   c=colors[i], label=f'Cluster {i}', alpha=0.6)
axes[0].set_xlabel('Recency (Days)')
axes[0].set_ylabel('Frequency (Purchases)')
axes[0].set_title('Recency vs Frequency')
axes[0].legend()

# Frequency vs Monetary
for i in range(optimal_k):
    cluster_data = rfm[rfm['cluster'] == i]
    axes[1].scatter(cluster_data['frequency'], cluster_data['monetary'], 
                   c=colors[i], label=f'Cluster {i}', alpha=0.6)
axes[1].set_xlabel('Frequency (Purchases)')
axes[1].set_ylabel('Monetary (Amount)')
axes[1].set_title('Frequency vs Monetary')
axes[1].legend()

# Recency vs Monetary
for i in range(optimal_k):
    cluster_data = rfm[rfm['cluster'] == i]
    axes[2].scatter(cluster_data['recency'], cluster_data['monetary'], 
                   c=colors[i], label=f'Cluster {i}', alpha=0.6)
axes[2].set_xlabel('Recency (Days)')
axes[2].set_ylabel('Monetary (Amount)')
axes[2].set_title('Recency vs Monetary')
axes[2].legend()

plt.tight_layout()
plt.show()

# STEP 10: Business Insights and Recommendations
print("\nSTEP 10: Business Insights and Recommendations")
print("-" * 30)

print("\n📊 CUSTOMER SEGMENT ANALYSIS")
print("=" * 50)

for idx, row in cluster_summary.iterrows():
    segment_label = row['segment_label']
    customer_count = row['customer_count']
    percentage = (customer_count / len(rfm)) * 100
    
    print(f"\n🎯 {segment_label.upper()} (Cluster {idx})")
    print(f"   Customers: {customer_count} ({percentage:.1f}%)")
    print(f"   Avg Recency: {row['recency_mean']:.1f} days")
    print(f"   Avg Frequency: {row['frequency_mean']:.1f} purchases") 
    print(f"   Avg Monetary: ${row['monetary_mean']:.2f}")
    
    # Recommendations based on segment
    if segment_label == 'Champions':
        print("   💡 Strategy: Reward loyalty, exclusive offers, referral programs")
    elif segment_label == 'Potential Loyalists':
        print("   💡 Strategy: Nurture with personalized offers, encourage repeat purchases")
    elif segment_label == 'At Risk':
        print("   💡 Strategy: Win-back campaigns, limited-time offers, feedback surveys")
    elif segment_label == 'Lost':
        print("   💡 Strategy: Minimal investment, reactivation campaigns, exit surveys")

# STEP 11: Save Results
print("\nSTEP 11: Saving Results")
print("-" * 30)

# Add segment labels to customer data
segment_mapping = cluster_summary['segment_label'].to_dict()
rfm['segment'] = rfm['cluster'].map(segment_mapping)

# Save detailed results
rfm.to_csv('rfm_customer_segments.csv', index=False)
cluster_summary.to_csv('rfm_cluster_summary.csv')

print("✓ Results saved:")
print("  - rfm_customer_segments.csv (detailed customer segments)")
print("  - rfm_cluster_summary.csv (cluster summary statistics)")

print(f"\n🎉 RFM Analysis Complete!")
print(f"Total customers analyzed: {len(rfm)}")
print(f"Segments identified: {optimal_k}")
print("=" * 60)