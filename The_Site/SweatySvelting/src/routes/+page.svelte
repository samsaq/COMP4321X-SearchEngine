<script lang="ts">
    import { onMount } from "svelte";

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
        --black: rgb(25 25 25);
        --gold: rgb(193 165 32);
        --white: rgb(255 255 255);

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

    .fancy {
        /*Add a gold underline to the text*/
        text-decoration-line: underline;
        text-decoration-color: var(--gold);
        text-decoration-thickness: 0.75rem;
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
