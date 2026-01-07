import requests
import sys
import os
import io
import time
from SPARQLWrapper import SPARQLWrapper, JSON
import random

class WikipediaInterface:
    def __init__(self, user_agent: str = None, rate_limit_delay: float = 1.0):
        """
        Initialize Wikipedia interface with independent configuration.
        
        Args:
            user_agent: Custom user agent string. If None, will try environment variables
                       or use sensible defaults
            rate_limit_delay: Delay between requests to respect rate limits
        """
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time = 0
        
        # Build user agent with fallback chain
        if user_agent:
            self.user_agent_header = user_agent
        else:
            # Try to construct from environment variables
            user_wiki = os.getenv("USER_WIKI", "")
            github_repo = os.getenv("GITHUB_REPO", "")
            app_name = os.getenv("APP_NAME", "a_gent_parl")
            version = os.getenv("VERSION", "1.0")
            
            if user_wiki and github_repo:
                self.user_agent_header = f'{app_name}/{version} ({github_repo}; {user_wiki})'
            elif github_repo:
                self.user_agent_header = f'{app_name}/{version} ({github_repo})'
            else:
                self.user_agent_header = f'{app_name}/{version} (https://github.com/user/repo)'
        
        self.headers = {'User-Agent': self.user_agent_header}
        
        # API endpoints
        self.WIKI_API_URL_METRICS = "https://wikimedia.org/api/rest_v1/metrics"
        self.WIKI_API_URL_SPARQL = "https://query.wikidata.org/sparql"
        self.WIKI_API_URL = [
            "https://en.wikipedia.org/w/api.php", 
            "https://de.wikipedia.org/w/api.php", 
            "https://fr.wikipedia.org/w/api.php",
            "https://it.wikipedia.org/w/api.php", 
            "https://es.wikipedia.org/w/api.php", 
            "https://nl.wikipedia.org/w/api.php"
        ]
        self.WIKI_API_FILE_URL = "https://api.wikimedia.org/core/v1/commons/file"
        
        # SPARQL user agent for Wikidata queries
        self.sparql_user_agent = f"WDQS-example Python/{sys.version_info[0]}.{sys.version_info[1]}"

    def _respect_rate_limit(self):
        """Ensure rate limiting between requests."""
        if self.rate_limit_delay > 0:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            if time_since_last < self.rate_limit_delay:
                time.sleep(self.rate_limit_delay - time_since_last)
            self._last_request_time = time.time()

    def get_top_articles_by_country(self, country_code, date):
        """
        Get top articles by country for a specific date.
        
        Args:
            country_code: Country code (e.g., 'IT', 'US')
            date: Date in YYYY/MM/DD format
            
        Returns:
            dict: API response with top articles data
        """
        self._respect_rate_limit()
        api_url = f"{self.WIKI_API_URL_METRICS}/pageviews/top-per-country/{country_code}/all-access/{date}"
        response = requests.get(api_url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Error fetching data from Wikipedia API: {response.status_code}")
        return response.json()

    def dates_between_two_dates(self, start_date, end_date):
        import datetime as dt
        start = dt.datetime.strptime(start_date, "%Y/%m/%d")
        end = dt.datetime.strptime(end_date, "%Y/%m/%d")
        return [(start + dt.timedelta(days=i)).strftime("%Y/%m/%d") for i in range((end - start).days + 1)]

    def get_start_and_end_dates_by_period(self, period='week'):
        import datetime as dt
        today = dt.datetime.now()
        if period == 'week':
            end = today - dt.timedelta(days=1)
            start = today - dt.timedelta(days=7)
        elif period == 'month':
            end = today - dt.timedelta(days=1)
            start = today - dt.timedelta(months=1)
        elif period == 'year':
            end = today - dt.timedelta(days=1)
            start = today - dt.timedelta(years=1)
        return start.strftime("%Y/%m/%d"), end.strftime("%Y/%m/%d")
    
    def get_top_articles_excluding(self, articles, exclude_list):
        return [article for article in articles if article['article'] not in exclude_list]

    def get_top_n_articles(self, articles_dict, n=5):
        return {k: v for k, v in sorted(articles_dict.items(), key=lambda item: item[1], reverse=True)[:n]}
    
    def get_top_n_articles_over_period(self, country_code, period='week', exclude_list=None, top_n=5):
        if exclude_list is None:
            exclude_list = []
        start_date, end_date = self.get_start_and_end_dates_by_period(period)
        date_list = self.dates_between_two_dates(start_date, end_date)
        top_articles = {}
        for date in date_list:
            for country in country_code:
                data = self.get_top_articles_by_country(country, date)
                if 'items' in data and len(data['items']) > 0:
                    articles = self.get_top_articles_excluding(data['items'][0]['articles'], exclude_list)
                    for art in articles:
                        if art['article'] not in top_articles:
                            top_articles[art['article']] = art['views_ceil']
                        else:
                            top_articles[art['article']] += art['views_ceil']
                else: 
                    raise ValueError(f"No data available for {country} on {date}.")
        sorted_top_articles = self.get_top_n_articles(top_articles, top_n)
        return sorted_top_articles

    
    def sparql_get_results(self, query):
        """
        Execute SPARQL query against Wikidata endpoint.
        
        Args:
            query: SPARQL query string
            
        Returns:
            dict: Query results in JSON format
        """
        sparql = SPARQLWrapper(self.WIKI_API_URL_SPARQL, agent=self.sparql_user_agent)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        return sparql.query().convert()

    def get_dead_on_date(self, professions):
        queries = []
        for p in professions:
            queries.append((r"SELECT ?comicArtistLabel ?comicArtistDescription ?award_receivedLabel ?date_of_death WHERE { "
                    r"?comicArtist wdt:P31 wd:Q5; "
                    f"wdt:P106 {p}. "
                    r"SERVICE wikibase:label { bd:serviceParam wikibase:language '[AUTO_LANGUAGE],mul,en'. } "
                    r"OPTIONAL { ?comicArtist wdt:P570 ?date_of_death. } "
                    r"OPTIONAL { ?comicArtist wdt:P166 ?award_received. } "
                    r"FILTER((((DAY(?date_of_death)) = (DAY(NOW()))) && ((MONTH(?date_of_death)) = (MONTH(NOW())))))} "
                    r"ORDER BY DESC (?date_of_death)"))
        total_dict = {}
        for query in queries:
            results = self.sparql_get_results(query)
            for result in results["results"]["bindings"]:
                total_dict[result["comicArtistLabel"]["value"]] = {
                    "description": result.get("comicArtistDescription", {}).get("value", "No description"),
                    "award_received": result.get('award_receivedLabel', {}).get("value", "No award"),
                    "date_of_death": result.get('date_of_death', {}).get("value", "No date")
                }
        return total_dict
    
    def get_random_wiki_image(self, title):
        """
        Get a random image from a Wikipedia article.
        
        Args:
            title: Wikipedia article title
            
        Returns:
            io.BytesIO: Image bytes or None if no suitable image found
        """
        for base_url_wiki in self.WIKI_API_URL:
            self._respect_rate_limit()
            params = {
                "action": "query",
                "format": "json",
                "titles": title,
                "prop": "images"
            }
            response = requests.get(url=base_url_wiki, params=params, headers=self.headers)
            data = response.json()
            pages = data['query']['pages']
            valid_extensions = ('jpg', 'jpeg', 'png')
            if 'images' not in list(random.choice(list(pages.values())).keys()):
                print(f"No images found for {title} in {base_url_wiki}")
                return None
            if not any(img['title'].lower().endswith(valid_extensions) for img in random.choice(list(pages.values()))['images']):
                print(f"No valid image found for {title} in {base_url_wiki}")
                return None
            img_title = random.choice([img for img in random.choice(list(pages.values()))['images'] if img['title'].lower().endswith(valid_extensions)])
            if not img_title:
                print(f"No valid image found for {title} in {base_url_wiki}")
                return None
            #remove any word before ":" from the title in any language
            img_title_clean = img_title['title'].split(":")[-1].strip()
            url_image = f"{self.WIKI_API_FILE_URL}/File:{img_title_clean.replace(' ', '_')}"
            
            self._respect_rate_limit()
            response = requests.get(url_image, headers=self.headers)
            data = response.json()
            
            self._respect_rate_limit()
            return io.BytesIO(requests.get(data['original']['url'],headers=self.headers).content)

    def get_category_members(self, category_name, lang='en', limit=50):
        """
        Gets list of articles in a category.
        
        Args:
            category_name: Wikipedia category name (e.g., "Anime", "Video_games")
            lang: Language code for Wikipedia (default: 'en')
            limit: Maximum number of members to return
        
        Returns:
            list: List of article titles
        """
        # Map language codes to Wikipedia API URLs
        lang_to_url = {
            'en': 'https://en.wikipedia.org/w/api.php',
            'de': 'https://de.wikipedia.org/w/api.php', 
            'fr': 'https://fr.wikipedia.org/w/api.php',
            'it': 'https://it.wikipedia.org/w/api.php',
            'es': 'https://es.wikipedia.org/w/api.php',
            'nl': 'https://nl.wikipedia.org/w/api.php'
        }
        
        api_url = lang_to_url.get(lang, 'https://en.wikipedia.org/w/api.php')
        
        params = {
            'action': 'query',
            'format': 'json',
            'list': 'categorymembers',
            'cmtitle': f'Category:{category_name}',
            'cmlimit': limit,
            'cmnamespace': 0  # Only articles (namespace 0), exclude meta pages
        }
        
        try:
            self._respect_rate_limit()
            response = requests.get(api_url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            if 'query' in data and 'categorymembers' in data['query']:
                # Filter out disambiguation pages and meta pages
                members = []
                for member in data['query']['categorymembers']:
                    title = member['title']
                    # Skip disambiguation pages and list pages
                    if not ('disambiguation' in title.lower() or 
                           title.startswith('List of') or
                           title.startswith('Category:') or
                           '(disambiguation)' in title):
                        members.append(title)
                return members
            else:
                return []
                
        except requests.RequestException as e:
            print(f"Error fetching category members for {category_name}: {e}")
            return []

    def get_random_article_from_category(self, category_name, lang='en'):
        """
        Fetches a random article from a Wikipedia category.
        
        Args:
            category_name: Wikipedia category (e.g., "Anime", "Video_games")
            lang: Language code for Wikipedia (default: 'en')
        
        Returns:
            dict: {
                'title': str,
                'url': str,
                'pageid': int
            } or None if no suitable article found
        """
        # Get category members
        members = self.get_category_members(category_name, lang, limit=100)
        
        if not members:
            print(f"No members found in category {category_name}")
            return None
        
        # Map language codes to Wikipedia base URLs
        lang_to_base_url = {
            'en': 'https://en.wikipedia.org',
            'de': 'https://de.wikipedia.org', 
            'fr': 'https://fr.wikipedia.org',
            'it': 'https://it.wikipedia.org',
            'es': 'https://es.wikipedia.org',
            'nl': 'https://nl.wikipedia.org'
        }
        
        lang_to_api_url = {
            'en': 'https://en.wikipedia.org/w/api.php',
            'de': 'https://de.wikipedia.org/w/api.php', 
            'fr': 'https://fr.wikipedia.org/w/api.php',
            'it': 'https://it.wikipedia.org/w/api.php',
            'es': 'https://es.wikipedia.org/w/api.php',
            'nl': 'https://nl.wikipedia.org/w/api.php'
        }
        
        base_url = lang_to_base_url.get(lang, 'https://en.wikipedia.org')
        api_url = lang_to_api_url.get(lang, 'https://en.wikipedia.org/w/api.php')
        
        # Try up to 10 random selections to find a suitable article
        max_attempts = min(10, len(members))
        
        for _ in range(max_attempts):
            # Select random article
            random_title = random.choice(members)
            
            # Get basic article info to validate content length
            params = {
                'action': 'query',
                'format': 'json',
                'titles': random_title,
                'prop': 'extracts|info',
                'exintro': True,
                'explaintext': True,
                'inprop': 'url'
            }
            
            try:
                self._respect_rate_limit()
                response = requests.get(api_url, params=params, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                
                if 'query' in data and 'pages' in data['query']:
                    pages = data['query']['pages']
                    page_data = next(iter(pages.values()))
                    
                    # Check if page exists and has content
                    if 'missing' not in page_data and 'extract' in page_data:
                        extract = page_data.get('extract', '')
                        
                        # Validate content length (minimum 500 characters as per requirements)
                        if len(extract) >= 500:
                            return {
                                'title': page_data['title'],
                                'url': page_data.get('fullurl', f"{base_url}/wiki/{page_data['title'].replace(' ', '_')}"),
                                'pageid': page_data['pageid']
                            }
                        else:
                            # Remove this article from members list to avoid selecting it again
                            members.remove(random_title)
                            
            except requests.RequestException as e:
                print(f"Error fetching article {random_title}: {e}")
                continue
        
        print(f"Could not find suitable article from category {category_name} after {max_attempts} attempts")
        return None

    def get_article_content(self, article_title, lang='en'):
        """
        Fetches full article content including summary and text.
        
        Args:
            article_title: Title of the Wikipedia article
            lang: Language code for Wikipedia (default: 'en')
        
        Returns:
            dict: {
                'title': str,
                'url': str,
                'summary': str,
                'content': str,
                'length': int
            } or None if article not found
        """
        # Map language codes to Wikipedia API URLs and base URLs
        lang_to_api_url = {
            'en': 'https://en.wikipedia.org/w/api.php',
            'de': 'https://de.wikipedia.org/w/api.php', 
            'fr': 'https://fr.wikipedia.org/w/api.php',
            'it': 'https://it.wikipedia.org/w/api.php',
            'es': 'https://es.wikipedia.org/w/api.php',
            'nl': 'https://nl.wikipedia.org/w/api.php'
        }
        
        lang_to_base_url = {
            'en': 'https://en.wikipedia.org',
            'de': 'https://de.wikipedia.org', 
            'fr': 'https://fr.wikipedia.org',
            'it': 'https://it.wikipedia.org',
            'es': 'https://es.wikipedia.org',
            'nl': 'https://nl.wikipedia.org'
        }
        
        api_url = lang_to_api_url.get(lang, 'https://en.wikipedia.org/w/api.php')
        base_url = lang_to_base_url.get(lang, 'https://en.wikipedia.org')
        
        # Get article summary (intro section)
        summary_params = {
            'action': 'query',
            'format': 'json',
            'titles': article_title,
            'prop': 'extracts|info',
            'exintro': True,
            'explaintext': True,
            'inprop': 'url'
        }
        
        # Get full article content
        content_params = {
            'action': 'query',
            'format': 'json',
            'titles': article_title,
            'prop': 'extracts|info',
            'explaintext': True,
            'inprop': 'url'
        }
        
        try:
            # Fetch summary
            self._respect_rate_limit()
            summary_response = requests.get(api_url, params=summary_params, headers=self.headers)
            summary_response.raise_for_status()
            summary_data = summary_response.json()
            
            # Fetch full content
            self._respect_rate_limit()
            content_response = requests.get(api_url, params=content_params, headers=self.headers)
            content_response.raise_for_status()
            content_data = content_response.json()
            
            if ('query' in summary_data and 'pages' in summary_data['query'] and
                'query' in content_data and 'pages' in content_data['query']):
                
                summary_pages = summary_data['query']['pages']
                content_pages = content_data['query']['pages']
                
                summary_page = next(iter(summary_pages.values()))
                content_page = next(iter(content_pages.values()))
                
                # Check if page exists
                if 'missing' in summary_page or 'missing' in content_page:
                    print(f"Article '{article_title}' not found")
                    return None
                
                summary = summary_page.get('extract', '')
                content = content_page.get('extract', '')
                
                return {
                    'title': summary_page['title'],
                    'url': summary_page.get('fullurl', f"{base_url}/wiki/{summary_page['title'].replace(' ', '_')}"),
                    'summary': summary,
                    'content': content,
                    'length': len(content)
                }
            else:
                print(f"Invalid response structure for article '{article_title}'")
                return None
                
        except requests.RequestException as e:
            print(f"Error fetching content for article '{article_title}': {e}")
            return None
