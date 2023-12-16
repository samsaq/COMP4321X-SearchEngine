<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import { searchHistory, searchQuery } from "../historyStore";
    import { getDrawerStore} from "@skeletonlabs/skeleton";

    const drawerStore = getDrawerStore();
    let searchHistoryLength: number = 0;
    let searchHistoryArray: string[] = [];
    let unSubSearchHistory: () => void;
    let valueSingle: string = 'selectedQuery';

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

<div class="flex flex-col justify-start items-center drawerContainer">
        <span class="text-xl py-4 underline-offset-4 underline search-history-hero">Search History</span>
        <nav class="list-nav">
            <ul>
                {#each searchHistoryArray as Query}
                    <li class= "flex justify-center py-2">
                        <button
                            class="btn variant-ringed-primary underline-offset-2 decoration-yellow-500 text-black"
                            on:click={setSearchQuery(Query)}>{Query}</button
                        >
                    </li>
                {/each}
            </ul>
        </nav>
</div>

<style lang="postcss">

    .drawerContainer {
        font-family: "Rubik", sans-serif;
    }

    .search-history-hero{
        font-family: "Lobster", cursive;
        font-size: 3rem;
        padding-bottom: 2rem;
        text-decoration: rgb(var(--color-primary-500)) underline;
        color: rgba(0, 0, 0, 0.75);
    }

</style>
