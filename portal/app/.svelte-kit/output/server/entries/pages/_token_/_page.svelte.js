import "../../../chunks/internal.js";
import { C as escape_html, a as head, c as stringify, i as ensure_array_like, l as unsubscribe_stores, n as attr_style, r as derived, s as store_get, t as attr_class } from "../../../chunks/server.js";
import "../../../chunks/client.js";
import { t as page } from "../../../chunks/stores.js";
//#region src/routes/[token]/+page.svelte
function _page($$renderer, $$props) {
	$$renderer.component(($$renderer) => {
		var $$store_subs;
		derived(() => store_get($$store_subs ??= {}, "$page", page).params.token);
		let mounted = false;
		const sparkles = Array.from({ length: 22 }, (_, i) => ({
			id: i,
			left: Math.random() * 100,
			delay: Math.random() * 8,
			duration: 6 + Math.random() * 8,
			size: 4 + Math.random() * 6,
			opacity: .2 + Math.random() * .5
		}));
		head("1ti142y", $$renderer, ($$renderer) => {
			$$renderer.title(($$renderer) => {
				$$renderer.push(`<title>${escape_html("Müşteri Portali")} — Eventra</title>`);
			});
			$$renderer.push(`<link href="https://fonts.googleapis.com/css2?family=Great+Vibes&amp;family=Cormorant+Garamond:ital,wght@0,400;0,700;1,400&amp;display=swap" rel="stylesheet" class="svelte-1ti142y"/>`);
		});
		$$renderer.push(`<div class="sparkle-layer svelte-1ti142y" aria-hidden="true"><!--[-->`);
		const each_array = ensure_array_like(sparkles);
		for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
			let s = each_array[$$index];
			$$renderer.push(`<div class="sparkle svelte-1ti142y"${attr_style(` left:${stringify(s.left)}%; animation-delay:${stringify(s.delay)}s; animation-duration:${stringify(s.duration)}s; width:${stringify(s.size)}px; height:${stringify(s.size)}px; opacity:${stringify(s.opacity)}; `)}></div>`);
		}
		$$renderer.push(`<!--]--></div> <div${attr_class("portal-shell svelte-1ti142y", void 0, { "mounted": mounted })}><header class="portal-header svelte-1ti142y"><div class="header-inner svelte-1ti142y"><div class="brand-block svelte-1ti142y"><div class="brand-logo-wrap svelte-1ti142y"><img src="/ikon.png" alt="Logo" class="brand-logo svelte-1ti142y"/> <div class="logo-glow svelte-1ti142y"></div></div> <div class="brand-text svelte-1ti142y"><img src="/crown-icon.png" alt="" class="header-crown svelte-1ti142y"/> <img src="/logo-yatay.png" alt="Eventra" class="header-wordmark svelte-1ti142y"/></div></div> `);
		$$renderer.push("<!--[-1-->");
		$$renderer.push(`<!--]--></div></header> <main class="portal-main svelte-1ti142y">`);
		$$renderer.push("<!--[0-->");
		$$renderer.push(`<div class="state-card animate-in svelte-1ti142y"><div class="spinner-ring svelte-1ti142y"></div> <p class="state-text svelte-1ti142y">Yükleniyor…</p></div>`);
		$$renderer.push(`<!--]--></main> <footer class="portal-footer svelte-1ti142y"><img src="/logo-dikey.png" alt="Eventra" class="footer-logo svelte-1ti142y"/> <p class="svelte-1ti142y">Bu portal <strong class="svelte-1ti142y">Eventra</strong> etkinlik yönetim sistemi tarafından oluşturulmuştur.</p></footer></div>`);
		if ($$store_subs) unsubscribe_stores($$store_subs);
	});
}
//#endregion
export { _page as default };
