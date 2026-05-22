# config.py — Central Path Registry for F.R.I.D.A.Y.
# ALL hardcoded paths in the codebase must source from here.
# To move the system to a new drive or machine, only edit FRIDAY_ROOT below.

import os

# ─── PRIMARY ROOT ───────────────────────────────────────────────────────────────
# Change ONLY this one line to relocate the entire system.
FRIDAY_ROOT = os.getenv("FRIDAY_ROOT", r"E:\F.R.I.D.A.Y")

# ─── DERIVED PATHS (never hardcode these elsewhere) ────────────────────────────
WORKSPACE_ROOT   = os.path.join(FRIDAY_ROOT, "Workspace")
MACRO_FILE       = os.path.join(FRIDAY_ROOT, "macros.json")
SYSTEM_VITALS    = os.path.join(FRIDAY_ROOT, "system_vitals.txt")
STAGING_DIR      = os.path.join(FRIDAY_ROOT, "staging")
HUD_LOG_FILE     = os.path.join(FRIDAY_ROOT, "hud_log.jsonl")

# ─── REGISTRY & STORAGE PATHS ──────────────────────────────────────────────────
REGISTRY_FILE       = os.path.join(FRIDAY_ROOT, "registry.json")
MEMORY_VAULT        = os.path.join(FRIDAY_ROOT, "friday_cortex")
OBSIDIAN_VAULT      = os.path.join(FRIDAY_ROOT, "obsidian_vault")
INTEL_BRIEFING_FILE = os.path.join(FRIDAY_ROOT, "macro_intelligence_briefing.txt")

# ─── ENSURE CRITICAL DIRS EXIST ON BOOT ────────────────────────────────────────
os.makedirs(WORKSPACE_ROOT, exist_ok=True)
os.makedirs(STAGING_DIR,    exist_ok=True)