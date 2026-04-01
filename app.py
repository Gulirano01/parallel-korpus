from flask import Flask, render_template, request
import pandas as pd
import re
import html

app = Flask(__name__)

FILE_NAME = "parallel_korpus.xlsx"
df = pd.read_excel(FILE_NAME)

df.columns = [str(col).strip().lower() for col in df.columns]

required_columns = ["uz", "eng"]
for col in required_columns:
    if col not in df.columns:
        raise ValueError(f"Excel faylda '{col}' ustuni topilmadi.")

for col in ["uz", "eng"]:
    df[col] = df[col].fillna("").astype(str)

def normalize(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.lower().strip()
    text = text.replace("’", "'").replace("`", "'").replace("ʻ", "'").replace("ʼ", "'").replace("‘", "'")
    text = re.sub(r"\s+", " ", text)
    return text

def tokenize(text: str):
    text = normalize(text)
    pattern = r"[a-zA-ZÀ-ÿА-Яа-яO'oʻʻ’‘`ʻʼ\-]+(?:'[a-zA-ZÀ-ÿА-Яа-яO'oʻʻ’‘`ʻʼ\-]+)?|\d+|[^\w\s]"
    return re.findall(pattern, text, flags=re.UNICODE)

def contains_exact_word(text: str, query: str) -> bool:
    query_norm = normalize(query)
    tokens = tokenize(text)
    return query_norm in tokens

def contains_phrase(text: str, query: str) -> bool:
    return normalize(query) in normalize(text)

def highlight_exact_word(text: str, query: str) -> str:
    if not query.strip():
        return html.escape(text)

    query_norm = normalize(query)
    parts = re.findall(r"\s+|[^\s]+", text, flags=re.UNICODE)

    result = []
    for part in parts:
        clean = normalize(re.sub(r"^[^\w']+|[^\w']+$", "", part))
        if clean == query_norm:
            result.append(f"<mark>{html.escape(part)}</mark>")
        else:
            result.append(html.escape(part))
    return "".join(result)

def highlight_phrase(text: str, query: str) -> str:
    if not query.strip():
        return html.escape(text)

    escaped_text = html.escape(text)
    escaped_query = html.escape(query)
    pattern = re.compile(re.escape(escaped_query), re.IGNORECASE)
    return pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", escaped_text)

def build_extralinguistic_block():
    return {
        "kitob": "Ikki eshik orasi",
        "muallif": "O‘tkir Hoshimov",
        "janr": "Roman",
        "uslub": "Badiiy",
        "auditoriya": "Keng omma",
        "nashr_yili": "1985-yil",
        "nashriyot": "Sharq",
        "hajmi": "624 bet"
    }

AUTHOR_INFO = """
Ushbu parallel korpus va qidiruv tizimi Gulira'no Nuriddinova tomonidan ishlab chiqilgan.
Tizim o‘zbek va ingliz tilidagi parallel matnlar asosida qidiruvni amalga oshiradi,
qidirilgan birliklarni konkordans ko‘rinishida ko‘rsatadi hamda tokenizatsiya va
extralingvistik ma’lumotlarni alohida bo‘limlarda taqdim etadi.
"""

@app.route("/", methods=["GET", "POST"])
def home():
    results = []
    query = ""
    active_tab = "search"
    extra_block = build_extralinguistic_block()

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        active_tab = request.form.get("active_tab", "search")

        if query:
            query_tokens = tokenize(query)

            if len(query_tokens) == 1:
                filtered = df[
                    df["uz"].apply(lambda x: contains_exact_word(x, query)) |
                    df["eng"].apply(lambda x: contains_exact_word(x, query))
                ].copy()

                filtered["uz_h"] = filtered["uz"].apply(lambda x: highlight_exact_word(x, query))
                filtered["eng_h"] = filtered["eng"].apply(lambda x: highlight_exact_word(x, query))
            else:
                filtered = df[
                    df["uz"].apply(lambda x: contains_phrase(x, query)) |
                    df["eng"].apply(lambda x: contains_phrase(x, query))
                ].copy()

                filtered["uz_h"] = filtered["uz"].apply(lambda x: highlight_phrase(x, query))
                filtered["eng_h"] = filtered["eng"].apply(lambda x: highlight_phrase(x, query))

            filtered["uz_tokens"] = filtered["uz"].apply(tokenize)
            filtered["eng_tokens"] = filtered["eng"].apply(tokenize)

            results = filtered.to_dict(orient="records")

    return render_template(
        "index.html",
        results=results,
        query=query,
        active_tab=active_tab,
        author_info=AUTHOR_INFO,
        extra_block=extra_block
    )

if __name__ == "__main__":
    app.run(debug=True)
