"""
Grand Majlis - 24/7 Authentic Islamic Daily Scholarly & Community Bot
====================================================================
Features:
1. 100% Authentic Classical Sources (Tanzil, King Fahd Complex, Sunnah.com)
2. Daily Quran & Hadith posting with persistent deduplication (daily_tracker.json)
3. Auto-Role on join: Automatically gives '🤍 ∙ Mu'min (Verified)' to every newcomer
4. Live Voice Member Counter: Updates '👥 Members: X' channel on join/leave (no duplicates)
5. Voice Verification Ticket System for Halal Gender Spaces:
   - Interactive Discord Buttons in #verify-and-roles
   - Private ticket channels with audio verification sentence requirement
   - Staff one-click [✅ Approve & Grant Role] and [🔒 Close Ticket] buttons
6. Button-based notification toggles (Announcements, Daily Reminders, Live Stages)
7. Rich Welcome Messages in #general-lounge (1548478278376095744):
   - Full Salam (السَّلَامُ عَلَيْكُمْ وَرَحْمَةُ ٱللَّٰهِ وَبَرَكَاتُهُ)
   - Ordinal member milestone (e.g. 27th seeker of knowledge)
   - Server navigation guide
   - Sahih Muslim 1893 Hadith encouraging sharing for the sake of Islam
8. Interactive commands (!daily, !quran, !hadith, !status, !testwelcome, !setuproles)
"""

import discord
from discord.ext import commands, tasks
import json
import os
import sys
import datetime
import traceback
import asyncio
import re
from collections import defaultdict, deque

RECENT_LOGS = deque(maxlen=250)

class LogCapture:
    def __init__(self, original):
        self.original = original
    def write(self, s):
        if s:
            try:
                text = s.decode('utf-8', errors='replace') if isinstance(s, bytes) else str(s)
                RECENT_LOGS.append(text)
            except Exception:
                pass
        if self.original:
            try:
                self.original.write(s)
            except Exception:
                pass
    def flush(self):
        if self.original:
            try:
                self.original.flush()
            except Exception:
                pass

if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    sys.stdout = LogCapture(sys.stdout)

if sys.stderr:
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
    sys.stderr = LogCapture(sys.stderr)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==============================================================================
# OPUS AUDIO ENGINE LOADER (Required for Discord Voice Playback on Linux / Render)
# ==============================================================================
if not discord.opus.is_loaded():
    candidates = [
        # System-installed (via apt-get install libopus0 in Docker)
        "libopus.so.0",
        "libopus.so",
        "opus",
        # Bundled fallback
        os.path.join(BASE_DIR, "libopus.so.0"),
        os.path.join(BASE_DIR, "libopus.so"),
    ]
    for candidate in candidates:
        try:
            discord.opus.load_opus(candidate)
            print(f"🎵 Successfully loaded Opus audio engine: {candidate}")
            break
        except Exception:
            pass

    if not discord.opus.is_loaded():
        print("⚠️ Notice: Discord Opus library could not be loaded via custom paths.")
    else:
        print("✅ Discord Opus voice transmission engine is fully active!")

# Load token from environment or local .env file
TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
if not TOKEN:
    env_file = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("DISCORD_BOT_TOKEN="):
                        TOKEN = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
        except Exception:
            pass

if not TOKEN:
    print("❌ ERROR: DISCORD_BOT_TOKEN is not set! Please set it in Render environment variables or .env file.")
    sys.exit(1)

GUILD_ID = 1548474725133459516
GENERAL_CHANNEL_ID = 1548478278376095744
VERIFY_CHANNEL_ID = 1548478260461961356
DATA_DIR = os.path.join(BASE_DIR, "authentic_islamic_data")
TRACKER_FILE = os.path.join(BASE_DIR, "daily_tracker.json")

# Curated foundational Quranic passages for daily reflections
FOUNDATIONAL_AYAHS = [
    (2, 255),   # Ayat al-Kursi
    (2, 285),   # The Messenger has believed...
    (2, 286),   # Allah does not burden a soul...
    (1, 1),     # Surah Al-Fatiha
    (94, 5),    # For indeed, with hardship [will be] ease
    (103, 1),   # Surah Al-Asr (By time, indeed mankind is in loss...)
    (112, 1),   # Surah Al-Ikhlas (Pure Monotheism)
    (3, 102),   # O you who have believed, fear Allah as He should be feared...
    (3, 103),   # And hold firmly to the rope of Allah...
    (49, 10),   # The believers are but brothers...
    (49, 13),   # O mankind, indeed We have created you from male and female...
    (31, 17),   # Luqman: Establish prayer, enjoin what is right, forbid what is wrong...
    (39, 53),   # Say, O My servants who have transgressed against themselves...
    (17, 23),   # And your Lord has decreed that you not worship except Him, and to parents, good treatment...
    (25, 63),   # And the servants of the Most Merciful are those who walk upon the earth easily...
    (59, 22),   # He is Allah, other than whom there is no deity...
    (14, 7),    # If you are grateful, I will surely increase you...
    (65, 2),    # And whoever fears Allah - He will make for him a way out...
    (65, 3),    # And will provide for him from where he does not expect...
    (2, 152),   # So remember Me; I will remember you...
    (2, 186),   # And when My servants ask you concerning Me, indeed I am near...
    (57, 16),   # Has the time not come for those who have believed that their hearts should become humbly subdued...
]

def get_ordinal(n: int) -> str:
    """Return ordinal string (e.g. 1st, 2nd, 3rd, 27th)."""
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"

def load_tracker():
    if os.path.exists(TRACKER_FILE):
        try:
            with open(TRACKER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_posted_date": "", "quran_step": 0, "hadith_step": 0}

def save_tracker(tracker):
    with open(TRACKER_FILE, "w", encoding="utf-8") as f:
        json.dump(tracker, f, indent=2)

def load_data():
    print("📖 Loading verified classical reference datasets into memory...")
    with open(os.path.join(DATA_DIR, "quran_arabic_uthmani.json"), "r", encoding="utf-8") as f:
        quran_ar = json.load(f)["data"]["surahs"]
    with open(os.path.join(DATA_DIR, "quran_english_sahih.json"), "r", encoding="utf-8") as f:
        quran_en = json.load(f)["data"]["surahs"]
    with open(os.path.join(DATA_DIR, "quran_tafsir_muyassar.json"), "r", encoding="utf-8") as f:
        quran_tafsir = json.load(f)["data"]["surahs"]
    with open(os.path.join(DATA_DIR, "hadith_nawawi_arabic.json"), "r", encoding="utf-8") as f:
        nawawi_ar = json.load(f)["hadiths"]
    with open(os.path.join(DATA_DIR, "hadith_nawawi_english.json"), "r", encoding="utf-8") as f:
        nawawi_en = json.load(f)["hadiths"]
    with open(os.path.join(DATA_DIR, "hadith_qudsi_arabic.json"), "r", encoding="utf-8") as f:
        qudsi_ar = json.load(f)["hadiths"]
    with open(os.path.join(DATA_DIR, "hadith_qudsi_english.json"), "r", encoding="utf-8") as f:
        qudsi_en = json.load(f)["hadiths"]
    with open(os.path.join(DATA_DIR, "hadith_bukhari_english.json"), "r", encoding="utf-8") as f:
        bukhari_en = json.load(f)["hadiths"]

    print("   Quran: 114 Surahs, 6236 Ayahs loaded.")
    print("   Hadiths: Nawawi 40, Qudsi 40, Bukhari 7589 loaded.")
    return {
        "quran_ar": quran_ar,
        "quran_en": quran_en,
        "quran_tafsir": quran_tafsir,
        "nawawi_ar": nawawi_ar,
        "nawawi_en": nawawi_en,
        "qudsi_ar": qudsi_ar,
        "qudsi_en": qudsi_en,
        "bukhari_en": bukhari_en,
    }

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
db = None

# ==============================================================================
# DUAL-TRACK LEVELING & CHANNEL LOCKDOWN ENGINE
# ==============================================================================

LEVELS_FILE = os.path.join(BASE_DIR, "levels_data.json")

# Aesthetic numbered milestone roles for Text and Voice
TEXT_LEVEL_ROLES = [
    (5, "[Chat Lvl 5] 🥉 ∙ Talib (Seeker)", 0xCD7F32),
    (10, "[Chat Lvl 10] 🥈 ∙ Mutakallim (Eloquent)", 0xC0C0C0),
    (20, "[Chat Lvl 20] 🥇 ∙ Faqih (Discerner)", 0xFFD700),
    (30, "[Chat Lvl 30] 💎 ∙ Allamah (Scholarly)", 0x00CED1),
    (50, "[Chat Lvl 50] 👑 ∙ Sabiqoon (Foremost)", 0x9932CC)
]

VOICE_LEVEL_ROLES = [
    (5, "[Voice Lvl 5] 🥉 ∙ Sami' (Attentive)", 0xA0522D),
    (10, "[Voice Lvl 10] 🥈 ∙ Jalis (Companion)", 0x708090),
    (20, "[Voice Lvl 20] 🥇 ∙ Murabit (Steadfast)", 0xDAA520),
    (30, "[Voice Lvl 30] 💎 ∙ Muhibb (Devoted)", 0x20B2AA),
    (50, "[Voice Lvl 50] 👑 ∙ Muqarrab (Drawn Near)", 0x8A2BE2)
]

READONLY_CHANNEL_KEYWORDS = [
    "rules-and-adab",
    "verify-and-roles",
    "daily-ayah-hadith",
    "level-alerts",
    "level-ups",
    "announcements",
    "information",
    "welcome"
]

def xp_required_for_level(lvl: int) -> int:
    """Returns total cumulative XP required to achieve level 'lvl'."""
    if lvl <= 0:
        return 0
    return int(25 * (lvl ** 2) + 75 * lvl)

def level_from_xp(xp: int) -> int:
    """Calculates the integer level corresponding to a given XP total."""
    lvl = 0
    while xp >= xp_required_for_level(lvl + 1):
        lvl += 1
    return lvl

def get_progress_bar(current_xp: int, level: int, length: int = 10) -> str:
    """Renders an aesthetic green and white progress bar."""
    current_base = xp_required_for_level(level)
    next_req = xp_required_for_level(level + 1)
    diff = next_req - current_base
    if diff <= 0:
        return "🟩" * length
    progress = max(0.0, min(1.0, (current_xp - current_base) / diff))
    filled = int(round(progress * length))
    return "🟩" * filled + "⬜" * (length - filled)

_levels_cache = None

def load_levels() -> dict:
    global _levels_cache
    if _levels_cache is not None:
        return _levels_cache
    if os.path.exists(LEVELS_FILE):
        try:
            with open(LEVELS_FILE, "r", encoding="utf-8") as f:
                _levels_cache = json.load(f)
                return _levels_cache
        except Exception as e:
            print(f"Notice loading levels: {e}")
    _levels_cache = {}
    return _levels_cache

def save_levels():
    global _levels_cache
    if _levels_cache is None:
        return
    try:
        with open(LEVELS_FILE, "w", encoding="utf-8") as f:
            json.dump(_levels_cache, f, indent=2)
    except Exception as e:
        print(f"Notice saving levels: {e}")

def get_user_stats(user_id: int) -> dict:
    levels = load_levels()
    uid = str(user_id)
    if uid not in levels:
        levels[uid] = {
            "text_xp": 0,
            "text_level": 0,
            "voice_xp": 0,
            "voice_level": 0,
            "last_text_xp": 0,
            "messages": 0,
            "voice_minutes": 0
        }
    return levels[uid]

async def get_or_create_level_alert_channel(guild: discord.Guild):
    """Finds or creates the dedicated ┊・🎉・level-alerts channel with proper read-only permissions."""
    ch = discord.utils.get(guild.text_channels, name="┊・🎉・level-alerts")
    if not ch:
        ch = next((c for c in guild.text_channels if "level-alert" in c.name or "level-up" in c.name), None)
    if ch:
        return ch

    target_cat = discord.utils.get(guild.categories, name="╭─・💬 ∙ 𝐂𝐎𝐌𝐌𝐔𝐍𝐈𝐓𝐘 ∙ 𝐌𝐀𝐉𝐋𝐈𝐒")
    if not target_cat:
        target_cat = discord.utils.get(guild.categories, name="╭─・📢 ∙ 𝐈𝐍𝐅𝐎𝐑𝐌𝐀𝐓𝐈𝐎𝐍")

    verified_role = discord.utils.get(guild.roles, name="🤍 ∙ Mu'min (Verified)")
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, embed_links=True, attach_files=True)
    }
    if verified_role:
        overwrites[verified_role] = discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True)

    try:
        if target_cat:
            ch = await target_cat.create_text_channel(
                name="┊・🎉・level-alerts",
                overwrites=overwrites,
                topic="Celebration & milestone announcements for active community members 🕊️"
            )
        else:
            ch = await guild.create_text_channel(
                name="┊・🎉・level-alerts",
                overwrites=overwrites,
                topic="Celebration & milestone announcements for active community members 🕊️"
            )
        print("🎉 Created dedicated level alert channel: #┊・🎉・level-alerts")
        return ch
    except Exception as e:
        print(f"Notice creating level alert channel: {e}")
        return None

