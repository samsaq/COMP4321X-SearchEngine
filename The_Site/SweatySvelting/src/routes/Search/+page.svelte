<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import SearchBarAndPaginator from "$lib/SearchBarAndPaginator.svelte";
    import {
        AppBar,
        ProgressRadial,
        drawerStore,
        modalStore,
    } from "@skeletonlabs/skeleton";
    import type { DrawerSettings, ModalSettings } from "@skeletonlabs/skeleton";
    import { get } from "svelte/store";
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

    onMount(() => {
        const btn = document.querySelector(".btn"),
            input = document.querySelector(".input");
        if (btn && input) {
            btn.addEventListener("click", () => {
                btn.classList.toggle("close");
                input.classList.toggle("inclicked");
            });
        }
    });

    let curQuery: string = "";
    let waitingForSearch: boolean = true; // to trigger the loading animation

    let searchHistoryArray: string[] = [];

    //function to append used search queries to the history store's searchHistory array
    function appendSearchQuery(newQuery: string) {
        searchHistory.update((arr) => [...arr, newQuery]);
    }

    function updateSearchQuery(newQuery: string) {
        searchQuery.set(newQuery);
    }

    //function to handle the search bar's submit event
    function submitQuery(event: Event) {
        event.preventDefault();
        const targetUrl = "/api/search?q=${curQuery}";
        if (curQuery !== "") {
            //if the query is not empty
            searchHistoryArray = get(searchHistory); //get the search history array from the store
            if (!searchHistoryArray.includes(curQuery)) {
                //if the query is a new one
                updateSearchQuery(curQuery);
                appendSearchQuery(curQuery);
                //now to send and process the query
            } // if the query has already been done, send a modal to the user
            else {
                const oldQuery: ModalSettings = {
                    type: "alert",
                    title: "You've already searched for this!",
                    body: "Please use the history menu to view your previous search results.",
                };
                curQuery = "";
                modalStore.trigger(oldQuery);
            }
        }
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
        <div class="search-hero flex flex-col border-l-4 border-black p-4">
            <h2 class="search-step">Let's</h2>
            <h2 class="search-step">Search for</h2>
            <h2 class="search-step"><span class="fancy">Connections</span></h2>
        </div>

        <form
            on:submit|preventDefault={submitQuery}
            method="GET"
            class="search-box pointer-events-auto"
        >
            <iconify-icon
                icon="ic:baseline-search"
                class="ml-3 search-icon"
                height="2rem"
                width="2rem"
                style="color: #000000"
            />
            <input
                type="text"
                class="border-0 bg-transparent w-20"
                id="search-input"
                placeholder="Search"
                bind:value={curQuery}
                on:blur= {() => curQuery = ""}
            /> <!--on:blur triggers when focus is lost, clearing the search text-->
        </form>
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
        line-height: 8vw;

        .fancy {
            font-family: "Lobster", cursive;
            color: rgb(var(--color-primary-500));
        }
    }

    .search-box {
        width: 38.5%; //find a better way to do this, works fine in 1920x1080, but lopsided otherwise
        height: 3.5rem;
        border-width: 4px;
        border-color: black;
        background-color: transparent;
        border-radius: 0px;
        margin: 0.75rem;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .search-icon {
        transition: all 0.3s ease-in-out;
    }

    #search-input {
        transition: all 0.3s ease-in-out;

        &:focus {
            box-shadow: none;
            flex: 1;
        }
    }

    #search-content-container {
        align-items: center;
        display: flex;
        flex-direction: column;
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
