<script lang="ts">
	let { children } = $props();
</script>

<svelte:head>
	<title>Eventra Admin</title>
</svelte:head>

{@render children()}

<style>
	:global(*) { box-sizing: border-box; }
	:global(body) {
		margin: 0;
		font-family: Inter, ui-sans-serif, system-ui, sans-serif;
		background: #0f172a;
		color: #f8fafc;
	}
	:global(input, select, textarea, button) { font: inherit; }
</style>
