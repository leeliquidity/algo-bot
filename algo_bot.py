#!/usr/bin/env python3
"""
ALGO - Algorithm Arbitrage community manager bot.

Modules:
  1. ONBOARDING   - private thread per new member; niche -> platforms/handles ->
                    audience -> goal -> experience; assigns niche role; logs to
                    Supabase 'creators'; 24h check-back. (PRE-LAUNCH: no deal link.)
  2. Q&A          - when @mentioned, answers from a built-in knowledge base.
  3. MODERATION   - light: flags likely spam/scams to staff, never auto-deletes.
  4. SUPPORT      - answers questions posted in the support channel.
  5. DAILY POST   - once a day, posts the active deal + a leaderboard pulled from
                    Supabase 'sales'. OFF until DAILY_POST_ENABLED=true.
  Escalation: anything ALGO can't answer -> private ping to staff (if a staff
              channel is configured; otherwise silently skipped).

RUNS 24/7. Host on Replit / Railway / a machine that stays on.
See SETUP.md for the full runbook.
"""

import os
import re
import json
import asyncio
import functools
import requests
import discord
from discord.ext import tasks
from openai import OpenAI  # used for Groq (OpenAI-compatible API)

# Load .env if present (local runs). On Replit, Secrets are real env vars, so
# this is a harmless no-op there. Safe if python-dotenv isn't installed.
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# This machine's Python can't verify TLS with the bundled CA store; use the OS
# trust store if available (harmless elsewhere, including Replit).
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

# ---------------- CONFIG ----------------
def _int_env(name):
    """Channel/guild IDs: return 0 if missing/blank instead of crashing.
    A feature whose channel ID is 0 is simply skipped until it's filled in."""
    v = (os.environ.get(name) or "").strip()
    return int(v) if v.isdigit() else 0


DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
GUILD_ID = _int_env("GUILD_ID")
ONBOARD_CHANNEL_ID = _int_env("ONBOARD_CHANNEL_ID")
SUPPORT_CHANNEL_ID = _int_env("SUPPORT_CHANNEL_ID")
STAFF_CHANNEL_ID = _int_env("STAFF_CHANNEL_ID")
DEALS_CHANNEL_ID = _int_env("DEALS_CHANNEL_ID")
SB_LINK = os.environ.get("SB_LINK") or "[SuperBonsai signup link]"
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
# Groq runs Llama via an OpenAI-compatible API. Cheap + fast.
MODEL = os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile")

NICHE_ROLES = ["Health", "Beauty", "Personal", "Fitness", "Business"]
ENTRY_ROLE = "Copper"
STAFF_ROLES = {"Junior Admin", "Community Manager", "Brand Success"}
NUDGE_AFTER = 24 * 3600

llm = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
)

# ---------------- KNOWLEDGE BASE ----------------
KB = """ALGORITHM ARBITRAGE AFFILIATE NETWORK - what ALGO knows:

WHAT IT IS: A free Discord where creators get paid to post content promoting real brands. Free to join, free to promote, free forever. We make money when creators make money.

HOW DEALS WORK: Pick a brand in #sign-up, sign up to its program, get a unique tracked link/code, post content, get paid a % of every sale you drive. You can run multiple brands at once. You keep 100% of your own brand and followers.

PAYOUTS: Weekly. Tracked automatically through each brand's affiliate platform. Set up your payout method when you sign up to a brand's program. Some platforms hold a few days for returns.

DEALS STATUS: we're in pre-launch right now - the first brand deals are dropping very soon and will be posted in #sign-up. for now, get set up: lock your niche, sharpen your content in the coaching channels, and be ready to move the second a deal goes live. don't hand out any signup links yet because none are live.

THE STEPS TO GET READY: 1) finish onboarding so we know your niche 2) go through the coaching channels (hooks, going viral, ai-content) 3) start posting daily on TikTok/Reels/Shorts/FB to warm up your account 4) when a deal drops in #sign-up, grab your tracked link and run it 5) get your first sale, screenshot it in #wins to unlock the inner circle.

PROGRESSION LADDER: Copper (just joined) -> Silver (1+ sale, unlocks inner circle + leaderboard) -> Gold (sustained sales, early deal access) -> Emerald (top-tier perks, higher commission) -> Diamond (apex, eligible for monthly base pay). VIP is a separate hand-picked badge.

RULES: no spam, no scams, no fake screenshots. Only promote with your own tracked link. Follow each brand's content guidelines. No medical or income claims a brand hasn't approved.

NICHES: Health, Beauty, Personal, Fitness, Business.

SKOOL: optional inner community for serious creators, unlocked after first sale. Free network stays free."""

