import streamlit as st

from utils import (
    read_stats_to_dataframe,
    create_tabs,
)

st.set_page_config(layout="wide")
st.markdown("# Швагер-Кубок 2022")
st.markdown(
    "Вихідні дані взяті з гугл-таблиці за [посиланням](https://docs.google.com/spreadsheets/d/1rvGhGGN45SY5AeFjvK6JDOw9P3P98u5M6qarIQEVei8/edit#gid=0)"
)
st.markdown("Помітили помилку? Пишіть [Олегу](https://fb.com/ptrvtch)")


def main():
    df_all = read_stats_to_dataframe("data/01_Швагер_Кубок_2022/*.csv")

    create_tabs(df_all)


main()
