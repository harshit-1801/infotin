from ast import main
from flask import Flask, render_template, redirect, request
from newsapi import NewsApiClient
import requests

app = Flask(__name__)

newsapi = NewsApiClient(api_key='205f6116c4984a6ea4ee7e69c00bbde0')

@app.route("/")
def index():
    top_headlines = newsapi.get_top_headlines(country='in')["articles"]
    for i in top_headlines:
        ind = i["title"][::-1].find("-")
        i["title"] = i["title"][::-1][ind+2:][::-1]
    return render_template("index.html",top_headlines = top_headlines)

app.run(debug=True)