export const manifest = (() => {
function __memo(fn) {
	let value;
	return () => value ??= (value = fn());
}

return {
	appDir: "_app",
	appPath: "_app",
	assets: new Set(["ayarlar-icon.png","contract-icon.png","crown-icon.png","dashboard-icon.png","ikon.png","logo-dikey.png","logo-yatay.png","musteriler-icon.png","salon-duzeni.png","takvim-icon.png"]),
	mimeTypes: {".png":"image/png"},
	_: {
		client: {start:"_app/immutable/entry/start.5ymuwPDo.js",app:"_app/immutable/entry/app.CBnpTGvU.js",imports:["_app/immutable/entry/start.5ymuwPDo.js","_app/immutable/chunks/C5gJBUl_.js","_app/immutable/chunks/BN-v7L_0.js","_app/immutable/entry/app.CBnpTGvU.js","_app/immutable/chunks/BN-v7L_0.js","_app/immutable/chunks/kNaey6uv.js","_app/immutable/chunks/xihTtKlq.js"],stylesheets:[],fonts:[],uses_env_dynamic_public:false},
		nodes: [
			__memo(() => import('./nodes/0.js')),
			__memo(() => import('./nodes/1.js')),
			__memo(() => import('./nodes/2.js')),
			__memo(() => import('./nodes/3.js'))
		],
		remotes: {
			
		},
		routes: [
			{
				id: "/[token]",
				pattern: /^\/([^/]+?)\/?$/,
				params: [{"name":"token","optional":false,"rest":false,"chained":false}],
				page: { layouts: [0,], errors: [1,], leaf: 2 },
				endpoint: null
			},
			{
				id: "/[token]/seating",
				pattern: /^\/([^/]+?)\/seating\/?$/,
				params: [{"name":"token","optional":false,"rest":false,"chained":false}],
				page: { layouts: [0,], errors: [1,], leaf: 3 },
				endpoint: null
			}
		],
		prerendered_routes: new Set([]),
		matchers: async () => {
			
			return {  };
		},
		server_assets: {}
	}
}
})();
