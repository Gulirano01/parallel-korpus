import os
import re
import pandas as pd
from flask import Flask, render_template, request

app = Flask(__name__)

# Excel faylni o‘qish
df = pd.read_excel("parallel_corpus.xlsx")   # fayl nomini o‘zingnikiga mosla

# Ustun nomlarini tekislash
df.columns = df.columns.str.strip().str.lower()

# Bo‘sh qiymatlarni to‘ldirish
df["uz"] = df["uz"].fillna("").astype(str)
df["eng"] = df["eng"].fillna("").astype(str)


def normalize(text):
    text = str(text).lower().strip()
    text = text.replace("’", "'").replace("‘", "'").replace("`", "'")
    text = re.sub(r"\s+", " ", text)
    return text


def tokenize(text):
    return str(text).split()


def highlight(text, query):
    if not query:
        return text
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    return pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", str(text))


# Oldindan normalize
df["uz_norm"] = df["uz"].apply(normalize)
df["eng_norm"] = df["eng"].apply(normalize)


@app.route("/", methods=["GET", "POST"])
def home():
    results = []
    query = ""

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        query_norm = normalize(query)

        if query_norm:
            filtered = df[
                df["uz_norm"].str.contains(query_norm, na=False, regex=False) |
                df["eng_norm"].str.contains(query_norm, na=False, regex=False)
            ].copy()

            filtered["uz_h"] = filtered["uz"].apply(lambda x: highlight(x, query))
            filtered["eng_h"] = filtered["eng"].apply(lambda x: highlight(x, query))

            filtered["uz_tok"] = filtered["uz"].apply(tokenize)
            filtered["eng_tok"] = filtered["eng"].apply(tokenize)

            results = filtered.head(10).to_dict(orient="records")

    return render_template("index.html", results=results, query=query)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))