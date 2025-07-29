# pip install sparqlwrapper
# https://rdflib.github.io/sparqlwrapper/

import sys
from SPARQLWrapper import SPARQLWrapper, JSON

endpoint_url = "https://query.wikidata.org/sparql"

#Occupation: comics artist

query_comics_artists = """
SELECT ?comicArtist ?comicArtistDescription ?award_receivedLabel ?date_of_death WHERE {
  ?comicArtist wdt:P31 wd:Q5;
    wdt:P106 wd:Q715301.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],it". }
  OPTIONAL { ?comicArtist wdt:P570 ?date_of_death. }
  OPTIONAL { ?comicArtist wdt:P166 ?award_received. }
  FILTER((((DAY(?date_of_death)) = (DAY(NOW()))) && ((MONTH(?date_of_death)) = (MONTH(NOW())))) && ((YEAR(?date_of_death)) = ((YEAR(NOW())) - 70 )))
}
ORDER BY DESC (?date_of_death)"""

query_cartoonist = """
SELECT ?comicArtist ?comicArtistDescription ?award_receivedLabel ?date_of_death WHERE {
  ?comicArtist wdt:P31 wd:Q5;
    wdt:P106 wd:Q715301.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],it". }
  OPTIONAL { ?comicArtist wdt:P570 ?date_of_death. }
  OPTIONAL { ?comicArtist wdt:P166 ?award_received. }
  FILTER((((DAY(?date_of_death)) = (DAY(NOW()))) && ((MONTH(?date_of_death)) = (MONTH(NOW())))) && ((YEAR(?date_of_death)) = ((YEAR(NOW())) - 70 )))
}
ORDER BY DESC (?date_of_death)"""

query_mangaka = """
SELECT ?comicArtist ?comicArtistDescription ?award_receivedLabel ?date_of_death WHERE {
  ?comicArtist wdt:P31 wd:Q5;
    wdt:P106 wd:Q715301.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],it". }
  OPTIONAL { ?comicArtist wdt:P570 ?date_of_death. }
  OPTIONAL { ?comicArtist wdt:P166 ?award_received. }
  FILTER((((DAY(?date_of_death)) = (DAY(NOW()))) && ((MONTH(?date_of_death)) = (MONTH(NOW())))) && ((YEAR(?date_of_death)) = ((YEAR(NOW())) - 70 )))
}
ORDER BY DESC (?date_of_death)"""

query_fantasy_writer = """
SELECT ?comicArtist ?comicArtistDescription ?award_receivedLabel ?date_of_death WHERE {
  ?comicArtist wdt:P31 wd:Q5;
    wdt:P106 wd:Q715301.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],it". }
  OPTIONAL { ?comicArtist wdt:P570 ?date_of_death. }
  OPTIONAL { ?comicArtist wdt:P166 ?award_received. }
  FILTER((((DAY(?date_of_death)) = (DAY(NOW()))) && ((MONTH(?date_of_death)) = (MONTH(NOW())))) && ((YEAR(?date_of_death)) = ((YEAR(NOW())) - 70 )))
}
ORDER BY DESC (?date_of_death)"""

query_scifi_writer = """
SELECT ?comicArtist ?comicArtistDescription ?award_receivedLabel ?date_of_death WHERE {
  ?comicArtist wdt:P31 wd:Q5;
    wdt:P106 wd:Q715301.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],it". }
  OPTIONAL { ?comicArtist wdt:P570 ?date_of_death. }
  OPTIONAL { ?comicArtist wdt:P166 ?award_received. }
  FILTER((((DAY(?date_of_death)) = (DAY(NOW()))) && ((MONTH(?date_of_death)) = (MONTH(NOW())))) && ((YEAR(?date_of_death)) = ((YEAR(NOW())) - 70 )))
}
ORDER BY DESC (?date_of_death)"""


def get_results(endpoint_url, query):
    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    # TODO adjust user agent; see https://w.wiki/CX6
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()


results = get_results(endpoint_url, query)

for result in results["results"]["bindings"]:
    print(result)
