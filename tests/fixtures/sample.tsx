// Umber Calm sample: every syntax role in one screen.
import * as fs from "node:fs/promises";

/** A palette entry. @param name color name */
interface Swatch { name: string; hex: string }
enum Tier { Supported = "supported", Experimental = "experimental" }
const MAX_RATIO = 21;
const pattern = /^#[0-9A-F]{6}$/i;

@sealed
export class Palette {
  constructor(private readonly path: string) {}
  async load(strict = true): Promise<Swatch[]> {
    const raw = await fs.readFile(this.path, "utf8");
    if (!pattern.test(raw)) throw new Error(`bad hex\n`);
    // legacy: return [];
    return raw.split("\n").map((name) => ({ name, hex: name.trim() }));
  }
}

export const view = <Swatch name="bg" hex={Palette.name} />;
