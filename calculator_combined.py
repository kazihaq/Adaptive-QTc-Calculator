# -*- coding: utf-8 -*-
"""
Created on Thu Jun 26 16:11:27 2025

@author: nikki
"""

import pandas as pd
import numpy as np
import scipy.io
import math

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ModuleNotFoundError:
    HAS_STREAMLIT = False
    print("Warning: Streamlit is not installed. GUI features are disabled.")
import base64


def set_background(image_file):
    with open(image_file, "rb") as file:
        encoded_string = base64.b64encode(file.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded_string}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Set the background (put this near the top of your script)
set_background("background.png")

# Load threshold CSV
threshold_df = pd.read_csv("threshold.csv")

# Preprocess age_range column into min_age and max_age
age_ranges = []
for entry in threshold_df['age_range']:
    if '-' in entry:
        start, end = map(int, entry.split('-'))
        age_ranges.append((start, end))
    else:
        val = int(entry)
        age_ranges.append((val, val))

threshold_df['min_age'] = [a[0] for a in age_ranges]
threshold_df['max_age'] = [a[1] for a in age_ranges]

def classify_qtc(age, qtc):
    match = threshold_df[(threshold_df['min_age'] <= age) & (age <= threshold_df['max_age'])]
    if not match.empty:
        row = match.iloc[0]
        if qtc < row['lower']:
            return "Normal"
        elif row['lower'] <= qtc <= row['upper']:
            return "Borderline"
        else:
            return "Prolonged"
    else:
        return "Age not found"

def load_data():
    data = scipy.io.loadmat("m_interp_data.mat")
    return {
        'Age_interp': data['Age_interp'].flatten(),
        'm_interp_all': data['m_interp_all'].flatten(),
        'm_interp_black_other': data['m_interp_black_other'].flatten(),
        'm_interp_female': data['m_interp_female'].flatten(),
        'm_interp_male': data['m_interp_male'].flatten(),
        'm_interp_white': data['m_interp_white'].flatten(),
        'neo_BO_HR': data['neo_BO_HR'].flatten(),
        'neo_BO_m': data['neo_BO_m'].flatten(),
        'neo_W_HR': data['neo_W_HR'].flatten(),
        'neo_W_m': data['neo_W_m'].flatten(),
        'neo_all_HR': data['neo_all_HR'].flatten(),
        'neo_all_m': data['neo_all_m'].flatten(),
        'neo_age': data['neo_age'].flatten()
    }

data = load_data()

if HAS_STREAMLIT:
    
    st.markdown("<h1 style='color:black;'>QTcAd Calculator</h1>", unsafe_allow_html=True)
    

    st.markdown("<p style='font-size:20px; color:#FFFFFF ;'>This calulator computes adaptive QTc and classify for risk startification</p>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:20px; color:#FFFFFF ;'>For details please visit : https://www.ahajournals.org/doi/abs/10.1161/CIRCEP.124.013237 </p>", unsafe_allow_html=True)

    st.markdown("<p style='font-size:16px; color:#FFFFFF;'>Enter the following demographic and ECG parameters:</p>", unsafe_allow_html=True)


    #st.title("QTcAd Calculator")
    #st.markdown("Enter the following demographic and ECG parameters:")

    age = st.number_input("Age (in days)", min_value=1)
    heart_rate = st.number_input("Heart Rate (bpm)", min_value=40)
    QT = st.number_input("QT Interval (ms)", min_value=200)
    race = st.selectbox("Race", ["", "White", "Black", "Other"])
    sex = st.selectbox("Sex", ["", "Male", "Female"])

    if st.button("Calculate QTc and Classify"):
        QTc = np.nan
        QTc_eq = np.nan
        QTc_interp = np.nan

        if age <= 34:
            try:
                idx = np.where(data['neo_age'] == age)[0][0]
                if race == "White":
                    HR = data['neo_W_HR'][idx]
                    m = data['neo_W_m'][idx]
                elif race in ["Black", "Other"]:
                    HR = data['neo_BO_HR'][idx]
                    m = data['neo_BO_m'][idx]
                else:
                    HR = data['neo_all_HR'][idx]
                    m = data['neo_all_m'][idx]

                QTc = round(QT + m * (heart_rate - HR), 0)
                classification = classify_qtc(age, QTc)
                st.markdown(
                    f"""
                    <div style="background-color: white; padding: 12px; border-radius: 8px; border: 1px solid #ddd;">
                        <span style="color: black; font-weight: bold; font-size: 18px;">QTc = {QTc} ms</span><br>
                        <span style="color: black; font-weight: bold; font-size: 18px;">Classification: {classification}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )


            except IndexError:
                st.error("Age not found in neonatal dataset.")

        else:
            HR_eq = -15.9 * math.log(age) + 219
            m_eq = 0.0001 * age + 1
            QTc_eq = round(QT + m_eq * (heart_rate - HR_eq))

            if age < len(data['m_interp_all']):
                m_interp = data['m_interp_all'][age]
                if 366 <= age < 2826:
                    if race == "White":
                        m_interp = data['m_interp_white'][age]
                    elif race in ["Black", "Other"]:
                        m_interp = data['m_interp_black_other'][age]
                elif 2826 <= age < 6571:
                    if sex == "Female":
                        m_interp = data['m_interp_female'][age]
                    elif sex == "Male":
                        m_interp = data['m_interp_male'][age]

                HR_interp = -15.9 * math.log(age) + 219
                QTc_interp = QT + m_interp * (heart_rate - HR_interp)

                classification = classify_qtc(age, QTc_eq)
                st.markdown(
                    f"""
                    <div style="background-color: white; padding: 12px; border-radius: 8px; border: 1px solid #ddd;">
                        <span style="color: black; font-weight: bold; font-size: 18px;">QTc = {QTc_eq} ms</span><br>
                        <span style="color: black; font-weight: bold; font-size: 18px;">Classification: {classification}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.warning("Age exceeds interpolation data range.")

else:
    print("Streamlit not available. Cannot display GUI.")
