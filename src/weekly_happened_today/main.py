from src.utilities.wikipedia_interface import WikipediaInterface
from src.utilities.llm_interface import LLMInterface
from src.utilities.telegram_interface import TelegramInterface
from src.utilities.config_manager import ConfigManager

# Initialize configuration manager
config = ConfigManager('weekly_happened_today')
config.ensure_data_directories()

wiki_interface = WikipediaInterface()
llm_interface = LLMInterface(env_path=config.get_env_path())
telegram_interface = TelegramInterface(env_path=config.get_env_path())

professions=['wd:Q266569','wd:Q5434338','wd:Q191633','wd:Q1114448','wd:Q715301']
total_dict = wiki_interface.get_dead_on_date(professions)


prompt=f"This is a list of famous comics artists, cartoonists, mangaka, fantasy writers and animators who died today in history:\n"
for name, info in total_dict.items():
    prompt+=f"- {name} ({info['date_of_death']}): {info['description']}. Award received: {info['award_received']}\n"
# Now, use Gemini to create a Telegram post
prompt+=f"\n\n Choose the most relevant artist and generate a long and detailed description for him.\n"
#print(prompt)
system_instruction = """
  You are an AI assistant specialized generating content for social media in ITALIAN.
  Respond in a formatted way as follows:

    #AccaddeOggi <DD MMM> 📅

    <EMOTICON RELEVANT TO THE PERSON> **<Name>** <EMOTICON RELEVANT TO THE PERSON>
    <EMOTICON > Nato il: <DATE OF BIRTH if available> - Morto il: <DATE OF DEATH if available>
    <IF AWARD RECEIVED EMOTICON AWARD> Premi Ricevuti: <AWARD RECEIVED>
    <LONG DESCRIPTION>

  Do not include any other text or explanation.
"""

# LLM interface already initialized above
telegram_post = llm_interface.generate_text(system_instruction, prompt)
name = telegram_post.split("**")[1].strip()
# Now, get an image from Wikipedia
image_bytes = wiki_interface.get_random_wiki_image(name)
if image_bytes is None:
    # Load a default image
    telegram_interface.send_message(telegram_post)
else:
    telegram_interface.post_image_and_caption(image_bytes, telegram_post)