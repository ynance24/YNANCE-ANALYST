
import streamlit as st
import json

st.title("Ynance Prototype UI")

# secrets.json 자동 로드
try:
    with open("secrets.json") as f:
        secrets = json.load(f)
    st.success("secrets.json loaded successfully!")
    st.write("Loaded Keys:", list(secrets.keys()))
except Exception as e:
    st.error("Failed to load secrets.json")
    st.write(e)

st.write("App is running.")
