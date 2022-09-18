import streamlit as st

from utils import (
    read_stats_to_dataframe,
    create_tabs,
)

st.set_page_config(layout="wide")
st.markdown("# Швагер-Ліга 2022 - Зима")
st.markdown(
    "Вихідні дані взяті з гугл-таблиці за [посиланням](https://docs.google.com/spreadsheets/d/16ZrwpH3bGRJKQ5W7KnI34io0Y_XPJeabCK9eu778UT0/edit#gid=0)"
)
st.markdown("Помітили помилку? Пишіть [Олегу](https://fb.com/ptrvtch)")


def main():
    df_all = read_stats_to_dataframe("data/03_Швагер-Ліга_2022_Зима/*.csv")

    create_tabs(df_all)


main()
