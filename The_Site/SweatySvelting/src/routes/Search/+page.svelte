<script lang="ts">

    import { onMount, onDestroy } from "svelte";
    import SearchBarAndPaginator from "$lib/SearchBarAndPaginator.svelte";

</script>

<main>

    <SearchBarAndPaginator />

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