import streamlit as st

from utils import (
    read_stats_to_dataframe,
    create_tabs,
)

st.set_page_config(layout="wide")
st.markdown("# Швагер-Ліга 2022 - Зима")


def main():
    df_all = read_stats_to_dataframe("data/01_Швагер_Ліга_2021-22/*.csv")

    create_tabs(df_all)


main()
