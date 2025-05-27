#!/opt/homebrew/bin/python3
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

URL_list = [
    "https://arxiv.org/list/astro-ph/new",
    "https://arxiv.org/list/gr-qc/new",
]

INCLUDE_SECTIONS = {"New submissions", "Cross-lists", "Cross lists", "Cross submissions"}
EXCLUDE_SECTION  = "Replacements"

def scrape_section(dl, subsection):
    records = []
    for dt, dd in zip(dl.find_all("dt"), dl.find_all("dd")):
        subjects = dd.find("div", class_="list-subjects")
        subjects = subjects.get_text(strip=True).split(":",1)[1].strip() if subjects else ""
        if subsection == "astro-ph" and "astro-ph.CO" not in subjects:
            continue

        # Basic fields
        # arxiv_id = dt.find("a").text.strip()
        title    = dd.find("div", class_="list-title").get_text(strip=True).split(":",1)[1].strip()
        authors  = dd.find("div", class_="list-authors").get_text(strip=True).split(":",1)[0].strip()
        abstract = dd.find("p", class_="mathjax").get_text(strip=True)
        pdf_link = dt.find("a", title="Download PDF")
        pdf_link = "https://arxiv.org" + pdf_link["href"] if pdf_link else ""

        records.append({
            # "arXiv ID": arxiv_id,
            "Title":    title,
            "Authors":  authors,
            "Subjects": subjects,
            "Abstract": abstract,
            "PDF":      pdf_link
        })
    return records

def main():
    for URL in URL_list:
        subsec = URL.split("/")[-2]
        resp = requests.get(URL, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        all_papers = []
        for h3 in soup.find_all("h3"):
            heading = h3.get_text(strip=True)
            if EXCLUDE_SECTION in heading:
                break
            if any(sec in heading for sec in INCLUDE_SECTIONS):
                # find the next <dl> no matter what intervenes
                dl = h3.find_next("dl")
                if dl is None:
                    print(f"⚠️ No <dl> block after “{heading}”")
                    continue
                all_papers.extend(scrape_section(dl, subsec))

        df = pd.DataFrame(all_papers)
        date = datetime.today().date()
        df.to_csv(f"outputs/{subsec}_announced_{date}.csv", index=False)
        print(f"Wrote {len(df)} {subsec} papers to outputs/{subsec}_announced_{date}.csv")

if __name__ == "__main__":
    main()
