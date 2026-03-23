from flask import Flask, render_template, request
import pandas as pd
import re
import os

app = Flask(__name__)

# Excel fayl
file_name = "parallel_korpus.xlsx"

df = pd.read_excel(file_name)
df.columns = df.columns.str.strip()

# Tekshirish
if 'uz' not in df.columns or 'eng' not in df.columns:
    raise ValueError("Excel faylda 'uz' va 'eng' ustunlari bo‘lishi kerak")

df['uz'] = df['uz'].fillna('').astype(str)
df['eng'] = df['eng'].fillna('').astype(str)


# Normalizatsiya
def normalize(text):
    text = str(text).lower().strip()
    text = text.replace("‘", "'").replace("’", "'").replace("`", "'")
    text = re.sub(r"[^\w\s']", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# Tokenlash
def tokenize(text):
    text = str(text).lower().strip()
    return re.findall(r"\w+(?:'\w+)?", text)


# Highlight
def highlight(text, query):
    if not query:
        return text
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    return pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", text)


# Oldindan normalize
df['uz_norm'] = df['uz'].apply(normalize)
df['eng_norm'] = df['eng'].apply(normalize)


# 🔥 MUHIM ROUTE (muammo shu edi)
@app.route("/", methods=["GET", "POST"])
def home():
    results = []
    query = ""

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        query_norm = normalize(query)

        if query_norm:
            filtered = df[
                df['uz_norm'].str.contains(query_norm, na=False) |
                df['eng_norm'].str.contains(query_norm, na=False)
            ].copy()

            filtered['uz_h'] = filtered['uz'].apply(lambda x: highlight(x, query))
            filtered['eng_h'] = filtered['eng'].apply(lambda x: highlight(x, query))

            filtered['uz_tok'] = filtered['uz'].apply(tokenize)
            filtered['eng_tok'] = filtered['eng'].apply(tokenize)

            results = filtered.head(10).to_dict(orient="records")

    return render_template("index.html", results=results, query=query)


# 🔥 Render uchun MUHIM
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))