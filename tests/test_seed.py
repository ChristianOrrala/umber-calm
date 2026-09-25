import json, unittest
from tests.helpers import REPO, load_real_palette
from umber import buildcmd, checks

KEYS = ["schema_version", "name", "slug", "palette_version", "release", "license", "author", "homepage",
        "colors", "ansi", "roles", "tints"]

class SeedTest(unittest.TestCase):
    def test_json_export_matches_the_palette_exactly(self):
        pal = load_real_palette()
        data = json.loads((REPO / "ports/json/umber-calm.json").read_text(encoding="utf-8"))
        self.assertEqual(list(data), KEYS)
        for key in KEYS[:8]:
            self.assertEqual(data[key], pal.meta[key], key)
        self.assertEqual(data["colors"], pal.colors)
        self.assertEqual(data["ansi"], pal.ansi)
        self.assertEqual(data["roles"], {c: {r: pal.colors[n] for r, n in roles.items()} for c, roles in pal.roles.items()})
        self.assertEqual(data["tints"], pal.tints)

    def test_repository_is_built_and_clean(self):
        self.assertEqual(buildcmd.build(REPO), [], "run: python3 tools/build.py")
        self.assertEqual(checks.run(REPO), [])

if __name__ == "__main__":
    unittest.main()
