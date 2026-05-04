# Joblens PRD

## 1. Product Summary

Joblens is a recruitment intelligence browser extension. It helps the user and Agent collect job-platform data, export it as files, and feed platform-specific knowledge bases for later analysis and consulting.

The first version focuses on Zhilian because the existing harvesting chain has already been tested with real data. Boss support is planned but not part of the first MVP implementation.

## 2. Goals

- Turn the existing recruitment harvesting work into a dedicated product instead of continuing to customize the general Obsidian Web Clipper.
- Preserve the validated Zhilian harvesting workflow.
- Create a clean project home for future platform-specific harvesters.
- Keep outputs auditable and easy to archive.

## 3. Users

- **Human operator**: opens Chrome, refreshes the extension, checks generated files, and reviews data quality.
- **Agent operator**: launches Chrome commands, verifies downloaded results, archives formal outputs, and maintains logs.
- **Future consulting system**: consumes the harvested intelligence to support job-search advice.

## 4. MVP Scope

### Included

- Zhilian keyword/category discovery.
- Zhilian job list harvesting.
- Automatic pagination until the configured page limit or end of results.
- One-page test mode.
- Detail-page test mode for limited samples.
- Markdown export.
- Existing Raw HTML / Raw JSON test outputs when enabled by current parameters.
- Agent-side formal archival into sandbox `artifacts`.

### Excluded

- General-purpose Obsidian clipping.
- Reader mode.
- Highlighting.
- Generic template authoring.
- Settings UI redesign.
- Firefox and Safari support.
- Boss job list harvesting in MVP.
- Full recruiting-consultation Q&A system.

## 5. Output Expectations

Test outputs remain in:

```text
D:\Downloads
```

Formal Zhilian outputs are archived by Agent into:

```text
/home/xstars/zhilian_intelligence_sandbox/artifacts
```

Future Boss outputs should archive into:

```text
/home/xstars/boss_intelligence_sandbox/artifacts
```

## 6. Success Criteria

- Chrome can load the Joblens `dist` directory as an unpacked extension.
- Zhilian category discovery still generates the expected keyword document.
- Zhilian list harvesting still generates `ZHILIAN_<keyword>_<timestamp>.md`.
- Special keywords such as `C++培训讲师` preserve the correct keyword in output file names and body text.
- Existing archive scripts remain usable.
- The original `D:\Projects\obsidian-clipper` is not modified as part of Joblens implementation.
- The MVP build and source packaging remain Chrome-only until Firefox or Safari support becomes an explicit priority.

## 7. Risks

- The inherited codebase still contains unrelated Web Clipper modules, but non-Chrome packaging has been removed from the active project surface.
- Removing entrypoints too early may break build output.
- Zhilian harvesting logic is currently concentrated in `content.ts`, so refactoring must be staged.
- Boss support will need a separate parser because BOSS page structure and anti-automation behavior differ from Zhilian.
