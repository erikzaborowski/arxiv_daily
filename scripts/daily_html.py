#!/opt/homebrew/bin/python3
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

URL_list = [
    "https://arxiv.org/list/astro-ph/new",
    "https://arxiv.org/list/gr-qc/new",
]

def scrape_section(dl, subsection, heading):
    records = []
    for dt, dd in zip(dl.find_all('dd') , dl.find_all("dd")):
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
            "Heading": heading,
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
        
        # 1. Find the very first <h3> whose text starts with "New submissions" or "Cross-lists"
        new_h3 = soup.find("h3", string=lambda t: t and t.startswith("New submissions"))
        cross_h3 = soup.find("h3", string=lambda t: t and t.startswith("Cross submissions"))

        # 2. Grab the next <dl> after that
        first_new_dd = new_h3.find_next('dd')
        new_dl = first_new_dd.find_parent('dl')
        first_cross_dd = cross_h3.find_next('dd')
        cross_dl = first_cross_dd.find_parent('dl')

        # 3. Parse it
        new_records = scrape_section(new_dl, subsec, 'New submissions')
        cross_records = scrape_section(cross_dl, subsec, 'Cross submissions')
        all_papers = new_records + cross_records

        df = pd.DataFrame(all_papers)
        date = datetime.today().date()
        subsec_name = subsec + '.CO' if subsec == 'astro-ph' else subsec
        df.to_csv(f"outputs/parsed_{subsec_name}.csv", index=False)
        print(f"Wrote {len(df)} {subsec} papers to outputs/parsed_{subsec_name}.csv")

if __name__ == "__main__":
    main()
