import streamlit as st

from utils import (
    read_stats_to_dataframe,
    create_tabs,
)

st.set_page_config(layout="wide")
st.markdown("# Швагер-Суперкубок 2022")
st.markdown(
    "Вихідні дані взяті з гугл-таблиці за [посиланням](https://docs.google.com/spreadsheets/d/1m0ZW2ZseTqYK30SLz_un-MiDF508N93IKZ7X2wypZ-U/edit#gid=0)"
)
st.markdown("Помітили помилку? Пишіть [Олегу](https://fb.com/ptrvtch)")


def main():
    df_all = read_stats_to_dataframe("data/05_Швагер_Суперкубок_2022/*.csv")

    create_tabs(df_all)


main()
