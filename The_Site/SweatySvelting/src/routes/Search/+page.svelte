<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import SearchBarAndPaginator from "$lib/SearchBarAndPaginator.svelte";
    import {
        AppBar,
        ProgressRadial,
        getDrawerStore,
        getModalStore,
    } from "@skeletonlabs/skeleton";
    import type { DrawerSettings, ModalSettings } from "@skeletonlabs/skeleton";
    import { get } from "svelte/store";
    import { searchHistory, searchQuery } from "../../historyStore";
    import "iconify-icon";
    import type { CustomEventWrapper, ParticlesEvents } from "svelte-particles";
    import type { Engine } from "tsparticles-engine";
    import type svelteParticles from "svelte-particles";
    import { loadFull } from "tsparticles";
    import ResultAccordions from "$lib/ResultAccordions.svelte";

    let ParticlesComponent: any;
    const drawerStore = getDrawerStore();
    const modalStore = getModalStore();

    const particlesConfig = {
        particles: {
            number: {
                value: 45,
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
    let loading = false; // to trigger the loading animation
    let searchHistoryArray: string[] = [];
    let resultsJson: any;

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
        //if the curQuery is in the format: "URL:texthere, Number:numberhere", then we need to change the targetUrl
        //check if the curQuery starts with URL
        let  targetUrl = "https://search-engine-api.fly.dev/api/search/" + curQuery + "/50/";
        if (curQuery !== "") {
            //if the query is not empty
            searchHistoryArray = get(searchHistory); //get the search history array from the store
            if (!searchHistoryArray.includes(curQuery)) {
                //if the query is a new one
                updateSearchQuery(curQuery);
                appendSearchQuery(curQuery);
                animateSearchHero();
                //now to send and process the query
                //for testing, send to localhost:5000/api/search?q=${curQuery}
                loading = true;
                //fetch the search results from the backend
                awaitSearch(targetUrl);

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

    //function to await the backend
    async function awaitSearch(targetUrl: string) {
        fetch(targetUrl)
            .then((response) => response.json())
            .then((data) => {
                //if the query has not been done before, send the results to the ResultAccordions component
                //and set the loading variable to false
                waitingForSearch = false;
                loading = false;
                resultsJson = data;
            })
            .catch((error) => {
                //if there is an error, send a modal to the user
                const errorModal: ModalSettings = {
                    type: "alert",
                    title: "Error!",
                    body: "There was an error processing your search. Please reload the page.",
                };
                modalStore.trigger(errorModal);
                waitingForSearch = false;
                loading = false;
            });
    }

    let heroAnimating: boolean = false;
    let resultsBroughtUp: boolean = false;

    // function to toggle the animation class for the search hero text
    function animateSearchHero() {
        heroAnimating = true;
    }

    function handleHeroAnimEndHandler(event: any) {
        //if animate-hero-squish is a class of the element, move the search box (as the hero text is now hidden)
        if (event.target.classList.contains("animate-hero-squish")) {
            const searchBox = document.querySelector(".search-box");
            //transform the search box to the top of the page
            if (searchBox) {
                (searchBox as HTMLElement).style.transform =
                    "translateY(-60vh)";
                resultsBroughtUp = true;
            }
        }
    }

    function handleHeroAnimStartHandler(event: any) {
        const searchInput = document.getElementById("search-input");
        const searchHero = document.querySelector(".search-hero");
        if (searchHero) {
            if (searchHero.classList.contains("animate-hero-squish")) {
                //also, set the flex to 1 of the seach-input so it stops shrinking now that we have a query
                if (searchInput) {
                    (searchInput as HTMLElement).style.flex = "1";
                }
            }
        }
    }

    function handleSearchBoxBlur(event: any) {
        //if the animate-hero-squish doesn't exist, then clear curQuery on blur
        //else, do nothing
        if (!document.querySelector(".animate-hero-squish")) {
            curQuery = "";
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
        <div
            class="search-hero overflow-hidden flex flex-col border-l-4 border-black p-4 {heroAnimating
                ? 'animate-hero-squish'
                : ''}"
            on:animationend={handleHeroAnimEndHandler}
            on:animationstart={handleHeroAnimStartHandler}
        >
            <!--the class is toggled by the animateSearchHero function, for some reason toggling the class doesn't work via JS, but this does-->
            <h2
                class="search-step {heroAnimating ? 'animate-search-step' : ''}"
            >
                Let's
            </h2>
            <h2
                class="search-step {heroAnimating ? 'animate-search-step' : ''}"
            >
                Search for
            </h2>
            <h2
                class="search-step {heroAnimating ? 'animate-search-step' : ''}"
            >
                <span class="fancy">Connections</span>
            </h2>
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
                on:blur={handleSearchBoxBlur}
            />
            <!--on:blur triggers when focus is lost, clearing the search text-->
        </form>
    </div>
    <div
        class="resultsHolder flex flex-col justify-center backdrop-blur-sm {heroAnimating
            ? 'broughtUp'
            : ''}"
    >
        {#if resultsJson}
            <ResultAccordions resultsJSON={JSON.stringify(resultsJson.pages)} />
        {:else}
            <ProgressRadial
                ...
                stroke={100}
                meter="stroke-primary-500"
                track="stroke-primary-500/30"
                class="flex justify-center items-center"
            />
        {/if}
    </div>
</main>

<style lang="scss">
    @keyframes stepAnimation {
        0% {
            transform: translateX(0);
        }
        100% {
            transform: translateX(-200%);
        }
    }

    @keyframes heroSquishAnimation {
        0% {
            transform: scaleY(1);
            opacity: 1;
        }
        100% {
            transform: scaleY(0);
            opacity: 0;
        }
    }

    main {
        background-color: rgb(var(--color-error-500));
        margin: 0px;
        height: 100vh;
        width: 100vw;
        overflow: hidden;
    }

    .resultsHolder {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, 75%);
        width: 60vw;
        height: 75vh;
        border-width: 4px;
        border-color: black;
        border-style: solid;

        &.broughtUp {
            transform: translate(-50%, -35%);
            transition: all 2s ease-in-out;
            transition-delay: 3s;
        }
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
            color: rgb(193 165 32);
        }

        .animate-search-step {
            animation: stepAnimation 2s ease-in-out;
        }
    }

    .animate-search-step {
        animation: stepAnimation forwards 2s ease-in-out;
    }

    .animate-hero-squish {
        animation: heroSquishAnimation forwards 1s ease-in-out;
        animation-delay: 2s; //should be the same as the animation duration of the search steps, since the animation is triggered after the steps are done
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
        transition: all 1s ease-in-out;
    }

    .search-icon {
        transition: all 0.3s ease-in-out;
    }

    #search-input {
        transition: all 0.3s ease-in-out;

        &:focus {
            //we don't want any outlines since we already have one
            box-shadow: none;
            outline: none;
            flex: 1; //used to expand the input on click, and shrink back on blur
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
