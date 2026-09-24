#!/usr/bin/env bash
# rename_project.sh — rename Axiom AI (and old "Noor AI") to NEW name everywhere in your repo.
# Usage (run from the repo root):   bash rename_project.sh            # does the code rename
#                                   bash rename_project.sh publish    # prints the publish commands
# Change NEW_LOWER / NEW_TITLE below if you pick a different name.

set -euo pipefail

NEW_LOWER="velto"     # package / repo / import name (lowercase, no spaces)
NEW_TITLE="Velto"     # display name
NEW_UPPER="VELTO"     # env vars / constants

if [[ "${1:-}" == "publish" ]]; then
cat <<EOF
=== PUBLISH STEPS (run these yourself, in order) ===

1) GitHub  (redirects from the old URL keep working)
   gh repo rename ${NEW_LOWER}
   git remote set-url origin https://github.com/<you>/${NEW_LOWER}.git

2) Hugging Face  (Space/model/dataset; old URL redirects)
   pip install -U huggingface_hub
   python - <<'PY'
from huggingface_hub import HfApi
api = HfApi()
api.move_repo(from_id="yaad25/axiom-ai", to_id="yaad25/${NEW_LOWER}", repo_type="space")
# repeat for any model/dataset repos, with repo_type="model" or "dataset"
PY

3) PyPI  (packages CAN'T be renamed: publish a new one, retire the old one)
   pip install -U build twine
   python -m build
   twine upload dist/*
   # Old package: upload one last release whose README says "Renamed to ${NEW_LOWER}",
   # then archive it in PyPI project settings (only if you own it).

4) npm  (also can't rename: publish new, deprecate old)
   npm publish --access public
   npm deprecate "axiom-decision-ai@*" "Renamed to ${NEW_LOWER}. Run: npm i ${NEW_LOWER}"

5) Also update by hand: domain/DNS, docs site, README badges, Docker image name,
   API base URL (keep the old one alive as a redirect for a few months), social handles.
EOF
exit 0
fi

# ---- safety: clean git tree + work on a branch so you can undo everything ----
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "Run inside your git repo."; exit 1; }
[[ -z "$(git status --porcelain)" ]] || { echo "Commit or stash your changes first."; exit 1; }
git checkout -b "rename-to-${NEW_LOWER}"

# ---- 1) replace text in all tracked text files (longest patterns first) ----
mapfile -t FILES < <(git ls-files | xargs grep -Il . 2>/dev/null || true)
for f in "${FILES[@]}"; do
  sed -i.bak \
    -e "s/axiom-decision-ai/${NEW_LOWER}/g" \
    -e "s/axiom_decision_ai/${NEW_LOWER}/g" \
    -e "s/Axiom AI/${NEW_TITLE}/g" \
    -e "s/Noor AI/${NEW_TITLE}/g" \
    -e "s/axiom-ai/${NEW_LOWER}/g" \
    -e "s/axiom_ai/${NEW_LOWER}/g" \
    -e "s/AXIOM/${NEW_UPPER}/g" \
    -e "s/Axiom/${NEW_TITLE}/g" \
    -e "s/axiom/${NEW_LOWER}/g" \
    "$f"
  rm -f "$f.bak"
done

# ---- 2) rename files and folders whose names contain "axiom" (deepest first) ----
git ls-files | grep -i axiom | awk '{print length, $0}' | sort -rn | cut -d' ' -f2- | while read -r p; do
  new="$(dirname "$p")/$(basename "$p" | sed "s/axiom/${NEW_LOWER}/Ig")"
  [[ "$p" != "$new" ]] && mkdir -p "$(dirname "$new")" && git mv "$p" "$new"
done

# ---- 3) show what's left and what to check ----
echo; echo "Leftover mentions (should be empty):"; git grep -in "axiom" || echo "  none"
echo; echo "Also check: pyproject.toml / setup.py name, package.json name, Dockerfile, CI workflows."
git add -A && git commit -qm "Rename project to ${NEW_TITLE}"
echo; echo "Done on branch rename-to-${NEW_LOWER}. Test it, then run:  bash rename_project.sh publish"
