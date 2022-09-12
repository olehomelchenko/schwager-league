from glob import glob
import streamlit as st
import pandas as pd
import numpy as np
import requests
import altair as alt
import re
from utils import transform_data, render_topic_stats, render_game_stats

st.markdown("# Швагер-кубок 2022")


def main():
    files = glob("data/01_Швагер_Кубок_2022/*.csv")
    files.sort()

    df_all = []
    for file in files:
        match = re.search(r"data/\d+_(?P<name>.*)/(?P<round>\d+).csv", file)
        df = pd.read_csv(file, header=[0, 1, 2, 3])
        df = transform_data(df)
        df["round"] = match.group("round")
        df_all.append(df)

    df = pd.concat(df_all)

    I_FILE_INPUT = st.selectbox("Оберіть коло", options=df["round"].unique())

    # I_ROUND_TABS = st.tabs(list(df['round'].unique()))

    df = df[df["round"] == I_FILE_INPUT]

    I_TAB_TOPIC_STATS, I_TAB_GAME_STATS = st.tabs(["Статистика тем", "Статистика боїв"])

    with I_TAB_TOPIC_STATS:
        results = render_topic_stats(df)
        for result in results:
            st.markdown(f"### {result['header']}")
            with st.expander("Питання"):
                st.markdown(result["questions_text"])
            st.altair_chart(result["chart"])

    with I_TAB_GAME_STATS:
        for result in render_game_stats(df):
            st.header(result["header"])
            st.write(result["results_table"])
            st.altair_chart(result["chart"])


main()
