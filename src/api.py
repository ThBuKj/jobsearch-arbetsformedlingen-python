

# api.py
# Hämtar jobb från JobTech API (arbetsförmedlingens API)

import requests

def fetch_jobs(keyword, location, limit=50):
    """
    Hämtar jobb från arbetsförmedlingens API
    """
    
    url = "https://jobsearch.api.jobtechdev.se/search"
    
    # Kombinerar sökord och plats
    search_text = f"{keyword} {location}"
    
    params = {
        "q": search_text,
        "limit": limit if limit <= 100 else 100  # Max 100
    }
    
    headers = {"accept": "application/json"}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        hits = data.get("hits", [])
        total = data.get("total", {}).get("value", 0)
        
        # Filtrerar på plats och exkluderade ord
        filtered = []
        
        # Hittar ord som ska exkluderas (de med - framför)
        exclude_words = []
        for word in keyword.split():
            if word.startswith('-'):
                exclude_words.append(word[1:].lower())
        
        for job in hits:
            # Kollar om jobbet är i rätt kommun
            workplace = job.get("workplace_address", {})
            municipality = workplace.get("municipality", "")
            
            if municipality and location.lower() not in municipality.lower():
                continue
            
            # Kollar om jobbet innehåller exkluderade ord
            title = job.get("headline", "").lower()
            description = job.get("description", {}).get("text", "").lower()
            
            should_skip = False
            for exclude in exclude_words:
                if exclude in title or exclude in description:
                    should_skip = True
                    break
            
            if not should_skip:
                filtered.append(job)
        
        print(f"  Hittade {len(filtered)} jobb i {location} (totalt fanns {total})")
        return filtered
        
    except Exception as e:
        print(f"Något gick fel vid sökning av '{keyword}' i {location}: {e}")
        return []
