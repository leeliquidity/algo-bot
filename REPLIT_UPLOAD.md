# Deploy ALGO to Replit (manual upload) — 24/7 hosting

## Step 1 — make the Repl
1. Go to https://replit.com and sign in
2. **Create Repl** → choose **Python** template → name it `algo-bot` → Create

## Step 2 — upload these 4 files
Drag them from `C:\Users\LeeJJ\algo-bot\` into the Replit file panel:
- `algo_bot.py`
- `requirements.txt`
- `.replit`
- `replit.nix`

(Do NOT upload `.env` — secrets go in the Secrets tab instead. Skip `bot.js`,
`package.json`, `node_modules` — those are the old JS version, not used.)

## Step 3 — add Secrets (the lock icon 🔒 in the left sidebar)
Add each as a key / value:

| Key | Value |
|-----|-------|
| `DISCORD_TOKEN` | (your bot token) |
| `GROQ_API_KEY` | (your gsk_... key) |
| `LLM_MODEL` | `llama-3.3-70b-versatile` |
| `GUILD_ID` | `1510090305272152204` |
| `ONBOARD_CHANNEL_ID` | `1510098601328771072` |
| `SUPPORT_CHANNEL_ID` | `1510094935217406062` |
| `DEALS_CHANNEL_ID` | `1510095025659183347` |
| `SUPABASE_URL` | `https://dghbrppywjwbbnmkhbxq.supabase.co` |
| `SUPABASE_KEY` | (the service key) |

Leave out `STAFF_CHANNEL_ID`, `SB_LINK`, `DAILY_POST_ENABLED` for now (pre-launch).

## Step 4 — Run
Click **Run**. Console should print:
`ALGO online as ALGO#9615. Roles: [...]. Daily post: off`

## Step 5 — 24/7 uptime
A normal Repl sleeps when idle. To keep ALGO always-on, either:
- **Reserved VM Deployment** (~$5/mo, most reliable) — Replit's "Deploy" button → Reserved VM → Background worker, OR
- free route: keep it awake with an uptime pinger (less reliable, ok to start)

---

## Before/after deploy: build the roles
Once ALGO is running (locally OR on Replit), in any channel he can see, an
admin types:

    !setup-roles

He'll auto-create the whole ladder (Junior Admin → ... → Copper → Health,
Beauty, Personal, Fitness, Business) with colors.

**Then** drag **ALGO's own role ABOVE** Copper + the niche roles
(Server Settings → Roles). A bot can only assign roles below itself.

⚠️ ALGO needs the **Manage Roles** permission for `!setup-roles` and for
assigning niche roles during onboarding. If you didn't grant it when inviting
him: Server Settings → Roles → ALGO → enable **Manage Roles**.
