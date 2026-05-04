import browser from './browser-polyfill';
import { sanitizeFileName } from '../utils/string-utils';
import { generateFrontmatter as generateFrontmatterCore } from './shared';
import { Template, Property } from '../types/types';
import { generalSettings, incrementStat } from './storage-utils';
import { copyToClipboard } from './clipboard-utils';
import { getMessage } from './i18n';

export async function generateFrontmatter(properties: Property[]): Promise<string> {
        const typeMap: Record<string, string> = {};
        for (const pt of generalSettings.propertyTypes) {
                typeMap[pt.name] = pt.type;
        }
        return generateFrontmatterCore(properties, typeMap);
}

export function generateObsidianUrl(
        noteName: string,
        path: string,
        vault: string,
        behavior: string,
): string {
        let obsidianUrl: string;
        const isDailyNote = behavior === 'append-daily' || behavior === 'prepend-daily';

        if (isDailyNote) {
                obsidianUrl = 'obsidian://daily?';
        } else {
                if (path && !path.endsWith('/')) {
                        path += '/';
                }
                const formattedNoteName = sanitizeFileName(noteName);
                obsidianUrl = 'obsidian://new?file=' + encodeURIComponent(path + formattedNoteName);
        }

        if (behavior.startsWith('append')) {
                obsidianUrl += '&append=true';
        } else if (behavior.startsWith('prepend')) {
                obsidianUrl += '&prepend=true';
        } else if (behavior === 'overwrite') {
                obsidianUrl += '&overwrite=true';
        }

        if (vault) {
                obsidianUrl += '&vault=' + encodeURIComponent(vault);
        }
        
        if (generalSettings.silentOpen) {
                obsidianUrl += '&silent=true';
        }

        return obsidianUrl;
}

function openObsidianUrl(url: string): void {
        browser.runtime.sendMessage({
                action: 'openObsidianUrl',
                url: url
        }).catch((error) => {
                console.log('[Clipper] background delegation');
        });
}

async function tryClipboardWrite(fileContent: string, obsidianUrl: string): Promise<void> {
        const success = await copyToClipboard(fileContent);
        if (success) {
                obsidianUrl += '&clipboard&content=' + encodeURIComponent(getMessage('clipboardError', 'https://help.obsidian.md/web-clipper/troubleshoot'));
                openObsidianUrl(obsidianUrl);
        } else {
                obsidianUrl += '&content=' + encodeURIComponent(fileContent);
                openObsidianUrl(obsidianUrl);
        }
}

export async function saveToObsidian(
        fileContent: string,
        noteName: string,
        path: string,
        vault: string,
        behavior: Template['behavior'],
): Promise<void> {
        const obsidianUrl = generateObsidianUrl(noteName, path, vault, behavior);

        if (generalSettings.legacyMode) {
                const finalUrl = obsidianUrl + '&content=' + encodeURIComponent(fileContent);
                openObsidianUrl(finalUrl);
        } else {
                await tryClipboardWrite(fileContent, obsidianUrl);
        }
}
