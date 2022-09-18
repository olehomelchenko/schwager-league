from glob import glob
import streamlit as st
import pandas as pd
import re
from utils import (
    get_total_stats,
    transform_data,
    render_topic_stats,
    render_game_stats,
    get_total_stats, generate_scatter
)

st.set_page_config(layout="wide")
st.markdown("# Швагер-кубок 2022")


def main():
    files = glob("data/01_Швагер_Кубок_2022/*.csv")
    files.sort()

    df_all = []
    for file in files:
        match = re.search(r"data/\d+_(?P<name>.*)/(?P<round>\d+).csv", file)
        df = pd.read_csv(file, header=[0, 1, 2, 3])
        rnd = match.group("round")
        df = transform_data(df, rnd=rnd)
        df_all.append(df)

    df_all = pd.concat(df_all)

    (
        I_TAB_TOTALS,
        I_TAB_TOPIC_STATS,
        I_TAB_GAME_STATS,
    ) = st.tabs(["Загалом", "Статистика тем", "Статистика боїв"])

    with I_TAB_TOTALS:
        chart = generate_scatter(df_all)

        st.altair_chart(chart)
        total_stats = get_total_stats(df_all, "round")
        st.write(total_stats)

        st.write(df_all)

        for i, g in df_all.groupby("round"):
            f"""Коло {i}"""
            st.dataframe(get_total_stats(g, "Тема"))

    with I_TAB_TOPIC_STATS:
        I_FILE_INPUT = st.selectbox(
            "Оберіть коло",
            options=df_all["round"].unique(),
            format_func=lambda x: f"Коло {x}",
        )

        df = df_all[df_all["round"] == I_FILE_INPUT]

        results = render_topic_stats(df)
        for result in results:
            st.markdown(f"### {result['header']}")
            with st.expander("Питання теми"):
                st.markdown(result["questions_text"])
            st.altair_chart(result["chart"])
            st.markdown(result["stats"])

    with I_TAB_GAME_STATS:
        for result in render_game_stats(df):
            st.header(result["header"])
            st.write(result["results_table"])
            st.altair_chart(result["chart"])


main()
