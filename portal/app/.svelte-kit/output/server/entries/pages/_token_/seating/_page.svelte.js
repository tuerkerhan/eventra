import { C as escape_html, S as attr, a as head, c as stringify, l as unsubscribe_stores, r as derived, s as store_get, t as attr_class } from "../../../../chunks/server.js";
import { t as page } from "../../../../chunks/stores.js";
//#region src/routes/[token]/seating/+page.svelte
function _page($$renderer, $$props) {
	$$renderer.component(($$renderer) => {
		var $$store_subs;
		const token = derived(() => store_get($$store_subs ??= {}, "$page", page).params.token);
		derived(() => store_get($$store_subs ??= {}, "$page", page).url.searchParams.get("layout"));
		let saving = false;
		let saved = false;
		let printMode = false;
		head("ghgfhu", $$renderer, ($$renderer) => {
			$$renderer.title(($$renderer) => {
				$$renderer.push(`<title>Oturma Düzeni</title>`);
			});
		});
		$$renderer.push(`<main${attr_class("seating-shell svelte-ghgfhu", void 0, { "print-mode": printMode })}><header class="seating-header no-print svelte-ghgfhu"><a class="back-link svelte-ghgfhu"${attr("href", `/${stringify(token())}`)}><img src="/ikon.png" alt="" class="back-logo svelte-ghgfhu"/> ← Portale Dön</a> <h1 class="svelte-ghgfhu">🪑 Oturma Düzeni</h1> <div class="header-actions svelte-ghgfhu"><button type="button"${attr("disabled", saving, true)}${attr_class("save-btn svelte-ghgfhu", void 0, { "saved": saved })}>${escape_html("Kaydet")}</button> <button type="button" class="print-btn svelte-ghgfhu">🖨 Yazdır</button></div></header> `);
		$$renderer.push("<!--[0-->");
		$$renderer.push(`<div class="loading svelte-ghgfhu">Yükleniyor…</div>`);
		$$renderer.push(`<!--]--></main>`);
		if ($$store_subs) unsubscribe_stores($$store_subs);
	});
}
//#endregion
export { _page as default };
