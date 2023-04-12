<!-- The component that will setup the colorful pixel-grid background -->
<script>
    import { onMount, onDestroy } from "svelte";
    import { Mystore } from "../Mystore.js";
    import anime from "animejs";

    const colors = [
        "rgb(229, 57, 53)",
        "rgb(253, 216, 53)",
        "rgb(244, 81, 30)",
        "rgb(76, 175, 80)",
        "rgb(33, 150, 243)",
        "rgb(156, 39, 176)",
    ];
    //variables for the grid
    let columns = 0,
        rows = 0,
        count = -1,
        curBackgroundColor = "rgb(20, 20, 20)",
        curIndexNum,
        curIndexMid,
        interval,
        wrapper;

    onMount(() => {
        wrapper = document.getElementById("tiles");

        //onclick animation function
        const onClick = (index) => {
            count += 1;

            //alert("You clicked on tile " + index + "!");

            anime({
                //staggered grid animation
                targets: ".tile",
                backgroundColor: colors[count % (colors.length - 1)],
                delay: anime.stagger(50, {
                    grid: [columns, rows],
                    from: index,
                }),
            });
            curBackgroundColor = colors[count % (colors.length - 1)];
            if (index === curIndexMid) {
                Mystore.update((currentValue) => {
                    return {
                        ...currentValue,
                        curMidIndexColor: curBackgroundColor,
                    };
                });
            }
        };

        //for individual tiles
        const createTile = (index) => {
            const tile = document.createElement("div");
            tile.classList.add("tile");
            tile.style.backgroundColor = curBackgroundColor;
            tile.onclick = () => onClick(index);
            return tile;
        };
        //for an amount of tiles
        const createTiles = (quantity) => {
            Array.from(Array(quantity)).map((title, index) => {
                wrapper.appendChild(createTile(index));
            });
        };

        // this function will create the grid, and wipe it clean if it already exists (on resize)
        const createGrid = () => {
            wrapper.innerHTML = "";
            const pixelSize = document.body.clientWidth > 800 ? 100 : 50;
            columns = Math.ceil(document.body.clientWidth / pixelSize);
            rows = Math.ceil(document.body.clientHeight / pixelSize);
            wrapper.style.setProperty("--columns", columns);
            wrapper.style.setProperty("--rows", rows);
            createTiles(columns * rows);
            curIndexNum = columns * rows;
            curIndexMid = Math.floor(curIndexNum / 2);
        };

        function simulateClick(curIndexNum) {
            // get a random index bounded by curIndexNum
            const randomIndex = Math.floor(Math.random() * curIndexNum);
            // simulate a click at the random index
            const tile = document.getElementsByClassName("tile")[randomIndex];
            tile.dispatchEvent(new Event("click"));
        }

        createGrid();

        //Call simulateClick every 5 to 7.5 seconds
        interval = setInterval(() => {
            simulateClick(curIndexNum);
        }, Math.floor(Math.random() * 2500) + 5000);
       

        window.onresize = () => createGrid();
    });

    onDestroy(() => {
        clearInterval(interval);
    })


</script>

<div class="componentBody">
    <div id="tiles" />
</div>

<style>
    .componentBody {
        background-color: rgb(
            20,
            20,
            20
        ); /* this is the starting background color of the entire page */
        position: absolute; /**We don't want to interfere with the positioning of other elements*/
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        overflow: hidden;
        margin: 0px;
    }

    #tiles {
        height: 100vh;
        width: 100vw;
        display: grid;
        grid-template-columns: repeat(var(--columns), 1fr);
        grid-template-rows: repeat(var(--rows), 1fr);
    }
</style>
