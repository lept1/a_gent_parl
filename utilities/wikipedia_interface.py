import requests
import sys
import os
from dotenv import load_dotenv
load_dotenv()

class WikipediaInterface:
    def __init__(self, env_path='.env'):
        self.env_path = env_path
        load_dotenv(self.env_path)
        self.USER_WIKI = os.getenv("USER_WIKI")
        if not self.USER_WIKI:
            raise ValueError("USER_WIKI not found in environment variables.")
        self.GITHUB_REPO = os.getenv("GITHUB_REPO")
        if not self.GITHUB_REPO:
            raise ValueError("GITHUB_REPO not found in environment variables.")
        self.APP_NAME = os.getenv("APP_NAME")
        if not self.APP_NAME:
            raise ValueError("APP_NAME not found in environment variables.")
        self.VERSION = os.getenv("VERSION")
        if not self.VERSION:
            raise ValueError("VERSION not found in environment variables.")
        self.headers = {'User-Agent': f'{self.APP_NAME}/{self.VERSION} ({self.GITHUB_REPO}; {self.USER_WIKI})'}
        self.WIKI_API_URL_METRICS = "https://wikimedia.org/api/rest_v1/metrics"
        self.WIKI_API_URL_SPARQL = "https://query.wikidata.org/sparql"
        self.user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])

    def get_top_articles_by_country(self, country_code, date):
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

    
    def get_results(self,endpoint_url, query):
        
        # TODO adjust user agent; see https://w.wiki/CX6
        sparql = SPARQLWrapper(endpoint_url, agent=self.user_agent)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        return sparql.query().convert()
