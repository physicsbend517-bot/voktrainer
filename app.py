
import streamlit as st

st.title("Meine Python-App")
st.write("Die App läuft jetzt im Browser!")

name = st.text_input("Wie heißt du?")

if st.button("Absenden"):
    st.success(f"Hallo {name}!")
