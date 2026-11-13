#!/usr/bin/env bash
# Publiceert een release van deze fork voor HACS: zet de versie in manifest.json, commit en tagt die,
# pusht branch en tag naar de fork en maakt een GitHub-release (HACS installeert de getagde bron).
#
# Gebruik: scripts/fork-release.sh v1.6.0-milenco.2 "Wat er veranderd is"
set -euo pipefail

tag="${1:?geef een tag op, bijv. v1.6.0-milenco.2}"
notes="${2:-}"
repo="${REPO:-Milenco/ha-xplora-watch}"
manifest="custom_components/xplora_watch/manifest.json"

cd "$(git rev-parse --show-toplevel)"
[[ "$(git branch --show-current)" == "milenco" ]] || { echo "Niet op branch milenco" >&2; exit 1; }
[[ -z "$(git status --porcelain)" ]] || { echo "Werkmap is niet schoon" >&2; exit 1; }
git rev-parse -q --verify "refs/tags/$tag" >/dev/null && { echo "Tag $tag bestaat al" >&2; exit 1; }

python3 -I - "$manifest" "$tag" <<'EOF'
import json, sys
path, tag = sys.argv[1], sys.argv[2]
data = json.load(open(path))
data["version"] = tag
open(path, "w").write(json.dumps(data, indent=2) + "\n")
EOF
git add "$manifest"
git commit -q -m "chore(fork): release $tag"
git tag -a "$tag" -m "$tag"
git push -q fork milenco "$tag"

gh release create "$tag" -R "$repo" --verify-tag --title "$tag" --notes "$notes"
echo "Release $tag gepubliceerd; HACS ziet hem na 'Update informatie' of binnen enkele uren."
