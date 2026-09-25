import unittest
from tests.helpers import load_real_palette
from umber import template

P = load_real_palette()
r = lambda text, **kw: template.render(text, P, source="t.tmpl", **kw)

class TemplateTest(unittest.TestCase):
    def test_refs_and_chains(self):
        self.assertEqual(r("fg={{ blue }}"), "fg=#88B0B4")
        self.assertEqual(r("{{blue|nohash|lower}}"), "88b0b4")
        self.assertEqual(r("{{ yellow | blend(bg, tint.search) }}"), "#423C2E")
        self.assertEqual(r("{{ syntax.keyword | alpha(4D) }}"), "#DCC07D4D")

    def test_literal_braces(self):
        self.assertEqual(r('{{ "{{" }} x'), "{{ x")

    def test_extra_values(self):
        self.assertEqual(r("{{ meta.template }}", extra={"meta.template": "templates/x.tmpl"}), "templates/x.tmpl")

    def test_errors_carry_location(self):
        with self.assertRaisesRegex(template.TemplateError, r"t\.tmpl:2: unknown reference 'nope'"):
            r("ok\n{{ nope }}")
        with self.assertRaisesRegex(template.TemplateError, r"t\.tmpl:1: unknown filter"):
            r("{{ blue | shout }}")
        with self.assertRaisesRegex(template.TemplateError, r"t\.tmpl:3: unclosed"):
            r("a\nb\nc {{ blue")
        with self.assertRaisesRegex(template.TemplateError, "empty expression"):
            r("{{   }}")

    def test_crlf_template_renders_lf(self):
        self.assertEqual(r("a\r\nb {{ red }}\r\n"), "a\nb #E08374\n")

    def test_unicode_passthrough(self):
        self.assertEqual(r("— {{ meta.name }} —"), "— Umber Calm —")

    def test_blends_are_listed_with_lines(self):
        text = "a={{ yellow | blend(bg, tint.search) }}\nb={{ blue }}\nc={{ green | blend(bg, 0.22) | lower }}\n"
        self.assertEqual(template.blends(text, P, source="t.tmpl"), [(1, "#423C2E"), (3, "#3E402F")])
        self.assertEqual(template.blends('{{ "{{" }} x', P, source="t.tmpl"), [])

    def test_preserves_trailing_text_exactly(self):
        self.assertEqual(r("{{ bg }}  \n\n"), "#201F1D  \n\n")

if __name__ == "__main__":
    unittest.main()
