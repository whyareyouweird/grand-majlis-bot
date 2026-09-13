# The Grand Majlis — Islamic Community Discord Bot

An authentic Islamic community Discord bot built for **The Grand Majlis** (hosted by **Khafos**).

## Features
- **100% Verified Classical Scholarship:** Zero AI hallucination or generation. Classical Quranic text (Medina Uthmani from Tanzil), Saheeh International translation, At-Tafsir al-Muyassar, and Hadiths from Sahih al-Bukhari, Sahih Muslim, 40 Hadith an-Nawawi, Hadith Qudsi, and Muwatta Malik.
- **Halal Gender Verification Ticket System:** Private voice note verification for segregated Brother/Sister lounges.
- **Dynamic Member Counter:** Live updating voice channel indicator.
- **Automated Welcomer:** Welcomes new members in `#general-lounge` with their exact member number and Islamic greeting.
- **Daily Reminders:** Automated daily morning & evening scholarly reflections.

## Cloud Deployment (Render)

### Environment Variables
- `DISCORD_BOT_TOKEN` *(Required)*: Your Discord Bot Token from the Discord Developer Portal.
- `PYTHONUNBUFFERED`: `1`

### Commands
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python daily_scholarly_bot.py`
