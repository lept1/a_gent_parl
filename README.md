# a_gent_parl

**a_gent_parl** is a Python project that fetches the most viewed Wikipedia articles for a given day and enriches them with related news headlines. It uses generative AI (Google Gemini) to summarize and format this information for sharing on Telegram, making it easy to keep your audience updated with trending topics and relevant news.

---

## Features

- Fetches top viewed Wikipedia articles by country and date using Wikimedia's API.
- Excludes generic or non-informative Wikipedia pages from results.
- Uses Google Gemini to generate a concise, Italian-language summary suitable for Telegram.
- Automatically posts the summary to a specified Telegram channel.

---

## Project Structure

```
a_gent_parl/
├── .env                  # Environment variables (API keys, tokens, etc.)
├── .gitignore
├── most_viewed_weekly.py  # Main script: Wikipedia/news fetch, AI summary, Telegram post
├── requirement.txt       # Python dependencies
├── tutorial.py           # Example: fetch top Wikipedia articles (simpler version)
├── wiki_sparsql_query.py # Example: SPARQL queries for Wikidata
```

---

## Setup

1. **Clone the repository**
   ```sh
   git clone https://github.com/lept1/a_gent_parl.git
   cd a_gent_parl
   ```

2. **Install dependencies**
   ```sh
   pip install -r requirement.txt
   ```

3. **Configure environment variables**

   Create a `.env` file in the project root (see `.env` for example keys):

   ```
   USER_WIKI=https://en.wikipedia.org/wiki/User:Leptone1
   GITHUB_REPO=https://github.com/lept1/a_gent_parl
   APP_NAME=a_gent_parl
   VERSION=0.0
   GEMINI_API_KEY=your_gemini_api_key
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   CHANNEL_ID=@your_channel_id
   ```

---

## Usage

Run the main script to fetch, summarize, and post the daily Wikipedia trends:

```sh
python most_viewed_weekly.py
```

- The script will:
  - Fetch last week's top Wikipedia articles for Italy.
  - For each article, use Gemini to generate a formatted summary in Italian.
  - Post the summary to your configured Telegram channel.

---

## Customization

- **Country**: Edit the `country_list` in `most_viewed_daily.py` to target other countries.
- **Number of articles**: Adjust the slicing and loop logic to fetch more or fewer articles.
- **Language/Formatting**: Modify the `system_instruction` string for different languages or output styles.

---

## Example Output

```
#WikipediaTrends 2025/07/30 📅

1️⃣ Mario Rossi 🇮🇹
👀 Views: 12345
❓ **Chi è**: Mario Rossi è stato un celebre attore italiano...
💡 **Perché è in trend**: Ricorre oggi il 70° anniversario della sua scomparsa...

2️⃣ Olimpiadi 2024 🏅
👀 Views: 9876
❓ **Cosa sono**: Le Olimpiadi sono il più importante evento sportivo internazionale...
💡 **Perché è in trend**: Si sono appena concluse le gare di atletica...
...
```

---

## License

MIT License

---

## Credits

- [Wikimedia REST API](https://wikimedia.org/api/rest_v1/)
