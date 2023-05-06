<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import SearchBarAndPaginator from "$lib/SearchBarAndPaginator.svelte";
    import {
        AppBar,
        ProgressRadial,
        drawerStore,
    } from "@skeletonlabs/skeleton";
    import type { DrawerSettings } from "@skeletonlabs/skeleton";
    import { searchHistory, searchQuery } from "../../historyStore";
    import "iconify-icon";
    import type { CustomEventWrapper, ParticlesEvents } from "svelte-particles";
    import type { Engine } from "tsparticles-engine";
    import type svelteParticles from "svelte-particles";
    import { loadFull } from "tsparticles";

    let ParticlesComponent: any;

    const particlesConfig = {
        particles: {
            number: {
                value: 30,
            },
            color: {
                value: "#607d8b",
            },
            size: {
                value: 2,
            },
            move: {
                enable: true,
                speed: 2,
                outModes: {
                    default: "bounce",
                },
            },
            line_linked: {
                enable: true,
                distance: 250,
                color: "#607d8b",
            },
        },
    };

    let onParticlesLoaded = (event: any) => {
        const particlesContainer = event.detail.particles;
    };

    let particlesInit = async (main: Engine) => {
        // you can use main to customize the tsParticles instance adding presets or custom shapes
        // this loads the tsparticles package bundle, it's the easiest method for getting everything ready
        // starting from v2 you can add only the features you need reducing the bundle size
        await loadFull(main);
    };

    onMount(async () => {
        //dynamic import for svelte-particles so it can be used client side (prevents window not defined crash)
        const particlesModule = await import("svelte-particles"); // thats why we add the particles to each side in onMount after page load

        ParticlesComponent = particlesModule.default;
    });

    let curQuery: string = "";
    let waitingForSearch: boolean = true; // to trigger the loading animation

    //function to append used search queries to the history store's searchHistory array
    function appendSearchQuery(newQuery: string) {
        searchHistory.update((arr) => [...arr, newQuery]);
    }

    function updateSearchQuery(newQuery: string) {
        searchQuery.set(newQuery);
    }
</script>

<main>
    <AppBar background="variant-ghost-error">
        <svelte:fragment slot="lead">
            <a href="/">
                <iconify-icon
                    icon="ic:outline-home"
                    height="2rem"
                    width="2rem"
                    style="color: #000000"
                />
            </a>
        </svelte:fragment>
        <svelte:fragment slot="trail">
            <!--We'll put the hamburger for the history menu here-->
            <button on:click={() => drawerStore.open()}>
                <img src="/history-linear.svg" alt="History" />
            </button>
        </svelte:fragment>
    </AppBar>

    <div id="particles-container">
        <svelte:component
            this={ParticlesComponent}
            id="particles"
            options={particlesConfig}
            on:particlesLoaded={onParticlesLoaded}
            {particlesInit}
        />
    </div>

    <div id="search-content-container">
        <div class= "search-hero flex flex-col border-l-4 border-black p-4">
            <h2 class="search-step">Let's</h2>
            <h2 class="search-step">Search for</h2>
            <h2 class="search-step"><span class="fancy">Connections</span></h2>
        </div>
    </div>

</main>

<style lang="scss">
    main {
        background-color: rgb(var(--color-error-500));
        margin: 0px;
        height: 100vh;
        width: 100vw;
        overflow: hidden;
    }

    #particles-container {
        position: absolute;
        width: 100%;
        height: 100%;
    }

    .search-step {
        font-family: "Rubik";
        font-size: 8vw;
        margin-top: .75rem;
        margin-bottom: .75rem;

        .fancy {
            font-family: "Lobster", cursive;
            color: rgb(var(--color-primary-500));
        }
    }

    #search-content-container {
    align-items: center;
    display: flex;
    justify-content: center;
    position: absolute;
    color: black;
    pointer-events: none;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    }

</style>
