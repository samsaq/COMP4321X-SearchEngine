<script lang="ts">
	//required theme imports, in required order, for a custom theme
	import "../theme.postcss";
	import "@skeletonlabs/skeleton/styles/all.css";
	import "../app.postcss";

	import { AppShell, Drawer, Modal } from "@skeletonlabs/skeleton";
	import HistoryDrawerNav from "$lib/HistoryDrawerNav.svelte";
</script>

<Modal/>

<Drawer>
	<HistoryDrawerNav />
</Drawer>

<!-- App Shell -->
<AppShell>
	<!-- Page Route Content -->
	<slot />
</AppShell>
