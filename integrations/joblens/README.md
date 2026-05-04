# Joblens

Joblens is a custom browser extension for collecting recruitment intelligence from job platforms.

This project starts from the proven Obsidian Clipper codebase, but its product direction is different: Joblens is not a general web clipper. It is a focused harvesting tool for job categories, job list pages, and eventually job detail pages.

## Current Focus

- Zhilian job category discovery.
- Zhilian job list harvesting with automatic pagination.
- Zhilian test harvesting for one-page checks.
- Zhilian detail-page test harvesting.
- Markdown export to browser downloads.
- Agent-side archival into platform sandbox artifacts.

## Planned Direction

- Keep Zhilian harvesting stable as the first MVP.
- Add a separate Boss Harvester later.
- Reduce or remove unrelated Web Clipper features such as reader mode, highlights, generic templates, side panel, broad settings UI, and non-Chrome packaging.

## Project Location

```bash
/home/xstars/programs/joblens
```

## Build

Install dependencies first when the project is created on a fresh machine:

```bash
npm install
```

Build the Chrome extension:

```bash
npm run build:chrome
```

The unpacked extension output is:

```bash
dist
```

## Documentation

- [PRD](docs/PRD.md)
- [Technical Design](docs/TECH_DESIGN.md)
- [Automation Guide](docs/zhilian-command-guide.md)

## Relationship To Obsidian Clipper

The original `D:\Projects\obsidian-clipper` project remains a historical source and fallback reference. Joblens is the new customization project and should be developed independently.