async def ensure_milestone_roles(guild: discord.Guild):
    """Ensures all Text and Voice milestone roles exist with aesthetic colors."""
    all_roles = TEXT_LEVEL_ROLES + VOICE_LEVEL_ROLES
    for lvl, role_name, color_int in all_roles:
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            try:
                await guild.create_role(
                    name=role_name,
                    colour=discord.Colour(color_int),
                    mentionable=False,
                    reason="Islamic leveling milestone role"
                )
                print(f"✨ Created milestone role: '{role_name}'")
            except Exception as e:
                print(f"Notice creating role '{role_name}': {e}")

async def check_and_grant_milestone_roles(member: discord.Member, track: str, new_level: int) -> list:
    """Grants any newly unlocked milestone roles for the track and returns list of granted role names."""
    milestones = TEXT_LEVEL_ROLES if track == "text" else VOICE_LEVEL_ROLES
    granted = []
    for req_lvl, role_name, color_int in milestones:
        if new_level >= req_lvl:
            role = discord.utils.get(member.guild.roles, name=role_name)
            if not role:
                try:
                    role = await member.guild.create_role(
                        name=role_name,
                        colour=discord.Colour(color_int),
                        mentionable=False,
                        reason="Islamic leveling milestone role"
                    )
                except Exception:
                    pass
            if role and role not in member.roles:
                try:
                    await member.add_roles(role, reason=f"Reached {track.title()} Level {new_level}")
                    granted.append(role_name)
                    print(f"🏆 Granted '{role_name}' to {member.name}")
                except Exception as e:
                    print(f"Notice granting role: {e}")
    return granted

async def announce_level_up(member: discord.Member, track: str, new_level: int, total_xp: int):
    """Sends an aesthetic embed in #level-alerts and pings the user."""
    ch = await get_or_create_level_alert_channel(member.guild)
    if not ch:
        return

    new_roles = await check_and_grant_milestone_roles(member, track, new_level)

    is_text = (track == "text")
    track_title = "💬 ∙ Chatting & Knowledge Activity" if is_text else "🎙️ ∙ Voice & Halaqah Presence"
    track_icon = "💬" if is_text else "🎙️"
    color = 0xFFD700 if is_text else 0x00CED1

    desc = (
        f"**السَّلَامُ عَلَيْكُمْ وَرَحْمَةُ ٱللَّٰهِ وَبَرَكَاتُهُ, {member.mention}!**\n\n"
        f"Mabrook! You have advanced to **{track_icon} {track.title()} Level {new_level}** in **The Grand Majlis**! 🎉\n\n"
        f"• **Track:** `{track_title}`\n"
        f"• **Current Level:** `Level {new_level}`\n"
        f"• **Total {track.title()} XP:** `{total_xp:,} XP`\n"
    )

    if new_roles:
        desc += f"\n👑 **New Milestone Role{'s' if len(new_roles) > 1 else ''} Unlocked:**\n" + "\n".join(f"• **`{r}`**" for r in new_roles) + "\n"

    if is_text:
        quote = "*\"Whoever takes a path upon which he procures knowledge, Allah will make easy for him the path to Paradise.\" (Sahih Muslim 2699)*"
    else:
        quote = "*\"No people sit together remembering Allah except that the angels surround them, mercy covers them, and tranquility descends upon them.\" (Sahih Muslim 2700)*"

    embed = discord.Embed(
        title=f"🎉 ∙ Level Up: {track.title()} Level {new_level}!",
        description=desc + f"\n> {quote}",
        color=color
    )
    if member.display_avatar:
        embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="The Grand Majlis ∙ Rewarding Dedication & Knowledge 🤍")

    try:
        await ch.send(
            content=f"🎉 Congratulations {member.mention}!",
            embed=embed,
            allowed_mentions=discord.AllowedMentions(users=True)
        )
    except Exception as e:
        print(f"Notice sending level alert: {e}")

async def enforce_channel_lockdowns(guild: discord.Guild):
  """Ensures read-only channels are strictly locked so normal members cannot type in them."""
  verified_role = discord.utils.get(guild.roles, name="🤍 ∙ Mu'min (Verified)")
  mod_role = discord.utils.get(guild.roles, name="🛡️ ∙ Muhtasib (Moderator)")
  owner_role = discord.utils.get(guild.roles, name="👑 ∙ Khafos")

  for ch in guild.text_channels:
    ch_name = ch.name.lower()
    is_readonly = (
        any(target in ch_name for target in READONLY_CHANNEL_KEYWORDS)
        or ch.id == VERIFY_CHANNEL_ID
    )

    if is_readonly:
      try:
        await ch.set_permissions(
            guild.default_role,
            send_messages=False,
            create_public_threads=False,
            create_private_threads=False,
            send_messages_in_threads=False,
            reason="Lockdown read-only channel",
        )
        if verified_role:
          await ch.set_permissions(
              verified_role,
              send_messages=False,
              create_public_threads=False,
              create_private_threads=False,
              send_messages_in_threads=False,
              reason="Lockdown read-only channel",
          )
        if mod_role:
          await ch.set_permissions(
              mod_role,
              send_messages=True,
              manage_messages=True,
              reason="Staff access in read-only channel",
          )
        if owner_role:
          await ch.set_permissions(
              owner_role,
              send_messages=True,
              reason="Owner access in read-only channel",
          )
      except Exception as e:
        print(f"Notice locking #{ch.name}: {e}")

# ==============================================================================
# UI COMPONENTS: TICKET & VERIFICATION DASHBOARD
# ==============================================================================

