# Joblens Technical Design

## 1. Architecture Direction

Joblens starts as a controlled fork-style copy of the current `obsidian-clipper` working tree. The first implementation keeps the proven Zhilian harvesting behavior intact, then removes unrelated Web Clipper features in stages.

The intended long-term architecture is:

```text
content bootstrap
  -> Zhilian Harvester
  -> Boss Harvester
  -> shared download/export helpers

background service worker
  -> file download
  -> detail tab orchestration
```

## 2. Project Boundary

Source project:

```text
D:\Projects\obsidian-clipper
```

New project:

```text
/home/xstars/programs/joblens
```

The source project is read-only for this migration. All custom changes happen in Joblens.

## 3. Bootstrap Strategy

The first Joblens version copies the existing codebase while excluding generated and heavy directories:

- `.git`
- `node_modules`
- `dist`
- `builds`
- browser-specific generated output directories

This preserves current harvesting logic while avoiding historical build artifacts.

## 4. Current MVP Implementation

The first customized version changes product identity only:

- `package.json` package name becomes `joblens`.
- Extension display name becomes `Joblens`.
- README becomes Joblens-specific.
- PRD and technical design live in `docs/`.

The first version kept reader/highlighter/settings code in the repository for reference, but Chrome production builds no longer expose those entrypoints. Content-script imports are now being removed in small verified stages.

## 5. Slimming Stages

### Completed: Stage 1 Build And Manifest Slimming

Implemented on 2026-04-30:

- Chrome build now emits only `content.js`, `background.js`, `browser-polyfill.min.js`, `manifest.json`, and icons.
- Webpack output now uses `clean: true`, so stale reader/highlighter/popup/settings files are removed from `dist`.
- Chrome manifest no longer exposes popup, settings, side panel, reader, highlighter, locale, or command entries.
- Chrome zip output is `builds/joblens-1.10.0-chrome.zip`.

Current build size:

- `dist`: about `500K`
- Chrome zip: about `126K`

Known remaining warning:

- `content.js` is still about `403K`, mainly because the monolithic content script still imports shared Web Clipper utilities such as Defuddle. This will be addressed in later content slimming stages.

### Completed: Stage 2 Content Script Import Slimming

Implemented on 2026-04-30:

- Removed the legacy `getPageContent` message branch from `src/content.ts`.
- Removed content-script imports for Defuddle, shadow DOM flattening, domain parsing, highlighter loading, storage settings, iframe resize helpers, generic clipping helpers, and generic file helpers.
- Kept Joblens-specific message actions:
  - `ping`
  - `parseZhilianDetail`
  - `auto-scroll-and-save`
- Limited icon copying to PNG files only, so TypeScript icon helper files no longer ship in `dist/icons`.

Current build size:

- `content.js`: about `93.6K`
- Chrome zip: about `43.9K`

Validation:

- `npx tsc --noEmit --module es2020`: passed.
- `npm run build:chrome`: passed.
- Webpack size warning is gone.

### Completed: Stage 3 Chrome-Only Packaging Slimming

Implemented on 2026-05-01:

- Removed Firefox and Safari npm scripts from the Joblens build surface.
- Simplified webpack output selection to Chrome-only `dist` and `dev` directories.
- Removed Firefox and Safari manifest source files.
- Removed the Safari type dependency from `package.json`.
- Removed the inherited Xcode/Safari app project because Joblens MVP explicitly excludes Safari support.

Validation:

- `npx tsc --noEmit --module es2020`: passed.
- `npm run build:chrome`: passed.

### Completed: Stage 1 Build Entrypoint Slimming

Modify webpack so Chrome production builds only the recruitment-required entrypoints:

- `content`
- `background`
- minimal shared style if still needed

Disable build output for:

- popup
- settings
- highlights
- reader-page
- reader-script

### Completed: Stage 2 Manifest Slimming

Remove or disable:

- popup action page
- side panel
- options UI
- reader/highlighter web accessible resources
- reader/highlighter commands

Keep:

- content script injection
- background service worker
- downloads
- scripting
- storage
- host permissions needed by target platforms

### Stage 3: Runtime Code Slimming

Remove from background:

- YouTube reader request rules
- highlighter state
- reader mode state
- side panel lifecycle
- generic context-menu clipping

Keep:

- download message handling
- detail tab orchestration
- harvester messages

### Stage 4: Harvester Split

Move platform-specific code out of the monolithic content script:

- `src/harvesters/zhilian.ts`
- `src/harvesters/boss.ts`
- `src/shared/download.ts`
- `src/shared/platform.ts`

Zhilian must remain behavior-compatible with current commands.

### Stage 5: Dependency Cleanup

After unused entrypoints are disconnected, remove unused dependencies and dev scripts.

Candidates:

- `highlight.js`
- `lucide`
- `dompurify`
- `linkedom`
- `lz-string`
- `defuddle`, only if raw/document extraction no longer uses it

## 6. Commands

Install dependencies:

```bash
npm install
```

Static type check:

```bash
npx tsc --noEmit --module es2020
```

Build Chrome extension:

```bash
npm run build:chrome
```

## 7. Acceptance Tests

- `npx tsc --noEmit --module es2020` passes.
- `npm run build:chrome` passes.
- Chrome can load `/home/xstars/programs/joblens/dist`.
- Zhilian one-page test command generates `ZHILIAN_TEST_*.md`.
- Zhilian formal command generates `ZHILIAN_*.md`.
- `C++培训讲师` works with `clipper_keyword_b64u`.
- Archive script still moves formal outputs into artifacts.

## 8. Future Boss Harvester

Boss support must be a separate harvester, not a reuse of the Zhilian parser.

Planned first Boss scope:

- detect `zhipin.com` search result pages
- scan `/job_detail/` links
- parse visible card fields
- use `boss_decrypt` for obfuscated salary text
- output `BOSS_<keyword>_<timestamp>.md`

Boss detail-page harvesting is deferred until list harvesting is stable.
