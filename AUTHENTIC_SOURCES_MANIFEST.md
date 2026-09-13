# 📜 Authentic Islamic Knowledge Manifest & Data Integrity
## Strictly Authentic Classical Sources (Zero AI Generation)

To safeguard against AI hallucinations and unverified statements, all Quranic verses and Hadiths used in **The Grand Majlis** are sourced exclusively from human-scholarly vetted, canonical repositories.

---

### 📁 Downloaded Local Databases

All files are stored in [`authentic_islamic_data/`](file:///C:/Users/sylas/.gemini/antigravity/scratch/khafos-islamic-discord/authentic_islamic_data):

| File Name | Description | Source / Provenance | Integrity Count |
| :--- | :--- | :--- | :---: |
| **`quran_arabic_uthmani.json`** | Complete Holy Quran in classical Medina Uthmani script. | **Tanzil.net** & **King Fahd Complex for the Printing of the Holy Quran** (Madinah al-Munawwarah). | **114 Surahs, 6,236 Ayahs** |
| **`quran_english_sahih.json`** | Complete English translation by **Saheeh International**. | Rigorously reviewed by international committees of Islamic scholars. | **114 Surahs, 6,236 Ayahs** |
| **`hadith_nawawi_arabic.json`** | *Al-Arba'in an-Nawawiyyah* in Arabic. | Compiled by **Imam Yahya ibn Sharaf an-Nawawi** (631–676 AH). | **42 Hadiths** |
| **`hadith_nawawi_english.json`** | *Al-Arba'in an-Nawawiyyah* in English. | Sunnah.com canonical translation with citations to Bukhari & Muslim. | **42 Hadiths** |
| **`hadith_bukhari_english.json`** | Complete *Al-Jami' al-Sahih* in English. | Compiled by **Imam Muhammad ibn Isma'il al-Bukhari** (194–256 AH). | **7,589 Hadiths** |
| **`hadith_muslim_english.json`** | Complete *Sahih Muslim* in English. | Compiled by **Imam Muslim ibn al-Hajjaj** (204–261 AH). | **7,563 Hadiths** |

---

### 🛡️ Why These Sources are 100% Reliable:

1. **Tanzil Project (Tanzil.net):**
   * Initiated in 2007 to provide a certified, error-free unicode text of the Holy Quran.
   * Cross-verified against the Mushaf al-Madinah published by King Fahd Glorious Quran Printing Complex.
   * Utilized as the underlying engine for Quran.com and major Islamic institutions worldwide.

2. **Sunnah.com Reference Corpus:**
   * The premier digital hadith database trusted globally by Islamic universities and scholars.
   * Contains exact book numbers, chapter numbers, and hadith numbers according to classical indexing standards (Fath al-Bari, etc.).

3. **No AI Generation Guarantee:**
   * The scripts read raw text directly from JSON files without passing prompts to large language models.
   * Every post includes exact Surah:Ayah numbers or Hadith numbers and grading.

---

### ⚡ Available Scripts:
* [`download_authentic_sources.py`](file:///C:/Users/sylas/.gemini/antigravity/scratch/khafos-islamic-discord/download_authentic_sources.py) — Re-downloads or updates the databases.
* [`post_verified_reminder.py`](file:///C:/Users/sylas/.gemini/antigravity/scratch/khafos-islamic-discord/post_verified_reminder.py) — Reads directly from the local files and posts authentic reminders to `#daily-ayah-hadith`.
