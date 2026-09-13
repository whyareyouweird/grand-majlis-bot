# 🤍 Roles & Permissions Matrix
## White-Themed Aesthetic Hierarchy for Khafos's Server

This guide contains the exact role structure, color hex codes (clean white/ivory/pearl palette), hoist settings, and Discord permission checkboxes.

---

### 🎨 Color Palette & Hierarchy (Top to Bottom)

In Discord, drag roles so that **Khafos** is at the absolute top, followed by staff, knowledge seekers, supporters, and verified members.

| Role Name | Hex Code | Visual Tone | Hoisted (Separated) | Key Responsibilities / Perks |
| :--- | :--- | :--- | :---: | :--- |
| **👑 ∙ Khafos** | `#FFFFFF` | Pure Diamond White | **YES** | Server Owner / Administrator. Full access. |
| **📜 ∙ Shuyookh & Advisors** | `#FDFCFA` | Warm Ivory | **YES** | Senior scholars or advisors; priority voice speaker, manage messages. |
| **🛡️ ∙ Muhtasib (Moderators)** | `#EEEEEE` | Clean Alabaster | **YES** | Full moderation (kick, ban, timeout, manage messages, audit log). |
| **🕊️ ∙ Talib al-'Ilm** | `#F5F5F7` | Pearl White | **YES** | Students of Knowledge; write access in library/daily reminders, manage threads. |
| **⭐ ∙ Khafos Patron** | `#E6E6EB` | Mist Silver | **YES** | VIP fans / Nitro Boosters; external emojis/stickers, soundboard, embed links. |
| **🤍 ∙ Mu'min (Verified)** | `#D7DAE0` | Soft Slate White | **YES** | Regular member who passed verification/rules; access to chat & voice. |
| **🧔 ∙ Brother** | `#EBF0FA` | Ice Alabaster | NO | Access to private `╭─・🌿 ∙ 𝐁𝐑𝐎𝐓𝐇𝐄𝐑𝐒 ∙ 𝐒𝐏𝐀𝐂𝐄`. |
| **🧕 ∙ Sister** | `#FAEEF5` | Rose Pearl | NO | Access to private `╭─・🌸 ∙ 𝐒𝐈𝐒𝐓𝐄𝐑𝐒 ∙ 𝐒𝐏𝐀𝐂𝐄`. |
| **📢 ∙ Khafos Announcements** | `#C8CCD2` | Muted Platinum | NO | Pinged when Khafos uploads or makes an official announcement. |
| **📖 ∙ Daily Ayah & Hadith** | `#C8CCD2` | Muted Platinum | NO | Pinged for morning/evening Quranic & Hadith posts. |
| **🎙️ ∙ Live Halaqah & Stage** | `#C8CCD2` | Muted Platinum | NO | Pinged when live sessions or stages begin. |
| **@everyone** | `Default` | Dark/Gray | NO | Base role: CANNOT speak or send messages anywhere until verified. |

---

## 🔒 Exact Permissions Matrix

### 1. `@everyone` (Unverified / Default)
*Keep this strictly locked down to prevent raids, spam bots, and unverified users.*
* ✅ **View Channels** (Only on Information category: `#welcome`, `#rules-and-adab`, `#verify-and-roles`)
* ✅ **Read Message History**
* ❌ **Send Messages** (Disabled across entire server)
* ❌ **Send Messages in Threads**
* ❌ **Create Public / Private Threads**
* ❌ **Embed Links**
* ❌ **Attach Files**
* ❌ **Add Reactions**
* ❌ **Mention @everyone, @here, and All Roles**
* ❌ **Connect / Speak in Voice Channels**
* ❌ **Use External Emojis / Stickers**

---

