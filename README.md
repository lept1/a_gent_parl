# a_gent_parl 🤖

**a_gent_parl** is an intelligent Python automation suite that creates engaging social media content by combining Wikipedia data, Wikidata queries, and AI-powered content generation. The project automatically generates and posts Italian-language content to Telegram channels, covering trending topics, historical events, and gaming news.

---

## 🚀 Features

### Core Functionality
- **Wikipedia Trends Analysis**: Fetches and analyzes the most viewed Wikipedia articles by country and time period
- **Historical Events**: Discovers notable figures (comics artists, cartoonists, mangaka, fantasy writers, animators) who died on this day in history using SPARQL queries
- **AI-Powered Content Generation**: Uses Google Gemini to create engaging, formatted social media posts in Italian
- **Automated Telegram Publishing**: Posts content with images and captions to specified Telegram channels
- **Gaming Content**: Generates monthly PlayStation Plus game summaries
- **Image Processing**: Automatically processes and posts images with AI-generated captions

### Technical Features
- **Modular Architecture**: Clean separation of concerns with dedicated interface classes
- **Error Handling**: Robust retry mechanisms and error handling
- **Flexible Configuration**: Environment-based configuration management
- **Multi-source Data**: Integrates Wikipedia API, Wikidata SPARQL, and Wikimedia Commons

---

## 📁 Project Structure

```
a_gent_parl/
├── .env                          # Environment variables (API keys, tokens)
├── .gitignore
├── requirement.txt               # Python dependencies
├── README.md
├── __init__.py
│
├── utilities/                    # Core interface modules
│   ├── __init__.py
│   ├── llm_interface.py         # Google Gemini AI integration
│   ├── telegram_interface.py    # Telegram Bot API wrapper
│   └── wikipedia_interface.py   # Wikipedia/Wikidata API wrapper
│
├── images/                      # Image storage for posts
│
├── happened_today.py           # Legacy: Historical events (SPARQL-based)
├── happened_today_v2.py        # Enhanced: Historical events with images
├── most_viewed_weekly.py       # Legacy: Weekly Wikipedia trends
├── most_viewed_weekly_v2.py    # Enhanced: Modular weekly trends
├── post_image_weekly.py        # Image posting with AI captions
└── psnews_monthly.py           # PlayStation Plus monthly games
```

---

## 🛠️ Setup

### Prerequisites
- Python 3.8+
- Google Gemini API key
- Telegram Bot Token
- Telegram Channel ID

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/lept1/a_gent_parl.git
   cd a_gent_parl
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirement.txt
   ```

4. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```env
   USER_WIKI=https://en.wikipedia.org/wiki/User:YourUsername
   GITHUB_REPO=https://github.com/yourusername/a_gent_parl
   APP_NAME=a_gent_parl
   VERSION=1.0
   GEMINI_API_KEY=your_gemini_api_key_here
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   CHANNEL_ID=@your_channel_id
   ```

---

## 📖 Usage

### Weekly Wikipedia Trends
```bash
python most_viewed_weekly_v2.py
```
Generates a formatted post with the top 5 trending Wikipedia articles from the past week.

### Historical Events (This Day in History)
```bash
python happened_today_v2.py
```
Finds notable comics/animation industry figures who died on this day and creates a detailed biographical post with images.

### PlayStation Plus Monthly Games
```bash
python psnews_monthly.py
```
Creates a summary of the current month's PlayStation Plus Essential games.

### Image Posts with AI Captions
```bash
python post_image_weekly.py
```
Processes the oldest image in the `images/` folder, generates an AI caption, and posts to Telegram.

---

## 🔧 Customization

### Country Selection
Edit the `country_list` in scripts to target different countries:
```python
country_list = ["IT", "US", "GB"]  # Italy, United States, Great Britain
```

### Content Language
Modify the `system_instruction` in each script to change the output language:
```python
system_instruction = """
  You are an AI assistant specialized in generating content for social media in ENGLISH.
  # ... rest of instruction
"""
```

### Article Filtering
Customize the exclusion list to filter out unwanted pages:
```python
pages_to_exclude = ["Main_Page", "Special:Search", "Your_Custom_Page"]
```

---

## 📊 Example Outputs

### Wikipedia Trends
```
#WikipediaTrends 15 Gen 2025 📅

1️⃣ Intelligenza Artificiale 🤖
👀 Views: 45,231
❓ **Cosa è**: L'intelligenza artificiale è una tecnologia che simula l'intelligenza umana...
💡 **Perché è in trend**: Nuovi sviluppi nel settore hanno catturato l'attenzione globale...

2️⃣ Olimpiadi Invernali 2026 ⛷️
👀 Views: 32,156
❓ **Cosa sono**: Le Olimpiadi Invernali 2026 si terranno a Milano-Cortina...
💡 **Perché è in trend**: Annunciati i nuovi eventi e le sedi delle competizioni...
```

### Historical Events
```
#AccaddeOggi 15 Gen 📅

🎨 Stan Lee 🎨
📅 Nato il: 28 dicembre 1922 - Morto il: 12 novembre 2018
🏆 Premi Ricevuti: National Medal of Arts

Stanley Martin Lieber, meglio conosciuto come Stan Lee, è stato uno dei più influenti fumettisti e editori americani del XX secolo...
```

---

## 🏗️ Architecture

### Interface Classes

#### `LLMInterface`
- Handles Google Gemini API interactions
- Implements retry logic for API failures
- Supports grounding tools for enhanced accuracy

#### `TelegramInterface`
- Manages Telegram Bot API communications
- Supports both text messages and image posts
- Handles error responses and validation

#### `WikipediaInterface`
- Wraps Wikipedia and Wikidata APIs
- Provides methods for trending articles and historical data
- Implements date range utilities and filtering

---

## 🔒 Security Notes

- Keep your `.env` file secure and never commit it to version control
- Use environment variables for all sensitive configuration
- The provided `.env` file contains example/demo keys - replace with your own
- Consider using a secrets management service for production deployments

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Credits & APIs

- **[Wikimedia REST API](https://wikimedia.org/api/rest_v1/)** - Wikipedia article data
- **[Wikidata Query Service](https://query.wikidata.org/)** - SPARQL queries for structured data
- **[Google Gemini](https://ai.google.dev/)** - AI content generation
- **[Telegram Bot API](https://core.telegram.org/bots/api)** - Message and media posting
- **[Wikimedia Commons](https://commons.wikimedia.org/)** - Image resources

---

## 📈 Roadmap

- [ ] Add support for multiple languages
- [ ] Implement scheduling and automation
- [ ] Add analytics and engagement tracking
- [ ] Create web dashboard for content management
- [ ] Add support for other social media platforms
- [ ] Implement content moderation and filtering
