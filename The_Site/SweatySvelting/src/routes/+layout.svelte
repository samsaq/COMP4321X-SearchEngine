<script lang="ts">
	//required theme imports, in required order, for a custom theme
	import "../app.postcss";

	import { AppShell, Drawer, Modal, initializeStores } from "@skeletonlabs/skeleton";
	import HistoryDrawerNav from "$lib/HistoryDrawerNav.svelte";

	initializeStores();
</script>

<Modal class= "text-black" rounded="rounded-none border-solid" buttonNeutral="rounded-none" background="bg-gray-100"/>

<Drawer width="w-1/4 min-w-[300px]" rounded="rounded-none" bgDrawer="bg-gray-300 bg-opacity-75">
	<HistoryDrawerNav />
</Drawer>

<!-- App Shell -->
<AppShell>
	<!-- Page Route Content -->
	<slot />
</AppShell>
