<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import { searchHistory, searchQuery } from "../historyStore";
    import { drawerStore } from "@skeletonlabs/skeleton";

    let searchHistoryLength: number = 0;
    let searchHistoryArray: string[] = [];
    let unSubSearchHistory: () => void;

    //when the user clicks on a search history item, set the search query to that item
    //we'll have the search display component listening to the search query in the store to react
    function setSearchQuery(newQuery: string): (event: MouseEvent) => void {
        return (event: MouseEvent) => {
            searchQuery.set(newQuery);
            drawerStore.close();
        };
    }

    //setup the needed listeners to the store
    onMount(() => {
        unSubSearchHistory = searchHistory.subscribe((arr) => {
            searchHistoryLength = arr.length;
            searchHistoryArray = arr;
        });
    });

    onDestroy(() => {
        unSubSearchHistory();
    });
</script>

{#if searchHistoryLength <= 0}
    <span>You haven't searched anything yet</span>
{:else}
    {#each searchHistoryArray as Query}
        <button
            class="btn variant-filled-primary"
            on:click={setSearchQuery(Query)}
        >
            <span>{searchQuery}</span>
        </button>
    {/each}
{/if}

<style lang="postcss">
</style>
