<!-- A fancy circle to bar animated search bar component-->

<script>
    import { Mystore } from "../Mystore.js";

    let bgColorForSearchIcon = "rgb(20, 20, 20)";

    Mystore.subscribe((value) => {
        value.curMidIndexColor = bgColorForSearchIcon;
    });
</script>

<style>

    .search-box {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: #2f3640;
        height : 2vh;
        border-radius: 2vh;
        padding: .5vh;
        z-index: 1;
    }

    .search-box:hover > .search-txt {
        width: 12vh;
        padding: 0 .25vh;
    }

    .search-box:hover > .search-btn {
        background: #e84118; /*put the value from the store here later, or just remove*/
    }

    .search-btn {
        color: #e84118;
        float: right;
        width: 2vh;
        height: 2vh;
        border-radius: 50%;
        background: #2f3640; /*put the value from the store here later*/
        display: flex;
        justify-content: center;
        align-items: center;
        transition: 0.4s;
    }

    .search-txt {
        border: none;
        background: none;
        outline: none;
        float: left;
        padding: 0;
        color: white;
        font-size: 1.2vh;
        transition: 0.4s;
        line-height: 2vh;
        width: 0px;
    }

</style>

<div class="search-box">
    <input type="text" class="search-txt" placeholder="What are you looking for?" />
    <a class="search-btn" href="#"> 
        <i class="fas fa-search"></i>
    </a>
</div>