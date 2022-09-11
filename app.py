from glob import glob
import streamlit as st
import pandas as pd
import numpy as np
import requests
import altair as alt

st.header("swager-league")


@st.cache(ttl=10)
def get_csv(url):
    r = requests.get(url)
    r.encoding = r.apparent_encoding
    assert r.status_code == 200
    return r.text


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


@st.cache
def pivot_game(df):
    df_pivot = df.pivot(index=["Name"], columns=["qid"], values=["val_emoji"])
    df_pivot.columns = df_pivot.columns.droplevel(0)
    return df_pivot


def main():
    files = glob("data/**/*.csv")
    files.sort()
    I_FILE_INPUT = st.selectbox("Select File", options=files)

    df = pd.read_csv(I_FILE_INPUT, header=[0, 1, 2, 3])

    df = transform_data(df)

    res_by_qid = (
        df.groupby(["qid", "Тема", "Питання", "price", "val_emoji"])
        .agg({"value": "count", "Name": ", ".join})
        .reset_index()
        # .query("val_emoji in ['✅', '❌']")
    )

    I_TAB_TOPIC_STATS, I_TAB_GAME_STATS = st.tabs(["Статистика тем", "Статистика боїв"])
    with I_TAB_TOPIC_STATS:

        for i, g in res_by_qid.groupby("Тема"):
            f"""###  {i}"""
            with st.expander("Питання"):
                st.markdown("\n\n---\n".join(g["Питання"].unique()))

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
                        legend=None
                    ),
                    tooltip=["Name"],
                )
                .properties(height=200, width=100)
            )
            text = base.mark_text(dy=-10).encode(text="value")
            st.altair_chart((base + text).facet(column="qid:N"))

    with I_TAB_GAME_STATS:
        dff = df.pivot(index=["Game", "Name"], columns=["qid"], values="val_emoji")
        for i, g in df.groupby("Game"):
            f"""{i}: {' / '.join(g['Name'].unique())} """
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
            st.write(totals.join(results))
            g["cumsum"] = g.groupby("Name")["pts"].cumsum()
            g["q"] = g["Питання"]
            st.altair_chart(
                alt.Chart(g[["Name", "pts", "cumsum", "qid", "Питання", 'Тема']])
                .mark_line(opacity=0.7, point=True)
                .encode(
                    x=alt.X("qid:N", title=None),
                    y=alt.Y("cumsum:Q", title=None),
                    color="Name:N",
                    tooltip=["Тема:N","Питання:N"],
                )
                .properties(width=800)
            )
            "---"


main()
# # read csv
# df = pd.read_csv("1.csv", header=[0, 1, 2, 3])

# # Transform Data
# df = transform_data(df)


# st.write(
#     df.pivot_table(index="val_emoji", columns="price", values="qid", aggfunc="count")
#     .fillna(0)
#     .astype(int)
# )
# st.write(
#     df.pivot_table(
#         index=["League", "val_emoji"], columns="price", values="qid", aggfunc="count"
#     )
#     .fillna(0)
#     .astype(int)
#     .sort_values("League", ascending=False)
# )

# # add tabs
# totals, results, questions = st.tabs(["Totals", "Results", "Questions"])
# with totals:
#     for game in df["League"].unique():
#         df__ = df.query(f"League=='{game}'")
#         st.write(df__)
#         st.write(
#             df__.pivot_table(
#                 index="val_emoji", columns="price", values="qid", aggfunc="count"
#             )
#             .fillna(0)
#             .astype(int)
#         )

# with results:
#     for game in df["League"].unique():
#         st.subheader(game)
#         df__ = df.query(f"League=='{game}'")

#         df_pivot = pivot_game(df__)
#         st.write(df_pivot)

#         c = alt.Chart(df__).mark_text().encode(y="Name:N", x="qid:N", text="val_emoji")
#         st.altair_chart(c)


# with questions:
#     st.write("questions")
