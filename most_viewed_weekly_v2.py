import utilities.wikipedia_interface as wiki
import utilities.llm_interface as llm
import utilities.telegram_interface as telegram

country_list = ["IT"]
pages_to_exclude =  ["Main_Page", "Special:Search", "Pagina_principale", "Speciale:Ricerca", "Wikipedia:Hauptseite", "Spezial:Suche", "Wikipedia:Portada", "Especial:Buscar", "Wikipédia:Accueil_principal","Spécial:Recherche","Wikipedia:Featured_pictures"]
wiki_interface = wiki.WikipediaInterface()
top_articles = wiki_interface.get_top_n_articles_over_period(country_list, 'week', pages_to_exclude, top_n=5)

query = "These are the trending Wikipedia articles from last week:\n"
for article in top_articles:
    query += f"titolo: {article.replace('_', ' ')}\n"
    query += f"views: {top_articles[article]}\n\n"

system_instruction = """
  You are an AI assistant specialized in summarizing news articles and generating content for social media in ITALIAN.
  Respond only with the final report, ready to be posted on Telegram, formatted as follows:

    #WikipediaTrends <DATE> 📅

    <EMOTICON NUMBER 1> Article Title 1 <EMOTICON RELEVANT TO THE ARTICLE>
    <EMOTICON EYES> Views: X
    <EMOTICON QUESTION MARK> **<COSA or CHI ACCORDING TO THE SUBJECT> è**: <SHORT DESCRIPTION OF THE ARTICLE>
    <EMOTICON LIGHT_BULB> **Perché è in trend**: <REASON WHY THIS ARTICLE IS TRENDING>

    <EMOTICON NUMBER 2> Article Title 2 <EMOTICON RELEVANT TO THE ARTICLE>
    <EMOTICON EYES> Views: Y
    <EMOTICON QUESTION MARK> **<COSA or CHI ACCORDING TO THE SUBJECT> è**: <SHORT DESCRIPTION OF THE ARTICLE>
    <EMOTICON LIGHT_BULB> **Perché è in trend**: <REASON WHY THIS ARTICLE IS TRENDING>
    ...
  Do not include any other text or explanation.
"""

llm_interface = llm.LLMInterface(env_path='.env')
response = llm_interface.generate_text(system_instruction, query)

telegram_bot = telegram.TelegramInterface(env_path='.env')
telegram_bot.send_message(response)