class TicketStaffView(discord.ui.View):
    """Staff controls inside a member's verification ticket (persistent across restarts)."""
    def __init__(self, target_user_id: int = None, gender_type: str = None):
        super().__init__(timeout=None)
        self.target_user_id = target_user_id
        self.gender_type = gender_type

    @discord.ui.button(label="Approve & Grant Role", emoji="✅", style=discord.ButtonStyle.success, custom_id="ticket_approve_btn")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Verify permissions: must have manage_roles, manage_channels, or be admin
        perms = interaction.user.guild_permissions
        if not (perms.manage_roles or perms.manage_channels or perms.administrator):
            await interaction.response.send_message("❌ Only moderators can approve verification tickets.", ephemeral=True)
            return

        await interaction.response.defer()

        guild = interaction.guild
        target_id = self.target_user_id
        gender = self.gender_type

        # Recover target_id and gender if not set (e.g. after a bot restart)
        if (not target_id or not gender) and interaction.channel.topic:
            m_id = re.search(r"user_id:(\d+)", interaction.channel.topic)
            if m_id:
                target_id = int(m_id.group(1))
            m_g = re.search(r"gender:(\w+)", interaction.channel.topic)
            if m_g:
                gender = m_g.group(1)

        if not gender:
            if "brother" in interaction.channel.name.lower():
                gender = "brother"
            elif "sister" in interaction.channel.name.lower():
                gender = "sister"

        if not target_id:
            for target in interaction.channel.overwrites.keys():
                if isinstance(target, discord.Member) and target.id != bot.user.id and not target.guild_permissions.manage_channels:
                    target_id = target.id
                    break

        role_name = "🧔 ∙ Brother" if (gender and gender.lower() == "brother") else "🧕 ∙ Sister"
        role = discord.utils.get(guild.roles, name=role_name)

        target_member = None
        if target_id:
            target_member = guild.get_member(target_id)
            if not target_member:
                try:
                    target_member = await guild.fetch_member(target_id)
                except Exception:
                    pass

        if not target_member:
            await interaction.followup.send("❌ Target member not found in server.", ephemeral=True)
            return

        if role:
            try:
                await target_member.add_roles(role)
            except Exception as e:
                print(f"Error adding role: {e}")

            await interaction.followup.send(
                f"✅ **Approved by {interaction.user.mention}!**\n"
                f"Granted **{role.name}** to {target_member.mention}.\n"
                f"*This ticket will automatically close in 5 seconds...*"
            )
            await asyncio.sleep(5)
            try:
                await interaction.channel.delete()
            except Exception:
                pass
        else:
            await interaction.followup.send(f"❌ Role '{role_name}' was not found in server.", ephemeral=True)

    @discord.ui.button(label="Close Ticket", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="ticket_close_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        perms = interaction.user.guild_permissions
        is_mod = perms.manage_roles or perms.manage_channels or perms.administrator

        target_id = self.target_user_id
        if not target_id and interaction.channel.topic:
            m = re.search(r"user_id:(\d+)", interaction.channel.topic)
            if m:
                target_id = int(m.group(1))

        is_owner = target_id and interaction.user.id == target_id

        if not (is_mod or is_owner):
            await interaction.followup.send("❌ You do not have permission to close this ticket.", ephemeral=True)
            return

        await interaction.followup.send(f"🔒 **Ticket closing by {interaction.user.mention}...**")
        await asyncio.sleep(2)
        try:
            await interaction.channel.delete()
        except Exception as e:
            print(f"Error deleting ticket channel: {e}")


class VerificationDashboardView(discord.ui.View):
    """The interactive dashboard in #verify-and-roles."""
    def __init__(self):
        super().__init__(timeout=None)

    async def open_gender_ticket(self, interaction: discord.Interaction, gender_type: str):
        # 1. DEFER IMMEDIATELY (<50ms) to prevent any Discord interaction timeout
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        user = interaction.user

        # 2. Check if user already has an active ticket
        sanitized_name = "".join(c for c in user.name.lower() if c.isalnum() or c in "-_")[:12]
        ticket_name = f"verify-{gender_type.lower()}-{sanitized_name}"

        existing = discord.utils.get(guild.text_channels, name=ticket_name)
        if existing:
            await interaction.followup.send(
                f"⚠️ You already have an open verification ticket: {existing.mention}",
                ephemeral=True
            )
            return

        # 3. Find or create ticket category
        cat_tickets = discord.utils.get(guild.categories, name="╭─・🎫 ∙ 𝐓𝐈𝐂𝐊𝐄𝐓𝐒")
        if not cat_tickets:
            cat_tickets = await guild.create_category("╭─・🎫 ∙ 𝐓𝐈𝐂𝐊𝐄𝐓𝐒", position=1)

        # 4. Channel overwrites (private)
        role_mod = discord.utils.get(guild.roles, name="🛡️ ∙ Muhtasib (Moderator)")
        role_owner = discord.utils.get(guild.roles, name="👑 ∙ Khafos")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, read_message_history=True),
        }
        if role_mod:
            overwrites[role_mod] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True)
        if role_owner:
            overwrites[role_owner] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        # 5. Create channel
        ticket_ch = await cat_tickets.create_text_channel(
            name=ticket_name,
            overwrites=overwrites,
            topic=f"Voice verification for {user.name} ({gender_type}) | user_id:{user.id} | gender:{gender_type.lower()}"
        )

        # 6. Generate clean sentence stating their exact username
        custom_sentence = f"Assalamu Alaikum, my username is {user.name} and I am verifying as a {gender_type} for The Grand Majlis."

        role_target = "🧔 ∙ Brother" if gender_type == "Brother" else "🧕 ∙ Sister"
        
        embed_prompt = discord.Embed(
            title=f"🎙️ ∙ Voice Verification for {role_target}",
            description=(
                f"**السَّلَامُ عَلَيْكُمْ وَرَحْمَةُ ٱللَّٰهِ وَبَرَكَاتُهُ, {user.mention}!**\n\n"
                "To preserve modesty (*Haya*) and protect the privacy of our gender-segregated spaces, "
                "we require members to verify their gender via a short voice note.\n\n"
                "--- \n"
                "### 🗣️ ∙ What you need to do:\n"
                f"Please record and send a **short voice message** in this channel reciting the following sentence:\n\n"
                f"> **« {custom_sentence} »**\n\n"
                "--- \n"
                "🔒 **Privacy Notice:**\n"
                "• This ticket is strictly private and hidden from the public.\n"
                "• A moderator will review your voice note and grant your role.\n"
                "• Once verified, this ticket will be closed and permanently deleted."
            ),
            color=0xFDFDFD
        )
        embed_prompt.set_footer(text="The Grand Majlis ∙ Preserving Modesty & Trust 🤍")

        staff_view = TicketStaffView(target_user_id=user.id, gender_type=gender_type)
        await ticket_ch.send(
            content=f"🕊️ {user.mention}, your private verification space is ready.",
            embed=embed_prompt,
            view=staff_view
        )

        await interaction.followup.send(
            f"✅ Your private verification ticket has been created: {ticket_ch.mention}\n"
            f"Please go there to record your verification voice note.",
            ephemeral=True
        )

    # BUTTON 1: VERIFY AS BROTHER
    @discord.ui.button(label="Verify as Brother", emoji="🧔", style=discord.ButtonStyle.secondary, custom_id="btn_verify_brother", row=0)
    async def btn_brother(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.open_gender_ticket(interaction, "Brother")

    # BUTTON 2: VERIFY AS SISTER
    @discord.ui.button(label="Verify as Sister", emoji="🧕", style=discord.ButtonStyle.secondary, custom_id="btn_verify_sister", row=0)
    async def btn_sister(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.open_gender_ticket(interaction, "Sister")

    # BUTTON 3: TOGGLE ANNOUNCEMENTS PING
    @discord.ui.button(label="Khafos Announcements", emoji="📢", style=discord.ButtonStyle.primary, custom_id="btn_ping_announce", row=1)
    async def btn_ping_announce(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        role = discord.utils.get(interaction.guild.roles, name="📢 ∙ Khafos Announcements")
        if not role:
            await interaction.followup.send("Role not found.", ephemeral=True)
            return
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.followup.send(f"🔕 Removed **{role.name}** role.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.followup.send(f"🔔 Added **{role.name}** role!", ephemeral=True)

    # BUTTON 4: TOGGLE DAILY AYAH PING
    @discord.ui.button(label="Daily Ayah & Hadith", emoji="📖", style=discord.ButtonStyle.primary, custom_id="btn_ping_ayah", row=1)
    async def btn_ping_ayah(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        role = discord.utils.get(interaction.guild.roles, name="📖 ∙ Daily Ayah & Hadith")
        if not role:
            await interaction.followup.send("Role not found.", ephemeral=True)
            return
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.followup.send(f"🔕 Removed **{role.name}** role.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.followup.send(f"🔔 Added **{role.name}** role!", ephemeral=True)

    # BUTTON 5: TOGGLE LIVE HALAQAH PING
    @discord.ui.button(label="Live Halaqah & Stage", emoji="🎙️", style=discord.ButtonStyle.primary, custom_id="btn_ping_stage", row=1)
    async def btn_ping_stage(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        role = discord.utils.get(interaction.guild.roles, name="🎙️ ∙ Live Halaqah & Stage")
        if not role:
            await interaction.followup.send("Role not found.", ephemeral=True)
            return
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.followup.send(f"🔕 Removed **{role.name}** role.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.followup.send(f"🔔 Added **{role.name}** role!", ephemeral=True)


async def publish_verification_dashboard(guild, force=False):
    """Publish or update the clean dashboard in #verify-and-roles ONLY if missing or forced."""
    ch = guild.get_channel(VERIFY_CHANNEL_ID)
    if not ch:
        return

    # Check if dashboard already exists
    if not force:
        try:
            bot_msgs = []
            async for msg in ch.history(limit=25):
                if msg.author.id == bot.user.id and msg.embeds:
                    for e in msg.embeds:
                        if "Roles & Gender Verification Dashboard" in (e.title or ""):
                            bot_msgs.append(msg)
                            break
            if bot_msgs:
                # Clean up any leftover duplicate dashboard messages from previous resets
                if len(bot_msgs) > 1:
                    for extra in bot_msgs[1:]:
                        try:
                            await extra.delete()
                        except Exception:
                            pass
                print("ℹ️ Verification dashboard already exists in #verify-and-roles. Will NOT resend on reset.")
                return
        except Exception as e:
            print(f"Notice checking existing verify message: {e}")

    # Clean old messages in verify channel and post fresh
    try:
        await ch.purge(limit=20)
    except Exception as e:
        print(f"Purge verify channel notice: {e}")

    embed = discord.Embed(
        title="🤍 ∙ Roles & Gender Verification Dashboard",
        description=(
            "Welcome to the role customization center for **The Grand Majlis**.\n"
            "Use the interactive buttons below to select notification alerts and request access to private spaces:\n\n"
            "--- \n"
            "### 🌿 ∙ Halal Gender Lounges (Voice Verification Required):\n"
            "To safeguard modesty (*Haya*) and prevent unauthorized entry, access to the gender lounges requires a short voice verification.\n\n"
            "• Click **`[🧔 Verify as Brother]`** or **`[🧕 Verify as Sister]`** to open a private ticket.\n"
            "• Send a short voice note stating your username to verify.\n"
            "• A moderator will review your voice note and grant you the role.\n\n"
            "--- \n"
            "### 🔔 ∙ Notification Alerts (Click to Toggle):\n"
            "📢 ∙ **Khafos Announcements** — Alerts when Khafos uploads new content or goes live.\n"
            "📖 ∙ **Daily Ayah & Hadith** — Morning and evening classical Quran/Hadith reminders.\n"
            "🎙️ ∙ **Live Halaqah & Stage** — Pinged when voice study circles or stages begin."
        ),
        color=0xFFFFFF
    )
    embed.set_footer(text="The Grand Majlis ∙ Click buttons below to interact")

    view = VerificationDashboardView()
    await ch.send(embed=embed, view=view)
    print("✅ Published Verification Dashboard with buttons into #verify-and-roles!")

# ==============================================================================
# SERVER MAINTENANCE & MONITORING
# ==============================================================================

async def update_member_counter(guild):
    """Ensure the locked voice channel reflects the exact live member count and SERVER STATS stays at position 0."""
    count = guild.member_count
    target_name = f"👥 Members: {count}"
    
    cat_stats = discord.utils.get(guild.categories, name="╭─・📊 ∙ 𝐒𝐄𝐑𝐕𝐄𝐑 ∙ 𝐒𝐓𝐀𝐓𝐒")
    if not cat_stats:
        try:
            cat_stats = await guild.create_category("╭─・📊 ∙ 𝐒𝐄𝐑𝐕𝐄𝐑 ∙ 𝐒𝐓𝐀𝐓𝐒", position=0)
        except Exception:
            pass
    elif cat_stats.position != 0:
        try:
            await cat_stats.edit(position=0)
        except Exception:
            pass

    # Find any voice channels that contain 'Members:'
    matching_vcs = [c for c in guild.voice_channels if "Members:" in c.name]
    
    # Clean up any duplicate counter channels if multiple exist
    if len(matching_vcs) > 1:
        for extra in matching_vcs[1:]:
            try:
                await extra.delete()
            except Exception:
                pass

    if matching_vcs:
        vc = matching_vcs[0]
        kwargs = {}
        if vc.name != target_name:
            kwargs["name"] = target_name
        if cat_stats and vc.category_id != cat_stats.id:
            kwargs["category"] = cat_stats
            kwargs["position"] = 0
        if kwargs:
            try:
                await vc.edit(**kwargs)
                print(f"Updated member counter: {kwargs}")
            except Exception as e:
                print(f"Notice on updating counter channel: {e}")
    else:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=True, connect=False)
        }
        if cat_stats:
            await cat_stats.create_voice_channel(target_name, overwrites=overwrites, position=0)
        else:
            await guild.create_voice_channel(target_name, overwrites=overwrites, position=0)
        print(f"Created member counter voice channel: '{target_name}'")

def build_welcome_text(member):
    """Build a concise, non-embedded welcome message with member count on top."""
    guild = member.guild
    ordinal_str = get_ordinal(guild.member_count)

    c_rules = discord.utils.get(guild.text_channels, name="┊・📜・rules-and-adab")
    c_verify = discord.utils.get(guild.text_channels, name="┊・🤍・verify-and-roles")
    c_daily = discord.utils.get(guild.text_channels, name="┊・🕋・daily-ayah-hadith")

    rules_tag = f"<#{c_rules.id}>" if c_rules else "#rules-and-adab"
    verify_tag = f"<#{c_verify.id}>" if c_verify else "#verify-and-roles"
    daily_tag = f"<#{c_daily.id}>" if c_daily else "#daily-ayah-hadith"

    return (
        f"You are our **{ordinal_str}** member!\n"
        f"السَّلَامُ عَلَيْكُمْ وَرَحْمَةُ ٱللَّٰهِ وَبَرَكَاتُهُ {member.mention}, welcome to The Grand Majlis 🕊️\n\n"
        f"• Read the rules in {rules_tag}\n"
        f"• Pick your roles / voice verify for gender spaces in {verify_tag}\n"
        f"• Check daily Quran & Hadith reminders in {daily_tag}\n\n"
        "Feel free to introduce yourself here! Invite your friends for the sake of Islam: "
        "*\"Whoever guides someone to goodness will have a reward like one who did it.\" (Sahih Muslim 1893)*"
    )

async def post_daily_if_due(force=False):
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return False

    channel = discord.utils.get(guild.text_channels, name="┊・🕋・daily-ayah-hadith")
    if not channel:
        return False

    tracker = load_tracker()
    today_str = datetime.date.today().isoformat()

    if not force:
        # 1. Check local tracker
        if tracker.get("last_posted_date") == today_str:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Daily reminder already recorded for today ({today_str}). Skipping.")
            return False

        # 2. Check Discord channel directly (cross-reset single source of truth)
        try:
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            async for msg in channel.history(limit=15):
                if msg.author.id == bot.user.id and msg.embeds:
                    # If posted within the last 18 hours or on the same UTC day, skip!
                    age_hours = (now_utc - msg.created_at).total_seconds() / 3600
                    if age_hours < 18 or msg.created_at.date() == now_utc.date():
                        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Daily reminder was already sent to Discord today ({age_hours:.1f}h ago). Skipping.")
                        tracker["last_posted_date"] = today_str
                        save_tracker(tracker)
                        return False
        except Exception as e:
            print(f"Notice checking channel history: {e}")

    q_step = tracker.get("quran_step", 0) % len(FOUNDATIONAL_AYAHS)
    h_step = tracker.get("hadith_step", 0)

    surah_num, ayah_num = FOUNDATIONAL_AYAHS[q_step]
    s_idx = surah_num - 1
    a_idx = ayah_num - 1

    s_name_ar = db["quran_ar"][s_idx]["name"]
    s_name_en = db["quran_en"][s_idx]["englishName"]
    ayah_ar = db["quran_ar"][s_idx]["ayahs"][a_idx]["text"]
    ayah_en = db["quran_en"][s_idx]["ayahs"][a_idx]["text"]
    tafsir_raw = db["quran_tafsir"][s_idx]["ayahs"][a_idx]["text"]
    tafsir_snippet = tafsir_raw[:450] + ("..." if len(tafsir_raw) > 450 else "")

    date_display = datetime.datetime.now().strftime("%A, %B %d, %Y")

    # 1. Quran Embed
    embed_quran = discord.Embed(
        title=f"📖 ∙ Daily Quranic Reflection: {s_name_en} ({s_name_ar}) [{surah_num}:{ayah_num}]",
        description=(
            f"### {ayah_ar}\n\n"
            f"> *\"{ayah_en}\"*\n\n"
            "--- \n"
            f"**📜 Classical Tafsir (التفسير الميسر — مجمع الملك فهد):**\n"
            f"*{tafsir_snippet}*\n\n"
            "**Verified Source:** Tanzil.net & King Fahd Complex (Madinah)\n"
            "**Translation:** Saheeh International"
        ),
        color=0xFDFCFA
    )
    embed_quran.set_footer(text=f"The Grand Majlis ∙ {date_display} ∙ Verified Classical Text")

    # 2. Hadith Selection
    total_nawawi = len(db["nawawi_ar"])
    total_qudsi = len(db["qudsi_ar"])
    total_cycles = total_nawawi + total_qudsi

    idx_cycle = h_step % total_cycles
    if idx_cycle < total_nawawi:
        h_num = idx_cycle + 1
        h_ar_text = db["nawawi_ar"][idx_cycle]["text"]
        h_en_text = db["nawawi_en"][idx_cycle]["text"]
        
        ar_first_line = h_ar_text.splitlines()[0] if h_ar_text else ""
        if len(ar_first_line) > 80:
            ar_first_line = ar_first_line[:80] + "..."

        embed_hadith = discord.Embed(
            title=f"📜 ∙ Authentic Hadith: Al-Arba'in an-Nawawiyyah (Hadith #{h_num})",
            description=(
                f"### {ar_first_line}\n\n"
                f"> *\"{h_en_text[:700]}{'...' if len(h_en_text) > 700 else ''}\"*\n\n"
                "--- \n"
                "**Anthology:** *Al-Arba'in an-Nawawiyyah* — Imam Yahya ibn Sharaf an-Nawawi (d. 676 AH)\n"
                "**Scholarly Grading:** **Sahih (صحيح)** — Verified Sunnah.com Canonical Index"
            ),
            color=0xF5F5F7
        )
    else:
        q_idx = idx_cycle - total_nawawi
        h_num = q_idx + 1
        h_en_text = db["qudsi_en"][q_idx]["text"]

        embed_hadith = discord.Embed(
            title=f"📜 ∙ Authentic Hadith: Forty Hadith Qudsi (Hadith #{h_num})",
            description=(
                f"> *\"{h_en_text[:700]}{'...' if len(h_en_text) > 700 else ''}\"*\n\n"
                "--- \n"
                "**Category:** Sacred Prophetic Sayings of Divine Speech (الحديث القدسي)\n"
                "**Scholarly Grading:** **Sahih (صحيح)** — Verified Canonical Reference"
            ),
            color=0xF5F5F7
        )

    embed_hadith.set_footer(text="The Grand Majlis ∙ Zero AI Generation ∙ Authentic Corpus")

    await channel.send(embed=embed_quran)
    await channel.send(embed=embed_hadith)
    print(f"✅ Published Daily Reminder for {today_str} (Quran Step: {q_step}, Hadith Step: {h_step})")

    tracker["last_posted_date"] = today_str
    tracker["quran_step"] = q_step + 1
    tracker["hadith_step"] = h_step + 1
    save_tracker(tracker)
    return True

# ==============================================================================
# 24/7 QURAN RECITATION VOICE STREAMER
# ==============================================================================

def get_ffmpeg_path():
    """Get FFmpeg path — prefer system-installed (Docker apt) over imageio-ffmpeg static binary."""
    import shutil
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        print(f"🎬 Using system FFmpeg: {system_ffmpeg}")
        return system_ffmpeg
    try:
        import imageio_ffmpeg
        import stat
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        try:
            os.chmod(exe, os.stat(exe).st_mode | stat.S_IEXEC)
        except Exception:
            pass
        print(f"🎬 Using imageio-ffmpeg: {exe}")
        return exe
    except Exception:
        return "ffmpeg"

FFMPEG_BEFORE_OPTS = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 3 -timeout 15000000 -nostdin"
FFMPEG_OPTS = "-vn -loglevel warning"

# Load all 54 authentic tracks for Sheikh Abdullah Al-Qarni from Internet Archive
QARNI_TRACKS = {}
qarni_file = os.path.join(BASE_DIR, "qarni_tracks.json")
if os.path.exists(qarni_file):
    try:
        with open(qarni_file, "r", encoding="utf-8") as f:
            QARNI_TRACKS = {int(k): v for k, v in json.load(f).items()}
        print(f"📖 Loaded {len(QARNI_TRACKS)} authentic tracks for Sheikh Abdullah Al-Qarni!")
    except Exception as e:
        print(f"Notice loading qarni_tracks: {e}")

QURAN_RECITERS = [
    {"name": "Sheikh Abdullah Al-Qarni", "url": None, "tracks": QARNI_TRACKS},
    {"name": "Sheikh Mishary Rashid Alafasy", "url": "https://server8.mp3quran.net/afs/{surah:03d}.mp3"},
    {"name": "Sheikh Abdul Basit Abdul Samad", "url": "https://server7.mp3quran.net/basit/{surah:03d}.mp3"},
    {"name": "Sheikh Yasser Al-Dossari", "url": "https://server11.mp3quran.net/yasser/{surah:03d}.mp3"},
    {"name": "Sheikh Maher Al-Muaiqly", "url": "https://server12.mp3quran.net/maher/{surah:03d}.mp3"},
    {"name": "Sheikh Nasser Al-Qatami", "url": "https://server6.mp3quran.net/qtm/{surah:03d}.mp3"},
    {"name": "Sheikh Mahmoud Khalil Al-Husary", "url": "https://server13.mp3quran.net/husr/{surah:03d}.mp3"},
    {"name": "Sheikh Abu Bakr Al-Shatri", "url": "https://server11.mp3quran.net/shatri/{surah:03d}.mp3"},
    {"name": "Sheikh Saad Al-Ghamdi", "url": "https://server7.mp3quran.net/s_gmd/{surah:03d}.mp3"},
    {"name": "Sheikh Saud Al-Shuraim", "url": "https://server7.mp3quran.net/shur/{surah:03d}.mp3"},
    {"name": "Sheikh Abdul Rahman Al-Sudais", "url": "https://server11.mp3quran.net/sds/{surah:03d}.mp3"},
]

FAVORITE_SURAHS = [
    1, 18, 19, 20, 36, 49, 50, 55, 56, 59, 67, 75, 76, 78, 87, 89, 93, 94, 95, 96, 97, 103, 108, 112, 113, 114,
    2, 3, 12, 14, 21, 23, 25, 31, 32, 39, 48, 53, 62
]

TARATEEL_RADIO_URL = "https://backup.qurango.net/radio/tarateel"

playlist_index = 0
current_recitation = {
    "title": "Continuous Quran Recitation",
    "reciter": "World Renowned Qaris",
    "surah_num": 1,
    "url": None
}
is_radio_mode = False
selected_reciter_mode = "qarni"  # Default: Sheikh Abdullah Al-Qarni (54 Surahs rotation)
_play_lock = asyncio.Lock()

async def play_next_recitation(guild):
    """Play the next beautiful Surah recitation or live stream."""
    global playlist_index, current_recitation, is_radio_mode, selected_reciter_mode

    vc = guild.voice_client
    if not vc or not vc.is_connected():
        print("⚠️ play_next_recitation: No voice client or not connected, skipping.")
        return

    # Non-blocking check: if already advancing, let the watchdog retry later
    if _play_lock.locked():
        print("⚠️ play_next_recitation: Lock held, deferring to watchdog.")
        return

    async with _play_lock:
        try:
            if vc.is_playing() or vc.is_paused():
                vc.stop()
                await asyncio.sleep(0.3)

            ffmpeg_exe = get_ffmpeg_path()
            if is_radio_mode:
                url = TARATEEL_RADIO_URL
                title = "24/7 Live Tarateel Radio"
                reciter = "Various World Renowned Qaris"
                current_recitation = {"title": title, "reciter": reciter, "surah_num": None, "url": url}
            elif selected_reciter_mode == "qarni" and QARNI_TRACKS:
                qarni_keys = sorted(QARNI_TRACKS.keys())
                surah_num = qarni_keys[playlist_index % len(qarni_keys)]
                playlist_index += 1
                url = QARNI_TRACKS[surah_num]
                reciter = "Sheikh Abdullah Al-Qarni"

                surah_name = f"Surah #{surah_num}"
                if db and "quran_en" in db and surah_num <= len(db["quran_en"]):
                    surah_name = f"Surah {db['quran_en'][surah_num - 1]['englishName']}"

                title = surah_name
                current_recitation = {
                    "title": title,
                    "reciter": reciter,
                    "surah_num": surah_num,
                    "url": url
                }
            else:
                # Try up to len(FAVORITE_SURAHS) times to find a valid surah+reciter combo
                url = None
                for _attempt in range(len(FAVORITE_SURAHS)):
                    surah_num = FAVORITE_SURAHS[playlist_index % len(FAVORITE_SURAHS)]
                    reciter_obj = QURAN_RECITERS[(playlist_index // len(FAVORITE_SURAHS)) % len(QURAN_RECITERS)]
                    playlist_index += 1

                    # Handle reciters with per-surah track dicts (e.g. Internet Archive collections)
                    tracks = reciter_obj.get("tracks")
                    if tracks:
                        if surah_num in tracks:
                            url = tracks[surah_num]
                            break
                        else:
                            continue  # This reciter doesn't have this surah, try next
                    else:
                        url = reciter_obj["url"].format(surah=surah_num)
                        break

                if not url:
                    print("⚠️ Could not find a valid surah+reciter combo, skipping.")
                    return

                surah_name = f"Surah #{surah_num}"
                if db and "quran_en" in db and surah_num <= len(db["quran_en"]):
                    surah_name = f"Surah {db['quran_en'][surah_num - 1]['englishName']}"

                title = surah_name
                reciter = reciter_obj["name"]
                current_recitation = {
                    "title": title,
                    "reciter": reciter,
                    "surah_num": surah_num,
                    "url": url
                }

            def after_playing(error):
                if error:
                    print(f"Quran playback finished with note: {error}")
                else:
                    print(f"✅ Finished playing: {current_recitation.get('title', '?')}")

                async def delayed_next():
                    await asyncio.sleep(1.0)
                    await play_next_recitation(guild)

                try:
                    asyncio.run_coroutine_threadsafe(delayed_next(), bot.loop)
                except Exception as schedule_err:
                    print(f"⚠️ Could not schedule next track: {schedule_err}")

            source = discord.FFmpegPCMAudio(
                url,
                executable=ffmpeg_exe,
                before_options=FFMPEG_BEFORE_OPTS,
                options=FFMPEG_OPTS
            )
            audio_volume = discord.PCMVolumeTransformer(source, volume=1.0)
            vc.play(audio_volume, after=after_playing)
            print(f"▶️ [Quran VC] Now transmitting: {title} by {reciter} | URL: {url}")

            # Update bot presence so everyone in the server sees what is playing
            try:
                await bot.change_presence(
                    activity=discord.Activity(
                        type=discord.ActivityType.listening,
                        name=f"{title} ∙ {reciter[:18]} 🕊️"
                    ),
                    status=discord.Status.online
                )
            except Exception:
                pass
        except Exception as e:
            print(f"❌ Error starting Quran recitation: {e}")
            import traceback as _tb
            _tb.print_exc()
            # Auto-skip to next track after a brief delay
            await asyncio.sleep(3)
            try:
                asyncio.run_coroutine_threadsafe(play_next_recitation(guild), bot.loop)
            except Exception:
                pass

@tasks.loop(seconds=30)
async def ensure_quran_vc_stream():
    """Ensure bot stays connected 24/7 in ┊・📖・quran-recitation-vc and continues playing."""
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return

    QURAN_VC_ID = 1548478297996787756
    quran_vc = guild.get_channel(QURAN_VC_ID)
    if not quran_vc:
        quran_vc = discord.utils.get(guild.voice_channels, name="┊・📖・quran-recitation-vc")
    if not quran_vc:
        quran_vc = next((c for c in guild.voice_channels if "quran-recitation-vc" in c.name), None)
    if not quran_vc:
        return

    vc = guild.voice_client

    # 1. If we have an active connected VoiceClient:
    if vc and vc.is_connected():
        if vc.channel.id != quran_vc.id:
            try:
                await vc.move_to(quran_vc)
            except Exception:
                pass
        if not vc.is_playing() and not vc.is_paused():
            print("Quran stream idle in VC. Resuming recitation...")
            await play_next_recitation(guild)
        return

    # 2. If we do NOT have an active connected VoiceClient:
    if vc and not vc.is_connected():
        print("Found disconnected VoiceClient, cleaning up before reconnect...")
        try:
            await vc.disconnect(force=True)
        except Exception:
            pass
        vc = None

    try:
        print("Connecting bot to Quran Recitation VC...")
        vc = await quran_vc.connect(reconnect=True, timeout=30.0, self_deaf=False, self_mute=False)
        await asyncio.sleep(2)
        await play_next_recitation(guild)
    except discord.ClientException as ce:
        print(f"VoiceClient status notice: {ce}")
        if vc and vc.is_connected() and not vc.is_playing():
            await play_next_recitation(guild)
    except Exception as e:
        print(f"Notice connecting to Quran VC: {e}")

@tasks.loop(minutes=1)
async def voice_xp_tracker_loop():
    """Awards Voice Activity XP (20 XP/min) to members active in voice channels."""
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return

    for vc in guild.voice_channels:
        # Skip member count channel
        if "Members:" in vc.name:
            continue

        for member in vc.members:
            if member.bot:
                continue
            # Skip if deafened (not participating/listening)
            if member.voice and (member.voice.self_deaf or member.voice.deaf or member.voice.suppressed):
                continue

            stats = get_user_stats(member.id)
            old_lvl = stats["voice_level"]
            stats["voice_xp"] += 20  # 20 XP per active minute
            stats["voice_minutes"] += 1
            new_lvl = level_from_xp(stats["voice_xp"])
            stats["voice_level"] = new_lvl

            save_levels()

            if new_lvl > old_lvl:
                try:
                    await announce_level_up(member, "voice", new_lvl, stats["voice_xp"])
                except Exception as e:
                    print(f"Error announcing voice level up: {e}")

@tasks.loop(minutes=15)
async def check_daily_schedule():
    """Checks every 15 minutes, but only triggers during the morning window (06:00 - 06:30 UTC)."""
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    if now_utc.hour == 6 and now_utc.minute < 30:
        await post_daily_if_due(force=False)

@bot.event
async def on_ready():
    global db
    print(f"✨ Grand Majlis Bot is ONLINE as {bot.user.name} ({bot.user.id})")
    db = load_data()
    
    # Register persistent views
    bot.add_view(VerificationDashboardView())
    bot.add_view(TicketStaffView())
    
    guild = bot.get_guild(GUILD_ID)
    if guild:
        # Sync voice member counter
        await update_member_counter(guild)
        # Ensure dashboard in #verify-and-roles exists (skips if already posted)
        await publish_verification_dashboard(guild)
        # Ensure dedicated level alert channel exists
        await get_or_create_level_alert_channel(guild)
        # Ensure all numbered milestone roles exist
        await ensure_milestone_roles(guild)
        # Enforce read-only channel permissions lockdown
        await enforce_channel_lockdowns(guild)

    if not check_daily_schedule.is_running():
        check_daily_schedule.start()
        print("⏰ 30-minute background calendar monitor is active!")

    if not ensure_quran_vc_stream.is_running():
        ensure_quran_vc_stream.start()
        print("🎙️ 24/7 Quran VC Recitation watchdog active!")

    if not voice_xp_tracker_loop.is_running():
        voice_xp_tracker_loop.start()
        print("🎙️ 1-minute Voice XP tracking loop active!")

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="Daily Quran & Sahih Hadith 🕊️"
        ),
        status=discord.Status.online
    )

@bot.event
async def on_member_join(member):
    """Automatically assigns verified role, updates counter, and welcomes in general-lounge."""
    guild = member.guild
    print(f"👤 New member joined: {member.name} (ID: {member.id})")

    # 1. AUTO-ROLE: '🤍 ∙ Mu'min (Verified)'
    role = discord.utils.get(guild.roles, name="🤍 ∙ Mu'min (Verified)")
    if role:
        try:
            await member.add_roles(role)
            print(f"   Auto-assigned role '{role.name}' to {member.name}")
        except Exception as e:
            print(f"   Could not auto-assign role: {e}")

    # 2. UPDATE VOICE MEMBER COUNTER
    await update_member_counter(guild)

    # 3. SEND FULL SALAM & WELCOME GUIDE IN GENERAL LOUNGE
    general_ch = guild.get_channel(GENERAL_CHANNEL_ID)
    if general_ch:
        try:
            welcome_msg = build_welcome_text(member)
            await general_ch.send(welcome_msg)
            print(f"   Sent welcome message for {member.name} in #{general_ch.name}")
        except Exception as e:
            print(f"   Error sending welcome message: {e}")

@bot.event
async def on_member_remove(member):
    """Update voice member counter when someone leaves."""
    await update_member_counter(member.guild)

# ==============================================================================
# ANTI-ADMIN ABUSE & ISLAMIC ADAB SECURITY ENGINE
# ==============================================================================

PROFANITY_PATTERNS = [
    r"f[\W_]*[\*u@4o]+[\W_]*c*[\W_]*k+",
    r"f[\W_]*\*+[\W_]*k+",
    r"f+[\W_]*u+[\W_]*c+[\W_]*k+",
    r"s+[\W_]*[h#]+[\W_]*[\*i!1|]+[\W_]*t+",
    r"s+[\W_]*\*+[\W_]*t+",
    r"b+[\W_]*[\*i!1|]+[\W_]*t+[\W_]*c+[\W_]*h+",
    r"c+[\W_]*[\*u@4]+[\W_]*n+[\W_]*t+",
    r"a+[\W_]*[s$5]{2,}[\W_]*h+[\W_]*[o0]+[\W_]*l+[\W_]*e+",
    r"w+[\W_]*h+[\W_]*[o0]+[\W_]*r+[\W_]*e+",
    r"s+[\W_]*l+[\W_]*[\*u]+[\W_]*t+",
    r"d+[\W_]*[\*i!1|]+[\W_]*c+[\W_]*k+",
    r"p+[\W_]*[\*u]+[\W_]*[s$5]{2,}[\W_]*y+",
    r"n+[\W_]*[\*i!1|]+[\W_]*g+[\W_]*g+[\W_]*[e3a4]+[\W_]*r*",
    r"f+[\W_]*[a@4]+[\W_]*g+[\W_]*g+[\W_]*[o0]+[\W_]*t+",
    r"r+[\W_]*[e3]+[\W_]*t+[\W_]*[a@4]+[\W_]*r+[\W_]*d+",
    r"\bk+y+s+\b",
    r"\bs+t+f+u+\b",
]
COMPILED_PROFANITY = [re.compile(p, re.IGNORECASE) for p in PROFANITY_PATTERNS]

INVITE_REGEX = re.compile(
    r"(?:https?://)?(?:www\.)?(?:discord\.(?:gg|io|me|li)|discord(?:app)?\.com/invite)/[a-zA-Z0-9]+",
    re.IGNORECASE
)

SUSPICIOUS_LINKS = re.compile(
    r"(grabify|iplogger|2no\.co|blasze|free-nitro|steamcommunity[^\s/]*\.link|discrod|dlscord)",
    re.IGNORECASE
)

def check_profanity(text: str) -> bool:
    for pattern in COMPILED_PROFANITY:
        if pattern.search(text):
            return True
    return False

user_msg_times = defaultdict(list)
staff_action_history = defaultdict(list)

async def check_staff_abuse(guild: discord.Guild, action_type: discord.AuditLogAction, threshold: int):
    """Detect and stop rogue moderators from mass-banning or deleting channels/roles."""
    try:
        async for entry in guild.audit_logs(limit=1, action=action_type):
            actor = entry.user
            if not actor or actor.bot or actor.id == guild.owner_id or actor.id == bot.user.id:
                return

            now = datetime.datetime.now(datetime.timezone.utc).timestamp()
            key = (actor.id, action_type)
            history = staff_action_history[key]
            history = [t for t in history if now - t < 60]
            history.append(now)
            staff_action_history[key] = history

            if len(history) >= threshold:
                member = guild.get_member(actor.id)
                if member:
                    # Strip dangerous staff roles immediately
                    roles_to_remove = [
                        r for r in member.roles 
                        if r.permissions.kick_members or r.permissions.ban_members or 
                           r.permissions.manage_channels or r.permissions.manage_roles or 
                           r.permissions.manage_messages or r.permissions.administrator
                    ]
                    if roles_to_remove:
                        try:
                            await member.remove_roles(*roles_to_remove, reason="Anti-Admin Abuse: Mass action detected")
                        except Exception as e:
                            print(f"Error revoking staff roles: {e}")

                    # Apply emergency 28-day timeout
                    try:
                        await member.timeout(datetime.timedelta(days=28), reason="Anti-Admin Abuse: Emergency security lock")
                    except Exception as e:
                        print(f"Error applying emergency timeout: {e}")

                    log_ch = discord.utils.get(guild.text_channels, name="╰・📊・server-logs")
                    desk_ch = discord.utils.get(guild.text_channels, name="┊・📋・moderation-desk")
                    
                    alert_embed = discord.Embed(
                        title="🚨 ∙ EMERGENCY: ANTI-ADMIN ABUSE TRIGGERED",
                        description=(
                            f"**Rogue Account:** {member.mention} (`{member.name}` - ID: `{member.id}`)\n"
                            f"**Action Detected:** Rapid {action_type.name.replace('_', ' ').title()} ({len(history)} in under 60 seconds)\n\n"
                            "🛡️ **Automated Security Protocol Executed:**\n"
                            "• All moderation and administrative roles have been revoked.\n"
                            "• Account has been placed in an immediate 28-day timeout.\n"
                            "• Server channels and member roster are protected."
                        ),
                        color=0xFF0000
                    )
                    alert_embed.set_footer(text="The Grand Majlis ∙ Anti-Nuke Shield 🤍")

                    if log_ch:
                        await log_ch.send(content=f"⚠️ <@{guild.owner_id}> Emergency Anti-Admin Abuse Alert!", embed=alert_embed)
                    if desk_ch:
                        await desk_ch.send(embed=alert_embed)
    except Exception as e:
        print(f"Notice in check_staff_abuse: {e}")

@bot.event
async def on_member_ban(guild, user):
    await check_staff_abuse(guild, discord.AuditLogAction.ban, threshold=3)

@bot.event
async def on_guild_channel_delete(channel):
    await check_staff_abuse(channel.guild, discord.AuditLogAction.channel_delete, threshold=2)

@bot.event
async def on_guild_role_delete(role):
    await check_staff_abuse(role.guild, discord.AuditLogAction.role_delete, threshold=2)

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    guild = message.guild
    if not guild:
        await bot.process_commands(message)
        return

    author = message.author
    is_owner = (author.id == guild.owner_id)

    # 1. ANTI-SPAM PINGS: @everyone and @here protection (only Owner allowed)
    if not is_owner and (message.mention_everyone or "@everyone" in message.content or "@here" in message.content):
        try:
            await message.delete()
        except Exception:
            pass
        try:
            await author.timeout(datetime.timedelta(hours=1), reason="Anti-Abuse: Unauthorized @everyone/@here ping")
        except Exception:
            pass

        log_ch = discord.utils.get(guild.text_channels, name="╰・📊・server-logs")
        if log_ch:
            embed = discord.Embed(
                title="🛡️ ∙ Anti-Abuse: Unauthorized Mention Blocked",
                description=f"**User:** {author.mention} (`{author.name}`)\n**Channel:** {message.channel.mention}\n**Action:** Message deleted & 1-hour timeout applied.\n**Violation:** Attempted unauthorized `@everyone` / `@here` ping.",
                color=0xFF4B4B
            )
            await log_ch.send(embed=embed)
        return

    # 2. ANTI-MASS MENTION (> 3 mentions)
    if not is_owner and len(message.mentions) > 3:
        try:
            await message.delete()
        except Exception:
            pass
        try:
            await author.timeout(datetime.timedelta(minutes=15), reason="Anti-Abuse: Mass mention spam")
        except Exception:
            pass

        log_ch = discord.utils.get(guild.text_channels, name="╰・📊・server-logs")
        if log_ch:
            embed = discord.Embed(
                title="🛡️ ∙ Anti-Abuse: Mass Mention Spam Blocked",
                description=f"**User:** {author.mention} (`{author.name}`)\n**Channel:** {message.channel.mention}\n**Mentions Count:** `{len(message.mentions)}`\n**Action:** Message deleted & 15-minute timeout applied.",
                color=0xFF4B4B
            )
            await log_ch.send(embed=embed)
        return

    # 3. ANTI-MESSAGE FLOODING (5 messages in 3 seconds)
    if not is_owner:
        now = datetime.datetime.now(datetime.timezone.utc).timestamp()
        times = user_msg_times[author.id]
        times = [t for t in times if now - t < 3.0]
        times.append(now)
        user_msg_times[author.id] = times

        if len(times) >= 5:
            try:
                await message.delete()
            except Exception:
                pass
            try:
                await author.timeout(datetime.timedelta(minutes=5), reason="Anti-Abuse: Rapid message flooding")
            except Exception:
                pass
            log_ch = discord.utils.get(guild.text_channels, name="╰・📊・server-logs")
            if log_ch:
                embed = discord.Embed(
                    title="🛡️ ∙ Anti-Abuse: Rapid Message Flooding Blocked",
                    description=f"**User:** {author.mention} (`{author.name}`)\n**Channel:** {message.channel.mention}\n**Action:** Message deleted & 5-minute timeout applied.\n**Violation:** Sent 5+ messages in under 3 seconds.",
                    color=0xFF9900
                )
                await log_ch.send(embed=embed)
            return

    # 4. ANTI-BAD WORDS / PROFANITY FILTER (Islamic Adab)
    if not is_owner and check_profanity(message.content):
        try:
            await message.delete()
        except Exception:
            pass
        try:
            await author.send(
                "السَّلَامُ عَلَيْكُمْ.\n"
                "Your message in **The Grand Majlis** was removed for containing inappropriate or vulgar language.\n"
                "Please preserve Islamic character (*Adab*) and clean speech in our community sanctuary. 🕊️"
            )
        except Exception:
            pass

        log_ch = discord.utils.get(guild.text_channels, name="╰・📊・server-logs")
        if log_ch:
            embed = discord.Embed(
                title="🕊️ ∙ Islamic Adab Filter: Inappropriate Language Removed",
                description=(
                    f"**User:** {author.mention} (`{author.name}`)\n"
                    f"**Channel:** {message.channel.mention}\n"
                    f"**Action:** Message deleted automatically.\n"
                    f"**Adab Standard:** Zero tolerance for profanity, vulgarity, or offensive words."
                ),
                color=0xFF9900
            )
            await log_ch.send(embed=embed)
        return

    # 5. ANTI-BAD LINKS & UNAUTHORIZED INVITES
    if not is_owner:
        has_invite = bool(INVITE_REGEX.search(message.content))
        has_suspicious = bool(SUSPICIOUS_LINKS.search(message.content))
        
        if has_invite or has_suspicious:
            try:
                await message.delete()
            except Exception:
                pass
            
            reason_str = "Unauthorized Discord Invite Link" if has_invite else "Suspicious / Phishing URL"
            try:
                await author.send(
                    f"⚠️ Your link in **The Grand Majlis** was removed ({reason_str}).\n"
                    "Server advertising, invite links, and untrusted URLs are strictly forbidden."
                )
            except Exception:
                pass

            log_ch = discord.utils.get(guild.text_channels, name="╰・📊・server-logs")
            if log_ch:
                embed = discord.Embed(
                    title=f"🛡️ ∙ Anti-Abuse: {reason_str} Blocked",
                    description=(
                        f"**User:** {author.mention} (`{author.name}`)\n"
                        f"**Channel:** {message.channel.mention}\n"
                        f"**Action:** Link deleted automatically.\n"
                        f"**Protection:** Server link safety & anti-raid protocol."
                    ),
                    color=0xFF4B4B
                )
                await log_ch.send(embed=embed)
            return

    # 6. READ-ONLY CHANNEL PROTECTION (Prevent typing in protected channels)
    ch_name_lower = message.channel.name.lower()
    is_protected_channel = any(k in ch_name_lower for k in READONLY_CHANNEL_KEYWORDS) or (message.channel.id == VERIFY_CHANNEL_ID)
    perms = author.guild_permissions
    is_staff = perms.manage_channels or perms.manage_roles or perms.administrator or is_owner

    if is_protected_channel and not is_staff:
        try:
            await message.delete()
        except Exception:
            pass
        try:
            await message.channel.send(
                f"⚠️ {author.mention}, this channel is **read-only**. Please chat in <#{GENERAL_CHANNEL_ID}>! 🤍",
                delete_after=5
            )
        except Exception:
            pass
        return

    # 7. TEXT ACTIVITY LEVELING XP
    if not message.content.startswith("!"):
        now_ts = datetime.datetime.now(datetime.timezone.utc).timestamp()
        stats = get_user_stats(author.id)

        # 60-second cooldown per user
        if now_ts - stats.get("last_text_xp", 0) >= 60.0:
            import random
            gained_xp = random.randint(15, 25)
            old_lvl = stats["text_level"]
            stats["text_xp"] += gained_xp
            stats["messages"] += 1
            stats["last_text_xp"] = now_ts
            new_lvl = level_from_xp(stats["text_xp"])
            stats["text_level"] = new_lvl
            save_levels()

            if new_lvl > old_lvl:
                try:
                    await announce_level_up(author, "text", new_lvl, stats["text_xp"])
                except Exception as e:
                    print(f"Error announcing text level up: {e}")
        else:
            stats["messages"] += 1
            save_levels()

    # Always process bot commands
    await bot.process_commands(message)

@bot.command(name="setuproles")
@commands.has_permissions(administrator=True)
async def cmd_setuproles(ctx):
    """Publish or refresh the verification dashboard in #verify-and-roles."""
    await publish_verification_dashboard(ctx.guild, force=True)
    await ctx.send("✅ Verification dashboard updated!")

@bot.command(name="testwelcome")
@commands.has_permissions(manage_messages=True)
async def cmd_testwelcome(ctx):
    """Preview the welcome message for testing."""
    general_ch = ctx.guild.get_channel(GENERAL_CHANNEL_ID)
    if general_ch:
        welcome_msg = build_welcome_text(ctx.author)
        await general_ch.send(welcome_msg)
        await ctx.send("✅ Sent welcome preview to general-lounge!")

@bot.command(name="daily")
@commands.has_permissions(manage_messages=True)
async def cmd_daily(ctx):
    """Trigger today's post manually."""
    await ctx.send("🕊️ *Publishing authentic classical daily reminder...*")
    await post_daily_if_due(force=True)

@bot.command(name="quran")
async def cmd_quran(ctx, surah: int = 1, ayah: int = 1):
    """Lookup any authentic verse directly from Tanzil.net dataset."""
    if not (1 <= surah <= 114):
        await ctx.send("Surah number must be between 1 and 114.")
        return
    s_idx = surah - 1
    total_ayahs = len(db["quran_ar"][s_idx]["ayahs"])
    if not (1 <= ayah <= total_ayahs):
        await ctx.send(f"Surah {surah} has {total_ayahs} verses. Please choose between 1 and {total_ayahs}.")
        return

    a_idx = ayah - 1
    s_ar = db["quran_ar"][s_idx]["name"]
    s_en = db["quran_en"][s_idx]["englishName"]
    txt_ar = db["quran_ar"][s_idx]["ayahs"][a_idx]["text"]
    txt_en = db["quran_en"][s_idx]["ayahs"][a_idx]["text"]

    embed = discord.Embed(
        title=f"📖 ∙ {s_en} ({s_ar}) [{surah}:{ayah}]",
        description=f"### {txt_ar}\n\n> *\"{txt_en}\"*\n\n**Source:** Tanzil.net (Uthmani) & Saheeh International",
        color=0xFDFCFA
    )
    await ctx.send(embed=embed)

@bot.command(name="hadith")
async def cmd_hadith(ctx, number: int = 1):
    """Lookup any of the 40 Hadith of Imam an-Nawawi (1 to 42)."""
    if not (1 <= number <= len(db["nawawi_ar"])):
        await ctx.send(f"Hadith number must be between 1 and {len(db['nawawi_ar'])}.")
        return
    idx = number - 1
    h_en = db["nawawi_en"][idx]["text"]

    embed = discord.Embed(
        title=f"📜 ∙ Al-Arba'in an-Nawawiyyah (Hadith #{number})",
        description=f"> *\"{h_en[:800]}{'...' if len(h_en) > 800 else ''}\"*\n\n**Grading:** Sahih — Imam an-Nawawi (d. 676 AH)",
        color=0xF5F5F7
    )
    await ctx.send(embed=embed)

@bot.command(name="status")
async def cmd_status(ctx):
    """Check bot status, member count, and database stats."""
    tracker = load_tracker()
    vc = next((c for c in ctx.guild.voice_channels if "Members:" in c.name), None)
    counter_name = vc.name if vc else "Not found"

    embed = discord.Embed(
        title="🏛️ ∙ Grand Majlis Bot Status",
        description=(
            f"**Bot Name:** `{bot.user.name}`\n"
            f"**Status:** 🟢 Online 24/7\n"
            f"**Total Server Members:** `{ctx.guild.member_count}`\n"
            f"**Voice Counter Channel:** `{counter_name}`\n"
            f"**Auto-Role Active:** `🤍 ∙ Mu'min (Verified)`\n"
            f"**Welcome Channel:** <#{GENERAL_CHANNEL_ID}>\n"
            f"**Last Daily Reminder:** `{tracker.get('last_posted_date', 'None')}`\n"
            f"**AI Generation:** 0% (Strictly Classical Human Scholarship)"
        ),
        color=0xFFFFFF
    )
    await ctx.send(embed=embed)

@bot.command(name="skip", aliases=["next"])
async def cmd_skip(ctx):
    """Skip to the next beautiful Quran recitation in the voice channel."""
    if ctx.guild.voice_client and ctx.guild.voice_client.is_connected():
        await ctx.send("⏭️ *Skipping to the next beautiful recitation...*")
        await play_next_recitation(ctx.guild)
    else:
        await ctx.send("The bot is not currently in the voice channel.")

@bot.command(name="nowplaying", aliases=["np"])
async def cmd_nowplaying(ctx):
    """View the currently playing Surah and reciter in the voice channel."""
    title = current_recitation.get("title", "Continuous Quran Recitation")
    reciter = current_recitation.get("reciter", "World Renowned Qaris")
    surah_num = current_recitation.get("surah_num")

    desc = f"**Currently Reciting:** `{title}`\n**Qari:** `{reciter}`\n\n🕊️ *Live 24/7 in <#1548478297996787756>*"
    if surah_num and db and "quran_ar" in db and surah_num <= len(db["quran_ar"]):
        ar_name = db["quran_ar"][surah_num - 1]["name"]
        desc = f"### {ar_name}\n**Currently Reciting:** `{title}`\n**Qari:** `{reciter}`\n\n🕊️ *Live 24/7 in <#1548478297996787756>*"

    embed = discord.Embed(
        title="🎙️ ∙ Live Quran Recitation Stream",
        description=desc,
        color=0xFFFFFF
    )
    embed.set_footer(text="The Grand Majlis ∙ Preserving the Sacred Word 🤍")
    await ctx.send(embed=embed)

@bot.command(name="radio")
async def cmd_radio(ctx):
    """Toggle between rotating Surahs and 24/7 live continuous Tarateel radio."""
    global is_radio_mode
    is_radio_mode = not is_radio_mode
    mode_str = "24/7 Live Tarateel Radio" if is_radio_mode else "Rotating Surahs & Iconic Qaris"
    await ctx.send(f"📻 Switched Quran recitation mode to: **{mode_str}**")
    if ctx.guild.voice_client and ctx.guild.voice_client.is_connected():
        await play_next_recitation(ctx.guild)

@bot.command(name="qarni")
async def cmd_qarni(ctx):
    """Switch recitation exclusively to Sheikh Abdullah Al-Qarni (54 Surahs)."""
    global selected_reciter_mode, is_radio_mode
    selected_reciter_mode = "qarni"
    is_radio_mode = False
    await ctx.send("🎙️ Quran voice stream set exclusively to: **Sheikh Abdullah Al-Qarni** (54 Surahs rotation) 🕊️")
    if ctx.guild.voice_client and ctx.guild.voice_client.is_connected():
        await play_next_recitation(ctx.guild)

@bot.command(name="reciter")
async def cmd_reciter(ctx, *, name: str = None):
    """View or change the active reciter (e.g. !reciter qarni, !reciter rotate)."""
    global selected_reciter_mode, is_radio_mode
    if not name:
        mode_desc = "Sheikh Abdullah Al-Qarni (54 Surahs)" if selected_reciter_mode == "qarni" else "Rotating All 10+ Iconic Qaris"
        embed = discord.Embed(
            title="🎙️ ∙ Quran Reciters Settings",
            description=(
                f"**Current Active Mode:** `{mode_desc}`\n\n"
                f"**Available Commands:**\n"
                f"• `!reciter qarni` or `!qarni` — Sheikh Abdullah Al-Qarni (54 Surahs)\n"
                f"• `!reciter rotate` / `!reciter all` — Rotates across 10+ Iconic Qaris\n"
                f"• `!radio` — 24/7 Live Tarateel Radio\n"
                f"• `!skip` — Skip to next Surah\n"
                f"• `!np` — View currently reciting Surah & Qari"
            ),
            color=0xFFFFFF
        )
        await ctx.send(embed=embed)
        return

    name_lower = name.lower().strip()
    if "qarni" in name_lower or "abdullah" in name_lower:
        selected_reciter_mode = "qarni"
        is_radio_mode = False
        await ctx.send("🎙️ Quran voice stream set to: **Sheikh Abdullah Al-Qarni** (54 Surahs) 🕊️")
    elif "rotate" in name_lower or "all" in name_lower:
        selected_reciter_mode = "rotate"
        is_radio_mode = False
        await ctx.send("🎙️ Quran voice stream set to: **Rotating All Iconic Qaris** 🕊️")
    else:
        await ctx.send(f"Unknown mode `{name}`. Available options: `!reciter qarni` or `!reciter rotate`.")

    if ctx.guild.voice_client and ctx.guild.voice_client.is_connected():
        await play_next_recitation(ctx.guild)

@bot.command(name="close")
async def cmd_close(ctx):
    """Close and delete the current ticket channel."""
    is_ticket = ctx.channel.name.startswith("verify-") or "ticket" in (ctx.channel.category.name.lower() if ctx.channel.category else "")
    if not is_ticket:
        await ctx.send("❌ This command can only be used inside a verification ticket channel.")
        return

    perms = ctx.author.guild_permissions
    is_mod = perms.manage_channels or perms.manage_roles or perms.administrator
    is_owner = ctx.channel.topic and f"user_id:{ctx.author.id}" in ctx.channel.topic

    if not (is_mod or is_owner):
        await ctx.send("❌ You do not have permission to close this ticket.")
        return

    await ctx.send(f"🔒 **Ticket closing by {ctx.author.mention}...**")
    await asyncio.sleep(2)
    try:
        await ctx.channel.delete()
    except Exception as e:
        print(f"Error deleting ticket via !close: {e}")

@bot.command(name="rank", aliases=["level", "xp"])
async def cmd_rank(ctx, target: discord.Member = None):
    """View your or another member's Text & Voice levels, XP, and milestone ranks."""
    member = target or ctx.author
    stats = get_user_stats(member.id)

    t_xp = stats.get("text_xp", 0)
    t_lvl = stats.get("text_level", 0)
    t_bar = get_progress_bar(t_xp, t_lvl)
    t_next = xp_required_for_level(t_lvl + 1)

    v_xp = stats.get("voice_xp", 0)
    v_lvl = stats.get("voice_level", 0)
    v_bar = get_progress_bar(v_xp, v_lvl)
    v_next = xp_required_for_level(v_lvl + 1)

    member_roles = [r.name for r in member.roles]
    t_milestones = [r[1] for r in TEXT_LEVEL_ROLES if r[1] in member_roles]
    v_milestones = [r[1] for r in VOICE_LEVEL_ROLES if r[1] in member_roles]

    t_badge = t_milestones[-1] if t_milestones else "None yet"
    v_badge = v_milestones[-1] if v_milestones else "None yet"

    embed = discord.Embed(
        title=f"📊 ∙ Majlis Progression: {member.display_name}",
        description=(
            f"### 💬 ∙ Text Activity (Chatting)\n"
            f"• **Level:** `{t_lvl}` | **XP:** `{t_xp:,} / {t_next:,}`\n"
            f"• **Progress:** `{t_bar}`\n"
            f"• **Messages Sent:** `{stats.get('messages', 0):,}`\n"
            f"• **Milestone Role:** `{t_badge}`\n\n"
            f"### 🎙️ ∙ Voice Activity (VC & Halaqah)\n"
            f"• **Level:** `{v_lvl}` | **XP:** `{v_xp:,} / {v_next:,}`\n"
            f"• **Progress:** `{v_bar}`\n"
            f"• **Time in VC:** `{stats.get('voice_minutes', 0):,} mins`\n"
            f"• **Milestone Role:** `{v_badge}`\n"
        ),
        color=0xFFFFFF
    )
    if member.display_avatar:
        embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="The Grand Majlis ∙ Rewarding Dedication & Beneficial Knowledge 🤍")
    await ctx.send(embed=embed)

@bot.command(name="leaderboard", aliases=["top", "levels", "ranks"])
async def cmd_leaderboard(ctx):
    """View the top members in Text Activity and Voice Activity."""
    levels = load_levels()
    if not levels:
        await ctx.send("No activity recorded yet. Start chatting or join VC!")
        return

    top_text = sorted(levels.items(), key=lambda x: x[1].get("text_xp", 0), reverse=True)[:10]
    top_voice = sorted(levels.items(), key=lambda x: x[1].get("voice_xp", 0), reverse=True)[:10]

    text_lines = []
    for rank, (uid, data) in enumerate(top_text, start=1):
        m = ctx.guild.get_member(int(uid))
        name = m.display_name if m else f"Member {uid[:6]}"
        text_lines.append(f"`#{rank:02d}` **{name}** — Lvl `{data.get('text_level', 0)}` ({data.get('text_xp', 0):,} XP)")

    voice_lines = []
    for rank, (uid, data) in enumerate(top_voice, start=1):
        m = ctx.guild.get_member(int(uid))
        name = m.display_name if m else f"Member {uid[:6]}"
        voice_lines.append(f"`#{rank:02d}` **{name}** — Lvl `{data.get('voice_level', 0)}` ({data.get('voice_xp', 0):,} XP)")

    embed = discord.Embed(
        title="🏆 ∙ The Grand Majlis Leaderboard",
        description=(
            "### 💬 ∙ Top Chatters (Text Activity)\n" +
            ("\n".join(text_lines) if text_lines else "No records yet.") +
            "\n\n" +
            "### 🎙️ ∙ Top Companions (Voice Activity)\n" +
            ("\n".join(voice_lines) if voice_lines else "No records yet.")
        ),
        color=0xFFFFFF
    )
    embed.set_footer(text="The Grand Majlis ∙ Strive together in righteousness and piety 🤍")
    await ctx.send(embed=embed)

@bot.command(name="lockchannels")
@commands.has_permissions(administrator=True)
async def cmd_lockchannels(ctx):
    """Audit and enforce read-only lockdown on all protected channels."""
    msg = await ctx.send("🔒 Enforcing channel permissions lockdown...")
    await enforce_channel_lockdowns(ctx.guild)
    await msg.edit(content="✅ All protected channels have been strictly locked to read-only for members!")

async def start_web_server():
    """Starts a lightweight HTTP server for Render / cloud health checks when PORT is set."""
    port_str = os.environ.get("PORT")
    if not port_str:
        return
    try:
        port = int(port_str)
    except ValueError:
        port = 10000

    from aiohttp import web

    async def handle_ping(request):
        return web.Response(
            text="🕊️ The Grand Majlis Bot is active and running 24/7 on Render.",
            content_type="text/plain",
            status=200
        )

    async def handle_voice_diagnostics(request):
        """Returns detailed voice diagnostics JSON without needing to log in with the token."""
        import json as _json
        diag = {}

        # 1. Opus
        diag["opus_loaded"] = discord.opus.is_loaded()
        opus_path = os.path.join(BASE_DIR, "libopus.so.0")
        diag["opus_file_exists"] = os.path.exists(opus_path)
        diag["opus_file_size"] = os.path.getsize(opus_path) if os.path.exists(opus_path) else 0

        # 2. FFmpeg
        try:
            ffmpeg_exe = get_ffmpeg_path()
            diag["ffmpeg_path"] = ffmpeg_exe
            diag["ffmpeg_exists"] = os.path.exists(ffmpeg_exe) if ffmpeg_exe != "ffmpeg" else "system"
        except Exception as e:
            diag["ffmpeg_path"] = None
            diag["ffmpeg_error"] = str(e)

        # 3. Bot state
        diag["bot_ready"] = bot.is_ready()
        diag["bot_user"] = str(bot.user) if bot.user else None
        diag["bot_latency_ms"] = round(bot.latency * 1000, 1) if bot.latency else None

        # 4. Guild & Voice
        guild = bot.get_guild(GUILD_ID) if bot.is_ready() else None
        diag["guild_found"] = guild is not None
        if guild:
            vc = guild.voice_client
            diag["voice_client_exists"] = vc is not None
            if vc:
                diag["voice_connected"] = vc.is_connected()
                diag["voice_playing"] = vc.is_playing()
                diag["voice_paused"] = vc.is_paused()
                diag["voice_channel"] = str(vc.channel) if vc.channel else None
                diag["voice_channel_id"] = vc.channel.id if vc.channel else None
            else:
                diag["voice_connected"] = False
                diag["voice_playing"] = False

        # 5. Current recitation
        diag["current_recitation"] = current_recitation
        diag["playlist_index"] = playlist_index
        diag["is_radio_mode"] = is_radio_mode
        diag["selected_reciter_mode"] = selected_reciter_mode
        diag["qarni_tracks_count"] = len(QARNI_TRACKS)
        diag["play_lock_held"] = _play_lock.locked()

        # 6. Task loop status
        diag["ensure_quran_vc_loop_running"] = ensure_quran_vc_stream.is_running()
        diag["daily_schedule_loop_running"] = check_daily_schedule.is_running()

        # 7. FFmpeg probe test — can it actually reach and decode an audio URL?
        test_url = "https://server8.mp3quran.net/afs/001.mp3"
        try:
            import subprocess
            ffmpeg_exe = get_ffmpeg_path()
            result = subprocess.run(
                [ffmpeg_exe, "-i", test_url, "-t", "1", "-f", "null", "-"],
                capture_output=True, text=True, timeout=10
            )
            diag["ffmpeg_probe_test"] = {
                "url": test_url,
                "returncode": result.returncode,
                "stderr_tail": result.stderr[-500:] if result.stderr else "",
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            diag["ffmpeg_probe_test"] = {"url": test_url, "error": "TIMEOUT after 10s"}
        except Exception as probe_err:
            diag["ffmpeg_probe_test"] = {"url": test_url, "error": str(probe_err)}

        # 8. HTTP fetch test — can aiohttp reach the audio server?
        try:
            import aiohttp as _aiohttp
            async with _aiohttp.ClientSession() as sess:
                async with sess.head(test_url, timeout=_aiohttp.ClientTimeout(total=5)) as resp:
                    diag["http_fetch_test"] = {
                        "url": test_url,
                        "status": resp.status,
                        "content_type": resp.headers.get("Content-Type", ""),
                        "content_length": resp.headers.get("Content-Length", "")
                    }
        except Exception as fetch_err:
            diag["http_fetch_test"] = {"url": test_url, "error": str(fetch_err)}

        return web.Response(
            text=_json.dumps(diag, indent=2, ensure_ascii=False, default=str),
            content_type="application/json",
            status=200
        )

    async def handle_logs(request):
        """Returns the recent stdout/stderr log output."""
        try:
            content = "".join(str(x) for x in list(RECENT_LOGS))
            return web.Response(
                text=content if content else "No logs recorded yet.",
                content_type="text/plain",
                charset="utf-8",
                status=200
            )
        except Exception as err:
            return web.Response(text=f"Log read error: {err}", status=200)

    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)
    app.router.add_get("/logs", handle_logs)
    app.router.add_get("/voice-diagnostics", handle_voice_diagnostics)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Cloud HTTP health server listening on port {port}!")

# Main runner with resilient auto-reconnect
async def main():
    # Start web server if PORT is defined (e.g. Render Web Service)
    await start_web_server()

    while True:
        try:
            await bot.start(TOKEN)
        except (discord.ConnectionClosed, discord.GatewayNotFound, asyncio.TimeoutError) as e:
            print(f"Connection lost ({e}). Reconnecting in 10 seconds...")
            await asyncio.sleep(10)
        except Exception as e:
            print(f"Fatal error in bot loop: {e}")
            traceback.print_exc()
            await asyncio.sleep(15)

if __name__ == "__main__":
    asyncio.run(main())
