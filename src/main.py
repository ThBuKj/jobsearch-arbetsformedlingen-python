# main.py
# Hämtar jobb från arbetsförmedlingen och sparar till Excel


import os
import yaml
import pandas as pd
from datetime import datetime
from api import fetch_jobs

def load_config():
    # Går upp en nivå för att hitta config.yml
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yml")
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config

def check_if_relevant(title, company, include_words, exclude_words):
    """
    Kollar om ett jobb är relevant
    """
    text = f"{title} {company}".lower()
    
    # Måste ha minst ett bra ord
    found_good = False
    for word in include_words:
        if word.lower() in text:
            found_good = True
            break
    
    if not found_good:
        return False
    
    # Får inte ha dåliga ord
    for word in exclude_words:
        if word.lower() in text:
            return False
    
    return True

def get_jobs(keywords, locations, limit):
    all_jobs = []
    
    # Går igenom alla sökord och platser
    for keyword in keywords:
        for location in locations:
            print(f"Söker '{keyword}' i {location}...")
            
            jobs = fetch_jobs(keyword, location, limit)
            
            # Lägger till jobben i listan
            for job in jobs:
                workplace = job.get("workplace_address", {})
                if workplace is None:
                    workplace = {}
                    
                employer = job.get("employer", {})
                if employer is None:
                    employer = {}
                
                # Ta bort minustecken från keyword
                clean_keyword = ' '.join([w for w in keyword.split() if not w.startswith('-')])
                
                url = job.get("webpage_url", "")
                if url:
                    url = url + " "  # Mellanrum efter URL
                
                all_jobs.append({
                    "keyword": clean_keyword,
                    "title": job.get("headline", ""),
                    "company": employer.get("name", ""),
                    "location": workplace.get("municipality", ""),
                    "url": url,
                    "published": job.get("publication_date", "")
                })
    
    return all_jobs

def main():
    print("Startar...")
    
    # Läser config
    config = load_config()
    keywords = config["keywords"]
    locations = config["locations"]
    limit = config.get("limit", 50)

    include_words = config.get("include_words", [])
    exclude_words = config.get("exclude_words", [])
    
    # Hämtar alla jobb
    jobs = get_jobs(keywords, locations, limit)
    
    if len(jobs) == 0:
        print("Hittade inga jobb")
        return
    
    # Filtrerar
    print("Filtrerar...")
    filtered_jobs = []
    for job in jobs:
        if job["url"] != "" and job["url"] != " ":
            if check_if_relevant(job["title"], job["company"], include_words, exclude_words):
                filtered_jobs.append(job)
    
    print(f"Hittade {len(filtered_jobs)} relevanta jobb")
    
    # Filvägar
    base = os.path.join(os.path.dirname(__file__), "..")
    csv_file = os.path.join(base, "jobs.csv")
    excel_file = os.path.join(base, "jobs.xlsx")
    
    # Läser gamla jobb
    old_jobs = []
    old_urls = set()
    if os.path.exists(csv_file):
        try:
            old_data = pd.read_csv(csv_file, encoding="utf-8-sig")
            old_jobs = old_data.to_dict('records')
            
            for job in old_jobs:
                if pd.notna(job.get("url")):
                    old_urls.add(job["url"].strip())
        except FileNotFoundError:
            print("Kunde inte läsa gammal fil")
    
    # Nya jobb
    new_jobs = []
    for job in filtered_jobs:
        if job["url"].strip() not in old_urls:
            new_jobs.append(job)
    
    if len(new_jobs) == 0:
        print("Inga nya jobb, filen ändras inte")
        return
    
    print(f"Hittade {len(new_jobs)} nya jobb att lägga till")
    
    # Separator
    old_jobs.append({"keyword": ""})
    old_jobs.append({"keyword": f"--- Uppdaterad {datetime.now().strftime('%Y-%m-%d %H:%M')} ---"})
    
    for job in new_jobs:
        old_jobs.append(job)
    
    # Sparar
    df = pd.DataFrame(old_jobs)

    # ✅ Tvingar mellanslag efter URL vid export
    df["url"] = df["url"].astype(str).str.replace(r"\s*$", " ", regex=True)

    df.to_csv(csv_file, index=False, encoding="utf-8-sig")
    df.to_excel(excel_file, index=False, engine='openpyxl')
    
    print(f"Klart! Sparade {len(new_jobs)} nya jobb")

if __name__ == "__main__":
    main()
