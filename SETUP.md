# ALGO — full setup runbook

Work top to bottom. Each step says **YOU** (only you can do it) or **DONE** (already handled).

---

## Part A — Get the 2 API keys

### A1. Groq key (ALGO's AI brain) — **YOU** (~2 min)
1. Go to https://console.groq.com
2. Sign in (Google/GitHub works)
3. Left sidebar -> **API Keys** -> **Create API Key**
4. Name it `algo` -> copy the key (starts with `gsk_...`)
5. Paste it to me, or save it for the Replit secrets step.
   - Free tier is plenty for a new server.

### A2. Supabase (the database) — **YOU pick one**
**Option 1 (fastest): reuse your existing ugc-empire Supabase.**
   - URL: `https://dghbrppywjwbbnmkhbxq.supabase.co`
   - Service key: already on file.
**Option 2: fresh project** at https://supabase.com -> New Project -> grab URL + service_role key
   (Settings -> API -> `service_role` secret).

Then create the tables: Supabase Dashboard -> **SQL Editor** -> New query ->
paste the contents of `SUPABASE_TABLES.sql` -> **Run**.

---

## Part B — Discord server setup — **YOU**

### B1. Create 6 niche roles
Server Settings -> Roles -> create (exact spelling, capitalized):
`Supplements`  `Beauty`  `Fashion`  `Home`  `Fitness`  `Pet`
(You already have a `Rookie` role from before — keep it.)

### B2. Put ALGO above the niche roles
Server Settings -> Roles -> drag **ALGO**'s role ABOVE all 6 niche roles + Rookie.
(A bot can only assign roles below its own. If ALGO is too low, role assignment silently fails.)

### B3. Create / identify 4 channels
- an **onboarding** channel (parent for the private welcome threads)
- **#support**
- a **staff-only** channel (where ALGO pings you for escalations)
- a **deals** channel (where the daily post + leaderboard go)

### B4. Copy the 4 channel IDs
Turn on Developer Mode (User Settings -> Advanced -> Developer Mode),
then right-click each channel -> **Copy Channel ID**. Send me all 4 labeled.

### B5. SuperBonsai signup link
Send me the affiliate signup link creators should use (`SB_LINK`).

---

## Part C — Deploy on Replit — **WE do together**

1. https://replit.com -> **Create Repl** -> **Import from GitHub** OR blank Python repl
2. Upload these files (I'll tell you which / or we push a repo):
   `algo_bot.py`, `requirements.txt`, `.replit`, `replit.nix`
3. Replit left sidebar -> **Secrets** (lock icon) -> add each as a key/value:
   - `DISCORD_TOKEN`
   - `GROQ_API_KEY`
   - `GUILD_ID` = `1510090305272152204`
   - `ONBOARD_CHANNEL_ID`, `SUPPORT_CHANNEL_ID`, `STAFF_CHANNEL_ID`, `DEALS_CHANNEL_ID`
   - `SB_LINK`
   - `SUPABASE_URL`, `SUPABASE_KEY`
4. Click **Run**. Console should print: `ALGO online as ALGO#9615. Roles: [...]`
5. For true 24/7: enable Replit **Reserved VM Deployment** (~$5/mo) OR keep the
   repl alive with an uptime pinger (free, slightly less reliable).

---

## What to send me next
- [ ] Groq key (or "got it, adding in Replit")
- [ ] Supabase choice (reuse ugc-empire? or new URL+key)
- [ ] 4 channel IDs (labeled)
- [ ] SuperBonsai link
- [ ] confirm roles created + ALGO dragged above them
