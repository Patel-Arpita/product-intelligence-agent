
import streamlit as st
import json
import os
from datetime import datetime
from groq import Groq
from ddgs import DDGS

st.set_page_config(page_title="Product Intelligence Agent", layout="wide")

MEMORY_FILE = "memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE) as f:
            return json.load(f)
    return {}

def save_to_memory(name, analysis, score):
    mem = load_memory()
    mem[name] = {
        "analysis": analysis,
        "score": score,
        "saved_at": datetime.now().strftime("%d %b %Y, %I:%M %p")
    }
    with open(MEMORY_FILE, "w") as f:
        json.dump(mem, f, indent=2)

def search_product(name):
    results = []
    with DDGS() as ddgs:
        for query in [
            f"{name} product what does it do",
            f"{name} who uses it target customers",
            f"{name} competitors alternatives"
        ]:
            for r in ddgs.text(query, max_results=2):
                results.append(r["body"])
    return "\n".join(results)

def ask_llm(client, prompt):
    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content

def check_results(client, name, data):
    return ask_llm(client, f"""Check if these search results are actually about {name}.

Results:
{data}

Reply in this format only:
CORRECT: Yes or No
CONFIDENCE: High, Medium, or Low
REASON: one sentence explaining why
""")

def get_confidence(check_text):
    for line in check_text.splitlines():
        if line.startswith("CONFIDENCE:"):
            return line.replace("CONFIDENCE:", "").strip()
    return "Low"

def analyze(client, name, data):
    return ask_llm(client, f"""You are a senior analyst at a VC firm.
Analyze {name} based on the search data below.
Be specific. Avoid generic statements.

Search Data:
{data}

Write these sections:
WHAT IT IS:
WHO IT IS FOR:
KEY DIFFERENTIATORS:
BIGGEST THREATS:
CONFIDENCE LEVEL: High, Medium, or Low
FLAGGED UNCERTAINTIES:
""")

def score(client, analysis):
    return ask_llm(client, f"""Score this product. Be harsh and realistic.
Most products score between 4 and 7. Only truly exceptional products score 8 or above.
A score of 8+ must be explicitly justified. Default to lower if uncertain.

Analysis:
{analysis}

Use this exact format, whole numbers only:
Market Position: X/10 - reason
Differentiation: X/10 - reason
AI Readiness: X/10 - reason
Competitive Risk: X/10 - reason
Overall Score: X/10
Verdict: one sentence
""")

def compare(client, p1, p2, a1, a2):
    return ask_llm(client, f"""Compare {p1} and {p2} as a product analyst would.

{p1} analysis:
{a1}

{p2} analysis:
{a2}

Write:
STRONGER OVERALL:
WHERE {p1.upper()} WINS:
WHERE {p2.upper()} WINS:
WHO SHOULD PICK WHICH:
""")

def pull_scores(score_text):
    found = {}
    labels = ["Market Position", "Differentiation", "AI Readiness", "Competitive Risk", "Overall Score"]
    for line in score_text.splitlines():
        for label in labels:
            if line.startswith(label):
                try:
                    found[label] = round(float(line.split(":")[1].strip().split("/")[0].strip()))
                except:
                    pass
    return found

with st.sidebar:
    st.markdown("## Settings")
    api_key = st.text_input("Groq API Key", type="password")
    
    st.divider()
    st.markdown("## Past Analyses")
    mem = load_memory()
    if mem:
        for pname, pdata in mem.items():
            st.markdown(f"**{pname}** — {pdata['saved_at']}")
        if st.button("Clear all memory"):
            os.remove(MEMORY_FILE)
            st.success("Cleared.")
            st.rerun()
    else:
        st.caption("Nothing saved yet. Run an analysis first.")

st.title("Product Intelligence Agent")
st.caption("Searches the web. Verifies results. Analyzes like a VC. Built by Arpita Patel.")
st.divider()

tab1, tab2 = st.tabs(["Analyze a Product", "Compare Two Products"])

with tab1:
    name = st.text_input("Product name", placeholder="Try: Linear, Radiq, LobeHub")
    
    mem = load_memory()
    from_memory = False
    if name and name in mem:
        from_memory = st.checkbox(f"Use saved analysis for {name}?", value=True)
    
    if st.button("Run Analysis"):
        if not api_key:
            st.error("Add your Groq API key in the sidebar first.")
        elif not name:
            st.error("Enter a product name.")
        else:
            client = Groq(api_key=api_key)
            
            if from_memory and name in mem:
                analysis_text = mem[name]["analysis"]
                score_text = mem[name]["score"]
                st.info(f"Loaded from memory — saved on {mem[name]['saved_at']}")
            else:
                with st.status("Working...", expanded=True) as s:
                    st.write("Searching the web...")
                    raw = search_product(name)

                    st.write("Checking if results are correct...")
                    check = check_results(client, name, raw)
                    confidence = get_confidence(check)

                    if confidence == "Low":
                        st.write("Confidence was low. Searching again with better query...")
                        raw += "\n" + search_product(name + " software product startup 2024")

                    st.write("Analyzing...")
                    analysis_text = analyze(client, name, raw)

                    st.write("Scoring...")
                    score_text = score(client, analysis_text)

                    save_to_memory(name, analysis_text, score_text)
                    s.update(label="Done.", state="complete")

            col1, col2 = st.columns([3, 2])

            with col1:
                st.subheader("Analysis")
                st.markdown(analysis_text)

            with col2:
                st.subheader("Scores")
                scores = pull_scores(score_text)
                for label, val in scores.items():
                    if label != "Overall Score":
                        st.metric(label, f"{val}/10")
                        st.progress(val / 10)
                if "Overall Score" in scores:
                    st.divider()
                    st.metric("Overall Score", f"{scores['Overall Score']}/10")
                for line in score_text.splitlines():
                    if line.startswith("Verdict:"):
                        st.divider()
                        st.info(line.replace("Verdict:", "").strip())

with tab2:
    c1, c2 = st.columns(2)
    with c1:
        p1 = st.text_input("First product", placeholder="Linear")
    with c2:
        p2 = st.text_input("Second product", placeholder="Notion")

    if st.button("Compare"):
        if not api_key:
            st.error("Add your Groq API key in the sidebar.")
        elif not p1 or not p2:
            st.error("Enter both product names.")
        else:
            client = Groq(api_key=api_key)
            mem = load_memory()

            with st.status("Researching both products...", expanded=True) as s:
                for product in [p1, p2]:
                    if product not in mem:
                        st.write(f"Researching {product}...")
                        raw = search_product(product)
                        a = analyze(client, product, raw)
                        sc = score(client, a)
                        save_to_memory(product, a, sc)
                    else:
                        st.write(f"{product} already in memory, skipping search.")

                mem = load_memory()

                st.write("Running comparison...")
                comparison_text = compare(client, p1, p2, mem[p1]["analysis"], mem[p2]["analysis"])
                s.update(label="Done.", state="complete")

            mem = load_memory()
            s1 = pull_scores(mem[p1]["score"])
            s2 = pull_scores(mem[p2]["score"])

            st.subheader(f"{p1} vs {p2}")

            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**{p1}**")
                st.metric("Overall", f"{s1.get('Overall Score', '?')}/10")
            with c2:
                st.markdown(f"**{p2}**")
                st.metric("Overall", f"{s2.get('Overall Score', '?')}/10")

            st.divider()
            st.markdown(comparison_text)
