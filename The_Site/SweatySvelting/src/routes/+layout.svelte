<script lang="ts">
	//required theme imports, in required order, for a custom theme
	import "../theme.postcss";
	import "@skeletonlabs/skeleton/styles/all.css";
	import "../app.postcss";

	import { AppShell, AppBar } from "@skeletonlabs/skeleton";
	import PixelBackground from "../lib/PixelBackground.svelte";
</script>

<!-- App Shell -->
<AppShell>
	<!-- Page Route Content -->
	<slot />
</AppShell>
