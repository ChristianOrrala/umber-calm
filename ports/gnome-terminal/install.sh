#!/usr/bin/env bash
# Umber Calm 0.1.0 — generated from templates/gnome-terminal/install.sh.tmpl. Do not edit. MIT License.
# Creates (or updates) the GNOME Terminal profile "Umber Calm" under its own fixed UUID.
# Profiles this script did not create are never modified, even if they have the same name.
# Usage: bash install.sh          # create or update
#        bash install.sh --remove # delete only the profile this script owns
set -euo pipefail
NAME="Umber Calm"
UUID="b6885571-c238-4b0d-8904-5a8531dfdbae"
GNOME_DEFAULT="b1dcc9dd-5262-4d8d-a863-c897e6d979b9"
BASE="/org/gnome/terminal/legacy/profiles:"
P="$BASE/:$UUID"
command -v dconf >/dev/null || { echo "dconf not found" >&2; exit 1; }
command -v python3 >/dev/null || { echo "python3 not found" >&2; exit 1; }

# GVariant string-array helper. Parses with ast.literal_eval (never sed); accepts '', '[]' and '@as []'.
LISTTOOL='
import ast, sys

def parse(raw):
    raw = raw.strip()
    if raw.startswith("@as"):
        raw = raw[3:].strip()
    items = ast.literal_eval(raw) if raw else []
    if not isinstance(items, list) or not all(isinstance(i, str) for i in items):
        sys.exit("unexpected profile list: " + raw)
    return items

def show(items):
    return "[" + ", ".join(repr(i) for i in items) + "]" if items else "@as []"

op, raw = sys.argv[1], sys.argv[2]
items = parse(raw)
if op == "ids":
    print("\n".join(items))
elif op == "first":
    print(items[0] if items else "")
elif op == "add":
    uid, seed = sys.argv[3], sys.argv[4]
    if not raw.strip():
        items = [seed]
    if uid not in items:
        items.append(uid)
    print(show(items))
elif op == "remove":
    print(show([i for i in items if i != sys.argv[3]]))
'
listtool() { python3 -c "$LISTTOOL" "$@"; }

LIST="$(dconf read "$BASE/list" || true)"

if [ "${1:-}" = "--remove" ]; then
  case "$LIST" in
    *"'$UUID'"*) ;;
    *) echo "\"$NAME\" ($UUID) is not installed; nothing to do"; exit 0 ;;
  esac
  NEW="$(listtool remove "$LIST" "$UUID")"
  if [ "$(dconf read "$BASE/default" || true)" = "'$UUID'" ]; then
    FIRST="$(listtool first "$NEW")"
    [ -n "$FIRST" ] || { echo "\"$NAME\" is your only profile; create another profile before removing it" >&2; exit 1; }
    dconf write "$BASE/default" "'$FIRST'"
  fi
  dconf write "$BASE/list" "$NEW"
  dconf reset -f "$P/"
  echo "removed \"$NAME\" ($UUID)"
  exit 0
fi

IDS="$(listtool ids "$LIST")"
for id in $IDS; do
  [ "$id" = "$UUID" ] && continue
  if [ "$(dconf read "$BASE/:$id/visible-name" || true)" = "'$NAME'" ]; then
    echo "note: profile $id is also named \"$NAME\"; it is left untouched" >&2
  fi
done

SEED="$(dconf read "$BASE/default" || true)"
SEED="${SEED//\'/}"
[ -n "$SEED" ] || SEED="$GNOME_DEFAULT"
dconf write "$BASE/list" "$(listtool add "$LIST" "$UUID" "$SEED")"
dconf write "$P/visible-name" "'$NAME'"
dconf write "$P/use-theme-colors" false
dconf write "$P/background-color" "'#201F1D'"
dconf write "$P/foreground-color" "'#D6C9B6'"
dconf write "$P/bold-color-same-as-fg" true
dconf write "$P/cursor-colors-set" true
dconf write "$P/cursor-background-color" "'#EDA97C'"
dconf write "$P/cursor-foreground-color" "'#201F1D'"
dconf write "$P/highlight-colors-set" true
dconf write "$P/highlight-background-color" "'#3C3A36'"
dconf write "$P/highlight-foreground-color" "'#D6C9B6'"
dconf write "$P/palette" "['#2A2826', '#E08374', '#A7B56E', '#DCC07D', '#88B0B4', '#C9A0C0', '#88C0AE', '#D6C9B6', '#6E6961', '#EC9A8C', '#B9C684', '#E8CE92', '#9DC2C5', '#D7B4CF', '#9CCEBC', '#EDE3D2']"
echo "profile \"$NAME\" is ready ($UUID)"
echo "To remove it later: bash install.sh --remove"
