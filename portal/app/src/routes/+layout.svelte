<script lang="ts">
	let { children } = $props();
</script>

<svelte:head>
	<title>Eventra – Müşteri Portali</title>
	<link rel="preconnect" href="https://fonts.googleapis.com" />
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
</svelte:head>

{@render children()}

<style>
	:global(*) { box-sizing: border-box; }
	:global(body) {
		margin: 0;
		font-family: Inter, ui-sans-serif, system-ui, -apple-system, sans-serif;
		background: #080e1c;
		color: #f8fafc;
		-webkit-font-smoothing: antialiased;
	}
	:global(input, select, textarea, button) { font: inherit; }
</style>
