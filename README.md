# Product Intelligence Agent
An AI agent that researches and scores products like a VC analyst.
Give it a product name. It searches the web, verifies the results are actually about the right product, analyzes it, scores it across four dimensions, and saves it to memory. If confidence in the search results is low, it searches again automatically before analyzing.

## Features
- Web search across three queries per product
- Verification step before analysis to catch wrong results
- Auto re-search if confidence is low
- VC-style scoring: Market Position, Differentiation, AI Readiness, Competitive Risk
- Head to head comparison between two products
- JSON memory so repeat queries load instantly

## Tech
Python, Streamlit, Groq API (LLaMA 3.3 70B), DuckDuckGo Search

## Setup
pip install streamlit groq ddgs pyngrok
streamlit run app.py

Add your Groq API key in the sidebar. Free key at console.groq.com

## How it works
Search -> Verify -> Re-search if confidence Low -> Analyze -> Score -> Save

## Tested on
LobeHub, Radiq, Linear, Notion
