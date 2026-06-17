import { writable } from 'svelte/store';

// '' = "Tüm Salonlar" (filtre yok)
export const activeSalonId = writable<string>('');

export function initActiveSalon() {
	const saved = localStorage.getItem('eventra-active-salon');
	if (saved) activeSalonId.set(saved);
	activeSalonId.subscribe((v) => {
		localStorage.setItem('eventra-active-salon', v);
	});
}
