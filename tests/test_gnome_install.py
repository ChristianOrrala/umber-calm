import json, os, shutil, stat, subprocess, tempfile, unittest
from pathlib import Path
from tests.helpers import REPO
from umber import buildcmd

SCRIPT = REPO / "ports/gnome-terminal/install.sh"
UUID = "b6885571-c238-4b0d-8904-5a8531dfdbae"
BASE = "/org/gnome/terminal/legacy/profiles:"
FAKE_DCONF = r'''#!/usr/bin/env python3
"""Minimal dconf stand-in backed by a JSON file ($FAKE_DCONF). Rejects values real dconf could not parse."""
import json, os, sys
store = os.environ["FAKE_DCONF"]
data = json.load(open(store, encoding="utf-8")) if os.path.exists(store) else {}
cmd, args = sys.argv[1], sys.argv[2:]
if cmd == "read":
    if args[0] in data:
        print(data[args[0]])
elif cmd == "write":
    key, value = args
    typed = value in ("true", "false") or value == "@as []" or (value.startswith("'") and value.endswith("'")) \
        or (value.startswith("['") and value.endswith("']"))
    if not typed:
        sys.exit(f"error: 0-{len(value)}:unable to infer type: {value}")
    data[key] = value
elif cmd == "reset" and args[0] == "-f":
    data = {k: v for k, v in data.items() if not k.startswith(args[1])}
elif cmd == "list":
    kids = {k[len(args[0]):].split("/")[0] + ("/" if "/" in k[len(args[0]):] else "")
            for k in data if k.startswith(args[0])}
    print("\n".join(sorted(kids)))
else:
    sys.exit(f"fake dconf: unsupported command {sys.argv[1:]}")
json.dump(data, open(store, "w", encoding="utf-8"), indent=1, sort_keys=True)
'''


def setUpModule():
    buildcmd.build(REPO)


@unittest.skipIf(os.name == "nt" or shutil.which("bash") is None, "needs a POSIX shell")
class GnomeInstallTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        fake = self.tmp / "bin" / "dconf"
        fake.parent.mkdir()
        fake.write_text(FAKE_DCONF, encoding="utf-8")
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        self.store = self.tmp / "dconf.json"
        self.env = {**os.environ, "FAKE_DCONF": str(self.store), "PATH": f"{fake.parent}{os.pathsep}{os.environ['PATH']}"}

    def seed(self, data):
        self.store.write_text(json.dumps(data), encoding="utf-8")

    def state(self):
        return json.loads(self.store.read_text(encoding="utf-8")) if self.store.exists() else {}

    def run_script(self, *args):
        return subprocess.run(["bash", str(SCRIPT), *args], env=self.env, capture_output=True, text=True)

    def test_fresh_install_keeps_gnome_default_profile_visible(self):
        r = self.run_script()
        self.assertEqual(r.returncode, 0, r.stderr)
        s = self.state()
        self.assertEqual(s[f"{BASE}/list"], f"['b1dcc9dd-5262-4d8d-a863-c897e6d979b9', '{UUID}']")
        self.assertEqual(s[f"{BASE}/:{UUID}/visible-name"], "'Umber Calm'")
        self.assertEqual(s[f"{BASE}/:{UUID}/palette"].count("'#"), 16)
        self.assertIn("--remove", r.stdout)

    def test_reinstall_is_idempotent(self):
        self.run_script()
        first = self.state()
        r = self.run_script()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.state(), first)

    def test_same_name_user_profile_is_left_untouched(self):
        mine = "11111111-2222-3333-4444-555555555555"
        seed = {f"{BASE}/list": f"['{mine}']", f"{BASE}/default": f"'{mine}'",
                f"{BASE}/:{mine}/visible-name": "'Umber Calm'", f"{BASE}/:{mine}/background-color": "'#FFFFFF'"}
        self.seed(seed)
        r = self.run_script()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("left untouched", r.stderr)
        s = self.state()
        for key, value in seed.items():
            if key != f"{BASE}/list":
                self.assertEqual(s[key], value)
        self.assertEqual(s[f"{BASE}/list"], f"['{mine}', '{UUID}']")

    def test_remove_when_default_moves_default_first(self):
        other = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        self.seed({f"{BASE}/list": f"['{other}']"})
        self.run_script()
        data = self.state(); data[f"{BASE}/default"] = f"'{UUID}'"; self.seed(data)
        r = self.run_script("--remove")
        self.assertEqual(r.returncode, 0, r.stderr)
        s = self.state()
        self.assertEqual(s[f"{BASE}/default"], f"'{other}'")
        self.assertEqual(s[f"{BASE}/list"], f"['{other}']")
        self.assertFalse([k for k in s if k.startswith(f"{BASE}/:{UUID}/")])

    def test_remove_refuses_when_it_is_the_only_profile(self):
        self.seed({f"{BASE}/list": f"['{UUID}']", f"{BASE}/default": f"'{UUID}'", f"{BASE}/:{UUID}/visible-name": "'Umber Calm'"})
        before = self.state()
        r = self.run_script("--remove")
        self.assertEqual(r.returncode, 1)
        self.assertIn("only profile", r.stderr)
        self.assertEqual(self.state(), before)

    def test_remove_when_absent_changes_nothing(self):
        self.seed({f"{BASE}/list": "@as []"})
        r = self.run_script("--remove")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("not installed", r.stdout)
        self.assertEqual(self.state(), {f"{BASE}/list": "@as []"})

    def test_empty_typed_list_is_handled(self):
        self.seed({f"{BASE}/list": "@as []"})
        r = self.run_script()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.state()[f"{BASE}/list"], f"['{UUID}']")

if __name__ == "__main__":
    unittest.main()
