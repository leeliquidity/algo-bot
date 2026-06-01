# ALGO on Oracle Cloud Always Free — full runbook

Goal: run ALGO 24/7 on a free Oracle Linux VM that stays on even when your PC is off.
You do the browser/SSH steps; Claude prepped every file + command. Paste outputs back.

═══════════════════════════════════════════════════════════
PART 1 — Create the Oracle Cloud account  (YOU, ~10 min + approval wait)
═══════════════════════════════════════════════════════════
1. Go to https://www.oracle.com/cloud/free/  → "Start for free".
2. Sign up: email, country, verify email.
3. ⚠️ It asks for a CREDIT CARD — this is for identity only. The "Always Free"
   resources never charge. They place a temporary ~$1 auth hold that drops off.
   Do NOT upgrade to "Pay As You Go" if you want to stay free.
4. Pick a Home Region close to you (you can't change it later). US East (Ashburn)
   or US West (Phoenix) are fine.
5. Finish. Account approval can take anywhere from instant to a few hours.
   When you can log into https://cloud.oracle.com you're ready for Part 2.

STOP here and tell Claude when you're logged into the Oracle console.

═══════════════════════════════════════════════════════════
PART 2 — Create the free VM instance  (YOU, ~10 min, Claude guides)
═══════════════════════════════════════════════════════════
In the Oracle console:
1. Hamburger menu → Compute → Instances → "Create instance".
2. Name: algo-bot
3. Image & shape:
   - Image: Canonical Ubuntu (22.04 or 24.04).
   - Shape: click "Change shape" → "Ampere" (ARM) → VM.Standard.A1.Flex →
     set 1 OCPU, 6 GB RAM  (well within Always Free). If ARM capacity is
     unavailable in your region, use "Specialty and previous gen" →
     VM.Standard.E2.1.Micro (AMD, also Always Free).
4. SSH keys: choose "Generate a key pair for me" → DOWNLOAD BOTH the private
   and public key. Save them somewhere safe (e.g. C:\Users\LeeJJ\.ssh\). The
   private key is how you log in — losing it locks you out.
5. Networking: leave defaults (creates a VCN with a public IP). Make sure
   "Assign a public IPv4 address" is YES.
6. Create. Wait ~1 min until state = RUNNING. Copy the PUBLIC IP ADDRESS.

A Discord bot makes only OUTbound connections, so you do NOT need to open any
inbound ports. Default security rules are fine.

Tell Claude the public IP when the instance is RUNNING.

═══════════════════════════════════════════════════════════
PART 3 — Connect via SSH  (YOU, Claude gives exact command)
═══════════════════════════════════════════════════════════
From your Windows machine (PowerShell), using the private key you downloaded:

    ssh -i C:\Users\LeeJJ\.ssh\<your-private-key> ubuntu@<PUBLIC_IP>

(The default user for Ubuntu images is `ubuntu`.)
First connect asks "are you sure" → type yes.
If it complains the key is "too open", Claude will give you the icacls fix.

═══════════════════════════════════════════════════════════
PART 4 — Install + run ALGO  (Claude gives a single paste-in block)
═══════════════════════════════════════════════════════════
Once you're SSH'd in, Claude provides one block that:
  - installs python3, venv, git
  - clones the repo (private → uses a short-lived token or a deploy key)
  - creates the venv + installs requirements
  - writes the .env (Claude provides the contents)
  - installs the systemd service (algo-bot.service) so it runs 24/7 +
    auto-restarts on crash + auto-starts on reboot
  - starts it and shows the logs

Then: `sudo systemctl status algo-bot` should show "active (running)" and the
logs show `ALGO online as ALGO#9615`.

That's it — ALGO is live 24/7, PC can be off.
