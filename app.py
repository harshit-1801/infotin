from flask import Flask, render_template, redirect, request
from newsapi import NewsApiClient
import requests
import urllib.parse

app = Flask(__name__)

newsapi = NewsApiClient(api_key='205f6116c4984a6ea4ee7e69c00bbde0')

colors = {
    "sports":"#fd916a",
    "entertainment":"#ffbb53",
    "health":"#e64bff",
    "science":"#71d2fe",
    "technology":"#fec70a",
    "business":"#e95554"
}

@app.route("/")
def index():
    top_headlines = newsapi.get_top_headlines(country='in')["articles"]
    for i in top_headlines:
        ind = i["title"][::-1].find("-")
        i["title"] = i["title"][::-1][ind+2:][::-1]
    return render_template("index.html",top_headlines = top_headlines)

@app.route("/categories/<string:category>")
def categories(category):
    news = newsapi.get_top_headlines(country='in',category=category)["articles"]
    return render_template("categories.html",news = news,category=category.title(),colors = colors[category])

@app.route("/search",methods=["GET","POST"])
def search():
    title = request.form.get("query")
    query = urllib.parse.quote(title)
    news = newsapi.get_everything(language="en",sort_by="publishedAt",q=request.form.get("query"))["articles"]
    print(news)
    return render_template("search.html",news = news,title = title.title())

app.run(debug=True)