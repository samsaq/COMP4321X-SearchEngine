<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import SearchBarAndPaginator from "$lib/SearchBarAndPaginator.svelte";
    import { AppBar, ProgressRadial, drawerStore } from "@skeletonlabs/skeleton";
    import type { DrawerSettings } from "@skeletonlabs/skeleton";
    import { searchHistory, searchQuery } from "../../historyStore";
    import 'iconify-icon';

    let curQuery: string = "";
    let waitingForSearch: boolean = true; // to trigger the loading animation

    //function to append used search queries to the history store's searchHistory array
    function appendSearchQuery (newQuery: string) {
        searchHistory.update((arr) => [...arr, newQuery]);
    }

    function updateSearchQuery (newQuery: string) {
        searchQuery.set(newQuery);
    }

</script>

<main>

    <AppBar background = "variant-ghost-error">
        <svelte:fragment slot="lead">
            <a href="/">
                <iconify-icon icon="ic:outline-home" height=2rem width=2rem style="color: #000000"></iconify-icon>
            </a>
        </svelte:fragment>
        <svelte:fragment slot= "trail">
            <!--We'll put the hamburger for the history menu here-->
            <button on:click="{() => drawerStore.open()}">
                <img src="/history-linear.svg" alt="History" />
            </button>
        </svelte:fragment>
    </AppBar>

</main>

<style>

    main {
        background-color: rgb(var(--color-error-500));
        margin: 0px;
        height: 100vh;
        width: 100vw;
        overflow: hidden;
    }

</style>