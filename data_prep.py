#!/usr/bin/env python
# coding: utf-8

# In[15]:


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
data=pd.read_excel(r"C:\Users\DELL\Desktop\OLA_DataSet.xlsx")
data


# In[19]:


data.shape


# In[17]:


data.head()


# In[12]:


data.info()


# In[13]:


data.isnull().sum()


# In[21]:


df=data.fillna(0)
df


# In[26]:


df=data.drop("Vehicle Images",axis=1)
df


# In[27]:


df.duplicated().sum()


# In[28]:


df.columns


# In[29]:


plt.figure(figsize=(10, 5))
sns.countplot(x='Booking_Status', data=df, palette='viridis', order=df['Booking_Status'].value_counts().index)
plt.title('Distribution of Booking Status', fontsize=15)
plt.ylabel('Count')
plt.show()


# In[30]:


# Which vehicle is most popular?
plt.figure(figsize=(10, 6))
top_vehicles = df['Vehicle_Type'].value_counts().head(10)

sns.barplot(x=top_vehicles.values, y=top_vehicles.index, palette='magma')
plt.title('Top 10 Requested Vehicle Types', fontsize=15)
plt.xlabel('Number of Bookings')
plt.show()


# In[31]:


# 1. Cancellations by Drivers
driver_cancel_reasons = df['Canceled_Rides_by_Driver'].value_counts().head(5)

# 2. Cancellations by Customers
customer_cancel_reasons = df['Canceled_Rides_by_Customer'].value_counts().head(5)

# Plotting side by side
fig, axes = plt.subplots(1, 2, figsize=(18, 6))

sns.barplot(x=driver_cancel_reasons.values, y=driver_cancel_reasons.index, ax=axes[0], palette='Reds_r')
axes[0].set_title('Top Reasons: Driver Cancellations')

sns.barplot(x=customer_cancel_reasons.values, y=customer_cancel_reasons.index, ax=axes[1], palette='Blues_r')
axes[1].set_title('Top Reasons: Customer Cancellations')

plt.tight_layout()
plt.show()


# In[32]:


# Let's look at Successful rides only for revenue analysis
success_df = df[df['Booking_Status'] == 'Success']

fig, ax = plt.subplots(1, 2, figsize=(16, 6))

# Histogram of Ride Cost
sns.histplot(success_df['Booking_Value'], bins=30, kde=True, ax=ax[0], color='green')
ax[0].set_title('Distribution of Booking Prices (Success Rides)')
ax[0].set_xlabel('Price (Currency)')

# Boxplot of Distance by Vehicle Type
sns.boxplot(x='Vehicle_Type', y='Ride_Distance', data=success_df, ax=ax[1], palette='Set2')
ax[1].set_title('Ride Distance Distribution by Vehicle Type')
ax[1].tick_params(axis='x', rotation=45)

plt.show()


# In[ ]:




