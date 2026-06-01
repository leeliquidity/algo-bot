"""ALGO preflight check. Logs in, verifies everything onboarding/Q&A needs,
prints a PASS/FAIL report, exits. Run before testing:  python3.12 preflight.py
Read-only except nothing is changed — it only inspects."""
import os
import discord

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

TOKEN = os.environ["DISCORD_TOKEN"]
GUILD_ID = int(os.environ["GUILD_ID"])
ONBOARD_CHANNEL_ID = int(os.environ.get("ONBOARD_CHANNEL_ID") or 0)
SUPPORT_CHANNEL_ID = int(os.environ.get("SUPPORT_CHANNEL_ID") or 0)
DEALS_CHANNEL_ID = int(os.environ.get("DEALS_CHANNEL_ID") or 0)
NICHE_ROLES = ["Health", "Beauty", "Personal", "Fitness", "Business"]
ENTRY_ROLE = "Copper"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
client = discord.Client(intents=intents)


def ok(b):
    return "✅" if b else "❌"


@client.event
async def on_ready():
    print(f"\n{'='*48}\nALGO PREFLIGHT\n{'='*48}")
    print(f"logged in as: {client.user}")

    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("❌ FATAL: bot is not in the guild / wrong GUILD_ID")
        await client.close()
        return
    print(f"guild: {guild.name}  ({guild.member_count} members)\n")

    me = guild.me
    p = me.guild_permissions
    print("PERMISSIONS")
    print(f"  {ok(p.manage_roles)} Manage Roles      (needed to assign Copper + niche)")
    print(f"  {ok(p.create_public_threads or p.create_private_threads)} Create Threads    (needed for onboarding threads)")
    print(f"  {ok(p.send_messages)} Send Messages")
    print(f"  {ok(p.read_message_history)} Read History")

    print("\nINTENTS (must be ON in Dev Portal)")
    print(f"  {ok(intents.members)} Server Members")
    print(f"  {ok(intents.message_content)} Message Content")

    print("\nCHANNELS (bot can see them?)")
    for label, cid in [("onboarding", ONBOARD_CHANNEL_ID),
                       ("support", SUPPORT_CHANNEL_ID),
                       ("deals", DEALS_CHANNEL_ID)]:
        ch = guild.get_channel(cid)
        name = f"#{ch.name}" if ch else "NOT FOUND / not visible"
        print(f"  {ok(bool(ch))} {label:10} -> {name}")

    print("\nROLES (exist + ALGO is above them?)")
    rolemap = {r.name: r for r in guild.roles}
    my_top = me.top_role
    for rn in [ENTRY_ROLE] + NICHE_ROLES:
        r = rolemap.get(rn)
        if not r:
            print(f"  ❌ {rn:10} -> missing")
        else:
            above = my_top > r
            print(f"  {ok(above)} {rn:10} -> exists, ALGO {'above' if above else 'BELOW (can’t assign!)'}")

    # quick verdict
    blockers = []
    if not p.manage_roles:
        blockers.append("grant ALGO Manage Roles")
    if not (p.create_public_threads or p.create_private_threads):
        blockers.append("grant ALGO Create Threads")
    if not guild.get_channel(ONBOARD_CHANNEL_ID):
        blockers.append("onboarding channel not visible")
    for rn in [ENTRY_ROLE] + NICHE_ROLES:
        r = rolemap.get(rn)
        if r and not (my_top > r):
            blockers.append(f"drag ALGO above '{rn}'")

    print(f"\n{'='*48}")
    if blockers:
        print("⚠️  FIX BEFORE TESTING:")
        for b in blockers:
            print(f"   - {b}")
    else:
        print("🟢 ALL CLEAR — onboarding, role-assign, Q&A should all work. Go test.")
    print(f"{'='*48}\n")
    await client.close()


client.run(TOKEN, log_handler=None)