### 2. `🤍 ∙ Mu'min (Verified Member)`
*Granted automatically via Discord Onboarding / Reaction Role after accepting rules.*
* ✅ **View Channels** (All standard community & educational channels)
* ✅ **Send Messages**
* ✅ **Read Message History**
* ✅ **Add Reactions**
* ✅ **Connect & Speak in Voice Channels**
* ✅ **Use Application Commands** (Slash commands like `/quran`)
* ❌ **Embed Links** (Can be turned off in educational channels to avoid spam)
* ❌ **Attach Files** (Restricted to creative/art channel only)
* ❌ **Mention @everyone / @here** (Never enable for members)
* ❌ **Manage Messages / Manage Threads**

---

### 3. `🕊️ ∙ Talib al-'Ilm (Student of Knowledge)`
*Trusted individuals who share authentic reminders and answer questions.*
* ✅ All **Verified Member** permissions, plus:
* ✅ **Embed Links & Attach Files** everywhere
* ✅ **Manage Threads** (Can close or archive answered question threads)
* ✅ **Pin Messages** (Highlight important educational points or references)
* ✅ **Priority Speaker** in voice channels

---

### 4. `🛡️ ∙ Muhtasib (Moderator)`
*Guardians of the server adab and safety.*
* ✅ **Kick Members**
* ✅ **Ban Members**
* ✅ **Moderate Members** (Timeout / Mute toxic users up to 28 days)
* ✅ **Manage Messages** (Delete inappropriate content, offensive speech)
* ✅ **View Audit Log**
* ✅ **Manage Nicknames**
* ✅ **Move Members** in Voice Channels
* ✅ **Mute / Deafen Members** in Voice Channels
* ❌ **Administrator** (Only Khafos has Administrator to protect the server)

---

### 5. `👑 ∙ Khafos (Owner)`
* ✅ **Administrator** (All permissions automatically granted)

---

## 🛡️ Category Permission Overwrite Matrix

To ensure clean channel management in Discord without manually configuring 30 channels, set permissions at the **Category level** and sync channels:

### Category: `╭─・🕊️ ∙ 𝐈𝐍𝐅𝐎𝐑𝐌𝐀𝐓𝐈𝐎𝐍`
* `@everyone`: View Channel: **ON** | Send Messages: **OFF** | Add Reactions: **OFF**
* `🤍 Mu'min`: View Channel: **ON** | Send Messages: **OFF** | Add Reactions: **ON** (for verification)
* `🛡️ Muhtasib` & `👑 Khafos`: View Channel: **ON** | Send Messages: **ON**

### Category: `╭─・📖 ∙ 𝐓𝐀'𝐋𝐄𝐄𝐌 ∙ 𝐄𝐃𝐔𝐂𝐀𝐓𝐈𝐎𝐍`
* `@everyone`: View Channel: **OFF**
* `🤍 Mu'min`: View Channel: **ON** | Send Messages: **ON** | Attach Files: **OFF**
* `🕊️ Talib al-'Ilm`: View Channel: **ON** | Send Messages: **ON** | Attach Files: **ON** | Manage Threads: **ON**

### Category: `╭─・🌿 ∙ 𝐁𝐑𝐎𝐓𝐇𝐄𝐑𝐒 ∙ 𝐒𝐏𝐀𝐂𝐄`
* `@everyone`: View Channel: **OFF**
* `🧔 Brother`: View Channel: **ON** | Send Messages: **ON** | Connect/Speak: **ON**

### Category: `╭─・🌸 ∙ 𝐒𝐈𝐒𝐓𝐄𝐑𝐒 ∙ 𝐒𝐏𝐀𝐂𝐄`
* `@everyone`: View Channel: **OFF**
* `🧕 Sister`: View Channel: **ON** | Send Messages: **ON** | Connect/Speak: **ON**

### Category: `╭─・🛠️ ∙ 𝐒𝐓𝐀𝐅𝐅 ∙ 𝐎𝐅𝐅𝐈𝐂𝐄`
* `@everyone`: View Channel: **OFF**
* `🤍 Mu'min`: View Channel: **OFF**
* `🛡️ Muhtasib` & `👑 Khafos`: View Channel: **ON** | Send Messages: **ON**
