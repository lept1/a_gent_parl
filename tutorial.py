
import requests as rq
import datetime as dt
headers = {'User-Agent': 'a_gent_parl/0.0 (https://github.com/lept1/a_gent_parl; https://en.wikipedia.org/wiki/User:Leptone1)'}
base_url = "https://wikimedia.org/api/rest_v1/metrics"
#format today date to yyyy/mm/dd string
today = (dt.datetime.now() - dt.timedelta(days=1)).strftime("%Y/%m/%d")
view_url = f"{base_url}/pageviews/top/en.wikipedia.org/all-access/{today}"

print(f"Fetching data from {view_url}")

view_response = rq.get(view_url, headers=headers, params={"limit": 10}).json()