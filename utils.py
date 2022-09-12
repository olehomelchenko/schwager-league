import numpy as np
import altair as alt
import streamlit as st


def transform_data(df):
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
    df["topic"] = df["Тема"].str.extract(r"([^.]+)").astype(int)
    df["qid"] = df.agg("{0[topic]}.{0[price]}".format, axis=1)
    df["pts"] = df["price"] * df["value"]
    df["pts_plus"] = np.select([df["value"] > 0], [df["pts"]], default=0)
    df["pts_minus"] = np.select([df["value"] < 0], [df["pts"]], default=0)
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
