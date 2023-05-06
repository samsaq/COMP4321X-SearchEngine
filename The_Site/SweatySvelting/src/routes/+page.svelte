<script lang="ts">
    import type { errors } from "@playwright/test";
    import { onMount, onDestroy } from "svelte";
    import particlesJS from "particles.js";

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
            line_linked: {
                enable: true,
                distance: 350,
                color: "#607d8b",
            },
        },
        interactivity: {
            events: {
                onhover: {
                    enable: true,
                    mode: "grab",
                },
                onclick: {
                    enable: false,
                },
            },
            modes: {
                grab: {
                    distance: 500,
                    line_linked: {
                        opacity: 1,
                    },
                },
            },
        },
    };

    onMount(() => {
        const left = document.getElementById("left-side")!;
        const right = document.getElementById("right-side")!;

        const handleMove = (e: MouseEvent) => {
            left.style.width = `${(e.clientX / window.innerWidth) * 100}%`;
        };

        document.onmousemove = (e) => handleMove(e);
    });
</script>

<main>
    <div id="left-side" class="side">
        <h2 class="title">
            Sometimes you simply need to
            <a href="/Search">
                <span class="fancy">Seek</span>
            </a>
        </h2>
    </div>
    <div id="right-side" class="side">
        <h2 class="title">
            Sometimes you simply need to
            <a href="/Search">
                <span class="fancy">Search</span>
            </a>
        </h2>
    </div>
</main>

<style lang="postcss">
    :root {
        --black: rgb(var(--color-surface-500));
        --gold: rgb(var(--color-primary-500));
        --white: rgb(var(--color-error-500));

        --left-color: var(--black);
        --right-color: var(--white);
    }

    main {
        background-color: var(--black);
        margin: 0px;
    }

    .side {
        display: grid;
        height: 100vh;
        overflow: hidden;
        place-items: center;
        position: absolute;
        width: 100%;
        text-align: center;
    }

    .side .title {
        font-family: "Rubik";
        font-size: 8vw;
        font-weight: 500;
        margin: 0px 10vw;
        width: 80vw;
    }

    .side .fancy {
        font-family: "Lobster", cursive;
        font-size: 1.3em;
        line-height: 1.5em;
    }

    #left-side {
        background-color: var(--left-color);
        width: 60%;
        z-index: 2;
    }

    #left-side .title {
        color: white;
    }

    #left-side .fancy {
        color: var(--right-color);
    }

    #right-side {
        background-color: var(--right-color);
    }

    #right-side .title {
        color: var(--black);
    }

    #right-side .fancy {
        color: var(--left-color);
    }
</style>
