from src.utilities.llm_interface import LLMInterface
from src.utilities.telegram_interface import TelegramInterface
from src.utilities.config_manager import ConfigManager

import datetime as dt

# Initialize configuration manager
config = ConfigManager('monthly_psnews')
config.ensure_data_directories()

# generating list of days in the last week in fromat YYYY/MM/DD
this_month = dt.datetime.now().strftime("%B %Y")

query = "What are the monthly games on PS Plus Essential for " + this_month + "?"

system_instruction = """
  You are an AI assistant specialized in summarizing news articles and generating content for social media in ITALIAN. 
  Respond only with the final report, ready to be posted on Telegram, formatted as follows:

#PSPlus <MONTH> <YEAR> <EMOTICON VIDEOGAME>

<EMOTICON RELEVANT TO THE GAME 1> Game 1 <EMOTICON RELEVANT TO THE GAME 1>
<SHORT DESCRIPTION OF THE GAME 1, SHORT SUMMARY OF THE CRITICS OF THE GAME 1, DESCRIBE HOW MUCH POPULAR THE GAME IS>

<EMOTICON RELEVANT TO THE GAME 2> Game 2 <EMOTICON RELEVANT TO THE GAME 2>
<SHORT DESCRIPTION OF THE GAME 2, SHORT SUMMARY OF THE CRITICS OF THE GAME 2, DESCRIBE HOW MUCH POPULAR THE GAME 2 IS>

...

Do not include any other text or explanation.
"""

llm_interface = LLMInterface(env_path=config.get_env_path())
response = llm_interface.generate_text(system_instruction, query)

telegram_bot = TelegramInterface(env_path=config.get_env_path())
telegram_bot.send_message(response)