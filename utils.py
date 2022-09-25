import numpy as np
import pandas as pd
import altair as alt
from glob import glob
import re
import streamlit as st


def read_stats_to_dataframe(glob_string: str):
    files = glob(glob_string)
    files.sort()

    df_all = []
    for file in files:
        match = re.search(r"data/\d+_(?P<name>.*)/(?P<round>\d+).csv", file)
        df = pd.read_csv(file, header=[0, 1, 2, 3])
        rnd = match.group("round")
        df = transform_data(df, rnd=rnd)
        df_all.append(df)

    df_all = pd.concat(df_all)
    return df_all


def transform_data(df, rnd):
    df.columns = ["🇺🇦".join(col).strip() for col in df.columns.values]
    df.rename(columns={df.columns[0]: "Тема", df.columns[1]: "Питання"}, inplace=True)
    df = df[~df["Тема"].isnull()]
    df = df.melt(id_vars=["Тема", "Питання"])
    df["value"] = df["value"].fillna(0).astype(int)
    df["val_emoji"] = np.select(
        [df["value"] == 1, df["value"] == 0, df["value"] == -1],
        ["✅", "⚪️", "❌"],
        default="🤷🏼",
    )
    df[["Game", "Name", "примітка", "c2"]] = df.variable.str.split("🇺🇦", expand=True)
    df["price"] = df["Питання"].str.extract(r"([^.]+)").astype(int)
    df["topic"] = df["Тема"].str.extract(r"([^.]+)")
    df["topic"] = df["topic"].str.pad(2)
    df["qid"] = df.agg("{0[topic]}.{0[price]}".format, axis=1)
    df["round"] = rnd
    df["gid"] = df.agg("{0[round]}.{0[Game]}".format, axis=1)
    df["pts"] = df["price"] * df["value"]
    df["pts_plus"] = np.select([df["value"] > 0], [df["pts"]], default=0)
    df["pts_minus"] = np.select([df["value"] < 0], [df["pts"]], default=0)
    df["pts_abs"] = df["pts_plus"] - df["pts_minus"]  # total value of activity
    df.drop(columns=["variable", "c2"], inplace=True)
    return df


def render_topic_stats(df):
    res_by_qid = (
        df.groupby(["qid", "Тема", "Питання", "price", "val_emoji"])
        .agg({"value": "count", "Name": ", ".join})
        .reset_index()
    )
    result = []
    for i, g in res_by_qid.groupby("Тема"):
        base = (
            alt.Chart(g.query("val_emoji in ['✅', '❌', '⚪️']"))
            .mark_bar()
            .encode(
                x=alt.X("val_emoji:O", title=None),
                y=alt.Y("value:Q", title=None),
                color=alt.Color(
                    "val_emoji:N",
                    scale=alt.Scale(
                        domain=["✅", "❌", "⚪️"], range=["green", "red", "grey"]
                    ),
                    legend=None,
                ),
                tooltip=["Name"],
            )
            .properties(height=200, width=100)
        )
        text = base.mark_text(dy=-10).encode(text="value")

        result.append(
            {
                "header": i,
                "questions_text": "\n\n---\n".join(g["Питання"].unique()),
                "chart": (base + text).facet(column=alt.Column("qid:N", title=None)),
                "stats": "",
            }
        )
    return result


def render_game_stats(df):
    result = []
    for i, g in df.groupby("Game"):
        totals = (
            g.query("val_emoji in ['✅', '❌']")
            .groupby("Name")
            .agg(
                {
                    "pts": "sum",
                    "pts_plus": "sum",
                    "pts_minus": "sum",
                    "price": "max",
                }
            )
            .rename(
                columns={
                    "pts": "Балли",
                    "pts_plus": "В плюс",
                    "pts_minus": "В мінус",
                    "price": "макс. ном.",
                }
            )
            .sort_values("Балли", ascending=False)
        )
        results = g.pivot(index="Name", columns="qid", values="val_emoji")

        g["cumsum"] = g.groupby("Name")["pts"].cumsum()
        g["q"] = g["Питання"]
        chart = (
            alt.Chart(g[["Name", "pts", "cumsum", "qid", "Питання", "Тема"]])
            .mark_line(opacity=0.7, point=True)
            .encode(
                x=alt.X("qid:N", title=None),
                y=alt.Y("cumsum:Q", title=None),
                color="Name:N",
                tooltip=["Тема:N", "Питання:N"],
            )
            .properties(width=800)
        )
        r = {
            "header": i,
            "results_table": totals.join(results),
            "chart": chart,
        }
        result.append(r)
    return result


