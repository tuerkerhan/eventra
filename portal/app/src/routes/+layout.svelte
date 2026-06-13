<script lang="ts">
	let { children } = $props();
</script>

<svelte:head>
	<title>Eventra – Müşteri Portali</title>
</svelte:head>

<div class="app">
	{@render children()}
</div>

<style>
	:global(*) { box-sizing: border-box; }
	:global(body) {
		margin: 0;
		font-family: Inter, ui-sans-serif, system-ui, sans-serif;
		background: #0f172a;
		color: #f8fafc;
	}
	:global(input, select, textarea, button) { font: inherit; }

	.app { min-height: 100vh; }
</style>