ONBOARD_PROMPT = """You are ALGO, the onboarding host for the Algorithm Arbitrage Affiliate Network. You talk like a chill helpful friend putting someone on. Lowercase, short texts, one question at a time, never salesy or corporate.

Private 1-on-1 thread with one new creator. Walk them through, in order:
1. Quick warm welcome.
2. Their NICHE -> map to ONE: Health, Beauty, Personal, Fitness, Business. Map close answers: supplements/wellness/nutrition/sleep/energy -> Health, skincare/makeup/hair -> Beauty, lifestyle/coaching/mindset/personal brand -> Personal, gym/workout/strength -> Fitness, entrepreneurship/finance/side hustles/money/startups -> Business.
3. Platforms they post on + their @ handles.
4. Audience / follower size (rough is fine).
5. Main goal for the next 90 days.
6. Experience: new, or been at it a while.
7. Get them ready (we're PRE-LAUNCH, no deals are live yet, do NOT give any signup link). Tell them: brand deals are dropping in #sign-up very soon, so right now they should go through the coaching channels and start posting daily to warm up their account, and they'll be first in line when a deal goes live. Tell them to drop their first videos in #drop-your-videos for feedback.

CONTROL TAGS (user never sees them; own line, end of message):
- niche known: [[NICHE:X]]
- once you have niche+platforms+handles+audience+goal+experience: [[SAVE:{"niche":"","platforms":"","handles":"","audience_size":"","goal":"","experience":""}]]
- after the get-ready nudge: [[DONE]]
Each tag once."""

QA_PROMPT = f"""You are ALGO, the community manager for the Algorithm Arbitrage Affiliate Network. Answer the member's question using ONLY the knowledge base below. Lowercase, short, friendly "put you on" voice. If the answer is not clearly in the knowledge base, do NOT guess - reply briefly that you'll grab a human, and put [[ESCALATE]] on its own line at the end.

KNOWLEDGE BASE:
{KB}"""

# Pre-launch: no live deal yet, so the daily auto-post is OFF. Flip
# DAILY_POST_ENABLED to True (and edit DAILY_DEAL_POST) once a deal is live.
DAILY_POST_ENABLED = os.environ.get("DAILY_POST_ENABLED", "").lower() in ("1", "true", "yes")
DAILY_DEAL_POST = (
    "gm. coaching's open and deals are dropping soon. go through the training "
    "channels and post one piece of content today. drop it in #drop-your-videos. "
    "let's get ready."
)

# ---------------- ROLE LADDER ----------------
# Full role ladder, TOP -> BOTTOM (ALGO and @everyone are not created here).
# Colors are 0xRRGGBB. !setup-roles creates any that are missing and orders them.
ROLE_LADDER = [
    ("Junior Admin", 0xE74C3C),
    ("Community Manager", 0xE67E22),
    ("Brand Success", 0xF1C40F),
    ("VIP", 0x9B59B6),
    ("Diamond", 0x5DADE2),
    ("Emerald", 0x2ECC71),
    ("Gold", 0xF39C12),
    ("Silver", 0xBDC3C7),
    ("Copper", 0xCD7F32),
    ("Health", 0x1ABC9C),
    ("Beauty", 0xFF6FCF),
    ("Personal", 0x3498DB),
    ("Fitness", 0xE91E63),
    ("Business", 0x34495E),
]

# ---------------- DISCORD ----------------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
client = discord.Client(intents=intents)

threads = {}      # thread_id -> {user_id, username, history, nudged}
role_cache = {}

SPAM = re.compile(
    r"(discord\.gg/|free\s*nitro|steam(community)?\s*gift|t\.me/|airdrop|"
    r"claim\s+your|crypto\s+giveaway|@everyone|@here)", re.IGNORECASE)


def is_staff(member):
    if isinstance(member, discord.Member):
        if member.guild_permissions.manage_messages:
            return True
        return any(r.name in STAFF_ROLES for r in member.roles)
    return False


# ---- Supabase helpers ----
def _sb_post(table, rec, upsert_key=None):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    if upsert_key:
        url += f"?on_conflict={upsert_key}"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
               "Content-Type": "application/json",
               "Prefer": "resolution=merge-duplicates"}
    try:
        r = requests.post(url, headers=headers, json=rec, timeout=10)
        if r.status_code >= 300:
            print("supabase post:", r.status_code, r.text)
    except Exception as e:
        print("supabase post exception:", e)


