#!/usr/bin/env bash
set -euo pipefail

CHIMERA_ASSET_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CHIMERA_REVISION=e33221d006f44c78849210eb29dd1eb9755dc78e
CHIMERA_BUILD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/chimera-build.XXXXXXXX")"
printf 'Building upstream %s in %s\n' "$CHIMERA_REVISION" "$CHIMERA_BUILD_DIR"
git clone --no-checkout https://github.com/jamesondh/chimera-vocal-synth.git "$CHIMERA_BUILD_DIR/upstream"
git -C "$CHIMERA_BUILD_DIR/upstream" checkout --detach "$CHIMERA_REVISION"
rustup toolchain install 1.99.1 --profile minimal --target wasm32-unknown-unknown
cargo +1.99.1 build --manifest-path "$CHIMERA_BUILD_DIR/upstream/Cargo.toml" --locked --release --target wasm32-unknown-unknown -p chimera-wasm
node --input-type=module - "$CHIMERA_BUILD_DIR/upstream" "$CHIMERA_ASSET_DIR" <<'NODE'
import { readFileSync, writeFileSync, copyFileSync } from 'node:fs';
import { stripTypeScriptTypes } from 'node:module';
import { createHash } from 'node:crypto';
import { join } from 'node:path';
const [src, dest] = process.argv.slice(2);
copyFileSync(join(src, 'target/wasm32-unknown-unknown/release/chimera_wasm.wasm'), join(dest, 'chimera.wasm'));
copyFileSync(join(src, 'LICENSE'), join(dest, 'CHIMERA-LICENSE.txt'));
copyFileSync(join(src, 'public/data/CMUDICT-LICENSE.txt'), join(dest, 'CMUDICT-LICENSE.txt'));
copyFileSync(join(src, 'public/data/cmudict.txt.gz'), join(dest, 'cmudict.txt.gz'));
writeFileSync(join(dest, 'wire.mjs'), stripTypeScriptTypes(readFileSync(join(src, 'src/wasm/wire.ts'), 'utf8'), {mode:'strip'}));
for (const name of ['chimera.wasm','wire.mjs','cmudict.txt.gz']) {
  const data = readFileSync(join(dest, name));
  console.log(JSON.stringify({name, bytes:data.length, sha256:createHash('sha256').update(data).digest('hex')}));
}
NODE
printf 'Built assets in %s. Source retained at %s. Existing verification records describe the original measured run.\n' "$CHIMERA_ASSET_DIR" "$CHIMERA_BUILD_DIR"
