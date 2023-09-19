<script lang="ts">
	//required theme imports, in required order, for a custom theme
	import "../app.postcss";

	import { AppShell, Drawer, Modal, initializeStores } from "@skeletonlabs/skeleton";
	import HistoryDrawerNav from "$lib/HistoryDrawerNav.svelte";

	initializeStores();
</script>

<Modal rounded="rounded-none" buttonNeutral="rounded-none border-solid"/>

<Drawer width="w-1/4" rounded="rounded-none">
	<HistoryDrawerNav />
</Drawer>

<!-- App Shell -->
<AppShell>
	<!-- Page Route Content -->
	<slot />
</AppShell>
