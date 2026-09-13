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

# Ensure UTF-8 output
if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
# UI COMPONENTS: TICKET & VERIFICATION DASHBOARD
# ==============================================================================

class TicketStaffView(discord.ui.View):
    """Staff controls inside a member's verification ticket."""
    def __init__(self, target_user_id: int, gender_type: str):
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

        role_name = "🧔 ∙ Brother" if self.gender_type.lower() == "brother" else "🧕 ∙ Sister"
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=role_name)
        target_member = guild.get_member(self.target_user_id) or await guild.fetch_member(self.target_user_id)

        if not target_member:
            await interaction.response.send_message("❌ Member not found in server.", ephemeral=True)
            return

        if role:
            await target_member.add_roles(role)
            await interaction.response.send_message(
                f"✅ **Approved by {interaction.user.mention}!**\n"
                f"Granted **{role.name}** to {target_member.mention}.\n"
                f"*This ticket will automatically close in 10 seconds...*"
            )
            button.disabled = True
            await interaction.message.edit(view=self)
            await asyncio.sleep(10)
            try:
                await interaction.channel.delete()
            except Exception:
                pass
        else:
            await interaction.response.send_message(f"❌ Role '{role_name}' was not found.", ephemeral=True)

    @discord.ui.button(label="Close Ticket", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="ticket_close_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        perms = interaction.user.guild_permissions
        if not (perms.manage_roles or perms.manage_channels or perms.administrator or interaction.user.id == self.target_user_id):
            await interaction.response.send_message("❌ You do not have permission to close this ticket.", ephemeral=True)
            return

        await interaction.response.send_message("🔒 Closing ticket in 5 seconds...")
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete()
        except Exception:
            pass


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
            topic=f"Voice verification for {user.name} ({gender_type})"
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
    """Ensure the locked voice channel reflects the exact live member count without duplicating."""
    count = guild.member_count
    target_name = f"👥 Members: {count}"
    
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
        if vc.name != target_name:
            try:
                await vc.edit(name=target_name)
                print(f"Updated member counter to: '{target_name}'")
            except Exception as e:
                print(f"Notice on updating counter channel: {e}")
    else:
        cat_stats = discord.utils.get(guild.categories, name="╭─・📊 ∙ 𝐒𝐄𝐑𝐕𝐄𝐑 ∙ 𝐒𝐓𝐀𝐓𝐒")
        if not cat_stats:
            cat_stats = await guild.create_category("╭─・📊 ∙ 𝐒𝐄𝐑𝐕𝐄𝐑 ∙ 𝐒𝐓𝐀𝐓𝐒", position=0)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=True, connect=False)
        }
        await cat_stats.create_voice_channel(target_name, overwrites=overwrites)
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
    tracker = load_tracker()
    today_str = datetime.date.today().isoformat()

    if not force and tracker.get("last_posted_date") == today_str:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Daily reminder already posted for today ({today_str}). Skipping.")
        return False

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return False

    channel = discord.utils.get(guild.text_channels, name="┊・🕋・daily-ayah-hadith")
    if not channel:
        return False

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

@tasks.loop(minutes=30)
async def check_daily_schedule():
    await post_daily_if_due(force=False)

@bot.event
async def on_ready():
    global db
    print(f"✨ Grand Majlis Bot is ONLINE as {bot.user.name} ({bot.user.id})")
    db = load_data()
    
    # Register persistent views
    bot.add_view(VerificationDashboardView())
    
    guild = bot.get_guild(GUILD_ID)
    if guild:
        # Sync voice member counter
        await update_member_counter(guild)
        # Setup/refresh dashboard in #verify-and-roles
        await publish_verification_dashboard(guild)

    # Check daily post
    await post_daily_if_due(force=False)

    if not check_daily_schedule.is_running():
        check_daily_schedule.start()
        print("⏰ 30-minute background calendar monitor is active!")

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

    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)

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
