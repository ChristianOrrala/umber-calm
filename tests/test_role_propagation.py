"""Spec §5.1: templates use syntax roles, so a role change reaches every keyword mapping of every port with a
syntax_check, and the old keyword color is left in none of them."""
import json, plistlib, re, shutil, tomllib, unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from tests.helpers import REPO, load_real_palette, tempdir
from umber import buildcmd, registry, syntaxcheck

PROBE = "#123456"


def _names(scope) -> set[str]:
    parts = scope if isinstance(scope, list) else str(scope).split(",")
    return {p.strip() for p in parts}


def _vscode(data: bytes) -> list[str]:
    d = json.loads(data)
    out = [t["settings"]["foreground"] for t in d.get("tokenColors", [])
           if "keyword" in _names(t.get("scope", "")) and "foreground" in t.get("settings", {})]
    sem = d.get("semanticTokenColors", {}).get("keyword")
    if sem is not None:
        out.append(sem if isinstance(sem, str) else sem["foreground"])
    return out


def _sublime(data: bytes) -> list[str]:
    return [r["foreground"] for r in json.loads(data).get("rules", []) if "keyword" in _names(r.get("scope", ""))]


def _zed(data: bytes) -> list[str]:
    return [t["style"]["syntax"]["keyword"]["color"] for t in json.loads(data)["themes"]]


def _helix(data: bytes) -> list[str]:
    d = tomllib.loads(data.decode("utf-8"))
    value = d["keyword"]
    fg = value if isinstance(value, str) else value["fg"]
    return [d.get("palette", {}).get(fg, fg)]


def _tmtheme(data: bytes) -> list[str]:
    return [e["settings"]["foreground"] for e in plistlib.loads(data)["settings"][1:]
            if "keyword" in _names(e.get("scope", "")) and "foreground" in e.get("settings", {})]


def _vim(data: bytes) -> list[str]:  # Keyword links to Statement, which carries the keyword role
    return re.findall(r"^hi Statement\s[^\n]*?guifg=(#[0-9A-Fa-f]{6})", data.decode("utf-8"), re.M)


def _jetbrains(data: bytes) -> list[str]:
    fg = ET.fromstring(data).find("attributes/option[@name='DEFAULT_KEYWORD']/value/option[@name='FOREGROUND']")
    return [] if fg is None else ["#" + fg.get("value")]


def _fish(data: bytes) -> list[str]:
    return ["#" + h for h in re.findall(r"^fish_color_keyword\s+([0-9A-Fa-f]{6})\b", data.decode("utf-8"), re.M)]


def _obsidian(data: bytes) -> list[str]:
    return re.findall(r"--code-keyword:\s*(#[0-9A-Fa-f]{6})", data.decode("utf-8"))


def _opencode(data: bytes) -> list[str]:
    value = json.loads(data).get("theme", {}).get("syntaxKeyword")
    return [] if value is None else [value]


# Format -> the colors of its keyword mappings (exactly the keyword token, never keyword.operator and the like).
KEYWORD_VALUES = {"vscode": _vscode, "sublime": _sublime, "zed": _zed, "helix": _helix, "tmtheme": _tmtheme,
                  "vim": _vim, "jetbrains": _jetbrains, "fish": _fish, "obsidian": _obsidian, "opencode": _opencode}


def keyword_values(fmt: str, data: bytes) -> list[str]:
    return [v.upper()[:7] for v in KEYWORD_VALUES[fmt](data)]


class RolePropagationTest(unittest.TestCase):
    def test_every_syntax_format_has_a_keyword_locator(self):
        self.assertLessEqual(set(registry.SYNTAX_FORMATS), set(KEYWORD_VALUES))

    def test_keyword_role_reaches_every_keyword_mapping(self):
        old = load_real_palette().resolve("syntax.keyword").upper()
        with tempdir() as d:
            root = Path(d) / "repo"
            shutil.copytree(REPO, root, ignore=shutil.ignore_patterns(".git", "dist", "__pycache__"))
            path = root / "palette/umber-calm.toml"
            text = path.read_text(encoding="utf-8").replace("[colors]\n", f'[colors]\nprobe       = "{PROBE}"\n', 1)
            text, n = re.subn(r'^keyword(\s*)= "yellow"$', r'keyword\1= "probe"', text, count=1, flags=re.M)
            self.assertEqual(n, 1, "[roles.syntax] keyword line not found")
            path.write_text(text, encoding="utf-8", newline="\n")
            buildcmd.build(root)
            checked = []
            for port in registry.load_ports(root / "ports.toml"):
                if port.syntax_check is None:
                    continue
                fmt, rel = port.syntax_check["format"], Path(port.output_root) / port.syntax_check["file"]
                before = keyword_values(fmt, (REPO / rel).read_bytes())
                after = keyword_values(fmt, (root / rel).read_bytes())
                self.assertTrue(after, f"{port.id}: no keyword mapping found in {rel}")
                self.assertEqual(len(after), len(before), f"{port.id}: keyword mappings changed in number")
                self.assertEqual(set(before), {old}, f"{port.id}: a keyword mapping does not use syntax.keyword")
                self.assertEqual(set(after), {PROBE}, f"{port.id}: a keyword mapping did not follow syntax.keyword")
                found = {value.upper()[:7] for value in syntaxcheck.extract(fmt, (root / rel).read_bytes())}
                self.assertIn(PROBE, found, f"{port.id}: the syntax check does not see the keyword mapping")
                checked.append(port.id)
            self.assertIn("vscode", checked)

if __name__ == "__main__":
    unittest.main()
