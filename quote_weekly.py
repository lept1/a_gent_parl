#pip install quotes-library

from quotes_library import get_quotes,get_categories
import random

list_of_categories_nerd=['science','technology','math','engineering','programming','geek','computers','internet',
                         'robotics','cyberpunk','AI','astronomy','physics','space','data','hacking','nerdy',
                         'anime','gaming','comics','video games','board games','dungeons and dragons']

#cat = get_categories()



quotes = get_quotes(category=random.choice(list_of_categories_nerd), count=1, random=True) # random quotes
print(quotes['data'][0]['quote'] + " - " + quotes['data'][0]['author'])