def _sb_get(path):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/{path}", headers=headers, timeout=10)
        return r.json() if r.status_code < 300 else []
    except Exception as e:
        print("supabase get exception:", e)
        return []


async def sb_post(table, rec, upsert_key=None):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, functools.partial(_sb_post, table, rec, upsert_key))


async def sb_get(path):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, functools.partial(_sb_get, path))


async def claude(system, messages, max_tokens=400):
    """Call the LLM (Groq/Llama). Name kept for the rest of the code.
    Converts the Anthropic-style system+messages into OpenAI chat format."""
    loop = asyncio.get_event_loop()

    def call():
        chat = [{"role": "system", "content": system}] + messages
        r = llm.chat.completions.create(model=MODEL, max_tokens=max_tokens,
                                        messages=chat)
        return (r.choices[0].message.content or "").strip()

    return await loop.run_in_executor(None, call)


async def escalate(reason, message):
    if not STAFF_CHANNEL_ID:
        return  # no staff channel configured -> skip silently
    staff = client.get_channel(STAFF_CHANNEL_ID)
    if staff:
        await staff.send(f"heads up, ALGO needs you. {reason}\nfrom {message.author} "
                         f"in {message.channel.mention}: {message.jump_url}\n"
                         f"> {message.content[:300]}")


@client.event
async def on_ready():
    guild = client.get_guild(GUILD_ID)
    if guild:
        for r in guild.roles:
            if r.name in NICHE_ROLES or r.name == ENTRY_ROLE:
                role_cache[r.name] = r
    if DAILY_POST_ENABLED and not daily_post.is_running():
        daily_post.start()
    print(f"ALGO online as {client.user}. Roles: {list(role_cache)}. "
          f"Daily post: {'on' if DAILY_POST_ENABLED else 'off'}", flush=True)


@client.event
async def on_member_join(member):
    entry = role_cache.get(ENTRY_ROLE)
    if entry:
        try:
            await member.add_roles(entry, reason="joined")
        except discord.Forbidden:
            pass
    parent = client.get_channel(ONBOARD_CHANNEL_ID)
    if not parent:
        return
    try:
        thread = await parent.create_thread(
            name=f"welcome-{member.display_name}"[:90],
            type=discord.ChannelType.private_thread, invitable=False)
        await thread.add_user(member)
    except Exception as e:
        print("thread create failed:", e)
        return
    greeting = (f"yo {member.mention} welcome in. i'll get you set up real quick. "
                f"first off, what kind of content do you make?")
    await thread.send(greeting)
    threads[thread.id] = {"user_id": member.id, "username": str(member),
                          "history": [{"role": "assistant", "content": greeting}],
                          "nudged": False}
    await sb_post("creators", {"discord_id": str(member.id),
                               "username": str(member), "status": "onboarding"},
                  upsert_key="discord_id")


async def setup_roles(message):
    """Admin-only: create any missing roles in ROLE_LADDER and order them.
    New roles the bot creates land just under ALGO's role, so ALGO can assign
    them. Staff roles end up below ALGO too — fine; only cosmetic ordering."""
    guild = message.guild
    if guild is None:
        return
    await message.channel.send("setting up the role ladder... one sec.")
    existing = {r.name: r for r in guild.roles}
    created, skipped = [], []
    for name, color in ROLE_LADDER:
        if name in existing:
            skipped.append(name)
            continue
        try:
            await guild.create_role(name=name, colour=discord.Colour(color),
                                    mentionable=True, reason="ALGO setup-roles")
            created.append(name)
        except discord.Forbidden:
            await message.channel.send(
                "i don't have **Manage Roles** permission, or my role is too low. "
                "give ALGO Manage Roles and drag ALGO's role near the top, then "
                "run `!setup-roles` again.")
            return
        except Exception as e:
            print("create_role error:", e)

    # Try to order the ladder (best-effort; ignore the ones above ALGO).
    try:
        me = guild.me
        positions = {}
        # place ladder roles just below ALGO's top role, in order
        base = me.top_role.position
        rolemap = {r.name: r for r in guild.roles}
        for i, (name, _) in enumerate(ROLE_LADDER):
            r = rolemap.get(name)
            if r and r < me.top_role:
                positions[r] = max(1, base - 1 - i)
        if positions:
            await guild.edit_role_positions(positions=positions,
                                            reason="ALGO setup-roles order")
    except Exception as e:
        print("role ordering skipped:", e)

    # refresh the role cache so onboarding can use them immediately
    for r in guild.roles:
        if r.name in NICHE_ROLES or r.name == ENTRY_ROLE:
            role_cache[r.name] = r

    msg = f"done. created: {', '.join(created) or 'none'}."
    if skipped:
        msg += f"\nalready existed: {', '.join(skipped)}."
    msg += ("\n\nlast step: make sure **ALGO**'s own role is dragged ABOVE "
            "Copper + the niche roles in Server Settings -> Roles, so i can "
            "assign them.")
    await message.channel.send(msg)


