from flask import Flask, render_template, request
import pandas as pd
import re
import os

app = Flask(__name__)

df = pd.read_excel("parallel_korpus.xlsx")
df.columns = df.columns.str.strip().str.lower()

if "uz" not in df.columns or "eng" not in df.columns:
    raise ValueError(f"Excel faylda 'uz' va 'eng' ustunlari bo‘lishi kerak. Hozirgi ustunlar: {list(df.columns)}")

df["uz"] = df["uz"].fillna("").astype(str)
df["eng"] = df["eng"].fillna("").astype(str)

def normalize(text):
    text = str(text).lower().strip()
    text = text.replace("‘", "'").replace("’", "'").replace("`", "'")
    text = re.sub(r"[^\w\s']", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def tokenize(text):
    text = str(text).lower().strip()
    text = text.replace("‘", "'").replace("’", "'").replace("`", "'")
    return re.findall(r"\w+(?:'\w+)?", text)

def highlight(text, query):
    if not query:
        return str(text)
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    return pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", str(text))

df["uz_norm"] = df["uz"].apply(normalize)
df["eng_norm"] = df["eng"].apply(normalize)

@app.route("/", methods=["GET", "POST"])
def home():
    results = []
    query = ""
    search_type = "all"
    total_results = 0
    show_all = False

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        search_type = request.form.get("search_type", "all")
        show_all = request.form.get("show_all") == "1"
        query_norm = normalize(query)

        if query_norm:
            if search_type == "uz":
                filtered = df[df["uz_norm"].str.contains(query_norm, na=False)].copy()
            elif search_type == "eng":
                filtered = df[df["eng_norm"].str.contains(query_norm, na=False)].copy()
            else:
                filtered = df[
                    df["uz_norm"].str.contains(query_norm, na=False) |
                    df["eng_norm"].str.contains(query_norm, na=False)
                ].copy()

            total_results = len(filtered)

            if not show_all:
                filtered = filtered.head(10)

            filtered["uz_highlight"] = filtered["uz"].apply(lambda x: highlight(x, query))
            filtered["eng_highlight"] = filtered["eng"].apply(lambda x: highlight(x, query))
            filtered["uz_tokens_str"] = filtered["uz"].apply(lambda x: " | ".join(tokenize(x)))
            filtered["eng_tokens_str"] = filtered["eng"].apply(lambda x: " | ".join(tokenize(x)))

            results = filtered[
                ["uz_highlight", "eng_highlight", "uz_tokens_str", "eng_tokens_str"]
            ].to_dict(orient="records")

    return render_template(
        "index.html",
        query=query,
        results=results,
        total_results=total_results,
        search_type=search_type,
        show_all=show_all
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))