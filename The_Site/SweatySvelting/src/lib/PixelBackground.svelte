<!-- The component that will setup the colorful pixel-grid background -->
<script>
    import { onMount } from "svelte";
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
                Mystore.update(currentValue => {
                    return { ...currentValue, curMidIndexColor: curBackgroundColor };
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

        createGrid();

        // this function will simulate a click at a random index every 3.5-7.5 seconds, after 3.5-7.5 seconds from page load
        setTimeout(() => {
            function simulateClick(curIndexNum) {
                setInterval(() => {
                    // get a random index bounded by curIndexNum
                    const randomIndex = Math.floor(Math.random() * curIndexNum);
                    // simulate a click at the random index
                    const tile =
                        document.getElementsByClassName("tile")[randomIndex];
                    tile.dispatchEvent(new Event('click'));
                }, Math.floor(Math.random() * (7500 - 3500) + 3500));
            }
            simulateClick(curIndexNum);
        }, Math.floor(Math.random() * (7500 - 3500) + 3500));

        window.onresize = () => createGrid();
    });
</script>

<div class="componentBody">
    <div id="tiles" />
</div>

<style>
    .componentBody {
        background-color: rgb(20, 20, 20);
        height: 100vh;
        overflow: hidden;
        margin: 0px;
        z-index: -1;
    }

    #tiles {
        height: 100vh;
        width: 100vw;
        display: grid;
        grid-template-columns: repeat(var(--columns), 1fr);
        grid-template-rows: repeat(var(--rows), 1fr);
    }
</style>
