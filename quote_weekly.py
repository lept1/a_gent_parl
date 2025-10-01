import utilities.telegram_interface as telegram
import utilities.llm_interface as llm
import sqlite3
db_path = r"c:\Users\adellorto\projects\a_gent_parl\quote_db.sqlite3"
conn = sqlite3.connect(db_path)
cursor=conn.cursor()
query_text = 'SELECT * FROM Quote WHERE posted=0 AND (category LIKE ? OR category LIKE ? OR category LIKE ? OR category LIKE ?) ORDER BY RANDOM() LIMIT 1'
records = cursor.execute(query_text, ['%anime%','%comics%','%cartoon%','%manga%']).fetchall()

gemini = llm.LLMInterface(env_path='.env')
system_instruction = """
  You are an AI assistant that generates hashtags for quotes and content for social media in ITALIAN.
  Generate 3 relevant hashtags based on the quote and author provided. Use popular and trending hashtags where applicable. 
  Format the hashtags as a space-separated list, each starting with a # symbol, without any additional text or punctuation.
  Respond only with the final report, ready to be posted on Telegram, formatted as follows:

    #QuoteOfTheDay <GENERATED HASHTAGS> 

    ***<QUOTE TEXT TRANSLATED IN ITALIAN>***
    _<AUTHOR NAME>_

    <SHORT DESCRIPTION OF THE AUTHOR AND WHERE THE QUOTE IS FROM>

  Do not include any other text or explanation.
"""

query = f"quote: {records[0][3]}\nauthor: {records[0][1]}"

telegram_post = gemini.generate_text(system_instruction, query)

telegram_bot = telegram.TelegramInterface(env_path='.env')
telegram_bot.send_message(telegram_post)

print(telegram_post)

# Mark as posted
query_text = 'UPDATE Quote SET posted=1 WHERE id=?'
cursor.execute(query_text, (records[0][0],))
conn.commit()
print(f"Marked quote id {records[0][0]} as posted.")


# csvfile = r"c:\Users\adellorto\Downloads\quotes.csv\quotes.csv"
# import pandas as pd
# df = pd.read_csv(csvfile)
# df['id'] = df.index + 1
# df['posted'] = 0
# df = df[['id','author','category','quote','posted']]
# df.to_sql('Quote', conn, if_exists='append', index=False)