def get_total_stats(df, split_by):

    total_stats = (
        df.groupby(split_by)
        .agg(
            {
                "Тема": "first",
                "pts": "sum",
                "pts_plus": "sum",
                "pts_minus": "sum",
                "Name": pd.Series.nunique,
            }
        )
        .rename(
            columns={
                "pts_plus": "В Плюс",
                "pts_minus": "В Мінус",
                "pts": "Балли",
                "Name": "Бої",
            }
        )
    )
    total_stats["Сер. Балли за тему"] = total_stats["Балли"] / total_stats["Бої"]
    total_stats["Сер. Плюси за тему"] = total_stats["В Плюс"] / total_stats["Бої"]
    total_stats["Сер. Мінуси за тему"] = total_stats["В Мінус"] / total_stats["Бої"]

    return total_stats


def generate_scatter(df):
    base = (
        alt.Chart(df)
        .mark_circle(opacity=0.5)
        .encode(
            x="sum(pts_plus):Q",
            y=alt.Y("sum(pts_minus):Q", scale=alt.Scale(reverse=True)),
            color="round:N",
            detail="Тема",
            tooltip=[
                alt.Tooltip("round:N", title="Коло"),
                alt.Tooltip("Тема", title="Тема"),
                alt.Tooltip("sum(pts)", title="Балли"),
                alt.Tooltip("sum(pts_plus)", title="В плюс"),
                alt.Tooltip("sum(pts_minus)", title="В мінус"),
            ],
            size=alt.Size("sum(pts_abs):Q", legend=None),
        )
    )

    text = (
        alt.Chart(df)
        .mark_text(opacity=0.9, align="left", dx=-0, dy=-20)
        .encode(
            x="sum(pts_plus):Q",
            y=alt.Y("sum(pts_minus):Q", scale=alt.Scale(reverse=True)),
            color=alt.Color("round:N", legend=None),
            detail="Тема",
            text="Тема",
        )
    )
    return (text + base).configure_view(width=1000, height=600)


def create_tabs(df_all):
    (
        I_TAB_TOTALS,
        I_TAB_TOPIC_STATS,
        I_TAB_GAME_STATS,
    ) = st.tabs(["Загалом", "Статистика тем", "Статистика боїв"])

    with I_TAB_TOTALS:
        total_stats = get_total_stats(df_all, "round")

        st.markdown("""### Статистика по колах""")
        st.write(total_stats.drop(columns=["Тема"]))

        st.markdown("### Статистика бо темах")
        for i, g in df_all.groupby("round"):
            st.markdown(f"""> Коло {i}""")
            st.dataframe(get_total_stats(g, "topic").set_index("Тема"))

        chart = generate_scatter(df_all)

        with st.expander("📊 плюси та мінуси по колах/темах"):
            st.altair_chart(chart)

    with I_TAB_TOPIC_STATS:
        I_FILE_INPUT = st.selectbox(
            "Оберіть коло",
            options=df_all["round"].unique(),
            format_func=lambda x: f"Коло {x}",
            key="topic_stats_filter",
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
        I_FILE_INPUT = st.selectbox(
            "Оберіть коло",
            options=df_all["round"].unique(),
            format_func=lambda x: f"Коло {x}",
            key="game_stats_filter",
        )
        df = df_all[df_all["round"] == I_FILE_INPUT]
        for result in render_game_stats(df):
            st.header(result["header"])
            st.write(result["results_table"])
            st.altair_chart(result["chart"])
