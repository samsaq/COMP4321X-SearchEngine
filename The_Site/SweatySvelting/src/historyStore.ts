import { writable } from 'svelte/store';
import type { Writable } from 'svelte/store';

export const searchHistory: Writable<string[]> = writable([]);
export const searchQuery: Writable<string> = writable('');