@client.event
async def on_message(message):
    if message.author.bot:
        return

    # Admin command: build the role ladder. Server admins / Manage Roles only.
    if message.content.strip().lower() == "!setup-roles":
        perms = getattr(message.author, "guild_permissions", None)
        if perms and (perms.administrator or perms.manage_roles):
            await setup_roles(message)
        else:
            await message.channel.send("that's an admin-only command.")
        return

    # 1) onboarding thread
    state = threads.get(message.channel.id)
    if state and message.author.id == state["user_id"]:
        await handle_onboarding(message, state)
        return

    # 2) support channel
    if SUPPORT_CHANNEL_ID and message.channel.id == SUPPORT_CHANNEL_ID \
            and not is_staff(message.author):
        await handle_qa(message)
        return

    # 3) @mention anywhere
    if client.user in message.mentions:
        await handle_qa(message)
        return

    # 4) light moderation everywhere else
    if not is_staff(message.author) and SPAM.search(message.content):
        await escalate("possible spam/scam (not deleted, light mod).", message)


async def handle_onboarding(message, state):
    state["history"].append({"role": "user", "content": message.content})
    state["history"] = state["history"][-16:]
    try:
        reply = await claude(ONBOARD_PROMPT, state["history"])
    except Exception as e:
        print("llm error:", e)
        await message.channel.send("one sec, lagged. say that again?")
        return

    m = re.search(r"\[\[NICHE:(\w+)\]\]", reply)
    if m and role_cache.get(m.group(1)):
        try:
            await message.author.add_roles(role_cache[m.group(1)], reason="niche")
        except discord.Forbidden:
            print("can't assign role - ALGO must be above the niche roles")

    s = re.search(r"\[\[SAVE:(\{.*?\})\]\]", reply, re.DOTALL)
    if s:
        try:
            data = json.loads(s.group(1))
            data.update({"discord_id": str(message.author.id),
                         "username": str(message.author), "status": "active"})
            await sb_post("creators", data, upsert_key="discord_id")
        except Exception as e:
            print("save parse error:", e)

    if "[[DONE]]" in reply:
        asyncio.create_task(schedule_nudge(message.channel.id))

    clean = re.sub(r"\[\[(NICHE:\w+|SAVE:\{.*?\}|DONE)\]\]", "", reply,
                   flags=re.DOTALL).strip()
    state["history"].append({"role": "assistant", "content": reply})
    if clean:
        await message.channel.send(clean)


async def handle_qa(message):
    q = message.content.replace(f"<@{client.user.id}>", "").strip()
    try:
        reply = await claude(QA_PROMPT, [{"role": "user", "content": q}], max_tokens=350)
    except Exception as e:
        print("llm error:", e)
        return
    if "[[ESCALATE]]" in reply:
        await escalate("couldn't answer from the knowledge base.", message)
        reply = re.sub(r"\[\[ESCALATE\]\]", "", reply).strip() or \
            "good q, let me grab someone who knows for sure. one sec."
    await message.reply(reply, mention_author=False)


async def schedule_nudge(thread_id):
    await asyncio.sleep(NUDGE_AFTER)
    state = threads.get(thread_id)
    if not state or state.get("nudged"):
        return
    thread = client.get_channel(thread_id)
    if thread:
        await thread.send("yo you get any content up yet? drop it in "
                          "#drop-your-videos for feedback. stuck on anything? "
                          "tell me here.")
        state["nudged"] = True


@tasks.loop(hours=24)
async def daily_post():
    channel = client.get_channel(DEALS_CHANNEL_ID)
    if not channel:
        return
    await channel.send(DAILY_DEAL_POST)
    rows = await sb_get("sales?select=handle,amount&order=amount.desc&limit=10")
    if rows:
        lines = [f"{i+1}. {r.get('handle','?')} - ${float(r.get('amount',0)):,.0f}"
                 for i, r in enumerate(rows)]
        await channel.send("**this week's top creators:**\n" + "\n".join(lines))


@daily_post.before_loop
async def _wait():
    await client.wait_until_ready()


if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
