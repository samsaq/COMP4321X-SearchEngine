<!--
    The component that encloses the search bar & results display
    the results will appear once a search is sent, and will disappear once the search bar is empty
    the results is a paginated list
-->
<script lang="ts">

    let resultsReady: boolean = false;

</script>

{#if resultsReady}
    <div id="resultsContainer" class="">
        
    </div>
{/if}

<style lang="scss">
    @function gray($color) {
        @return rgb($color, $color, $color);
    }

    $shadow: rgba(0, 0, 0, 0.12) 0px 1px 6px, rgba(0, 0, 0, 0.12) 0px 1px 4px;
    $cardShadow: rgba(50, 50, 93, 0.25) 0px 50px 100px -20px,
        rgba(0, 0, 0, 0.3) 0px 30px 60px -30px;

    $red: rgb(237, 66, 69);

    @keyframes fadeInAndExpand {
        from {
            opacity: 0;
            transform: scale(0.25);
        }

        50% {
            opacity: 0;
        }

        to {
            opacity: 1;
            transform: scale(1);
        }
    }

    @keyframes fadeInFromLeft {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }

        50% {
            opacity: 0;
        }

        to {
            opacity: 1;
            transform: translateX(0px);
        }
    }

    @keyframes spin {
        from {
            transform: rotate(0deg);
        }

        50% {
            transform: rotate(720deg);
        }

        to {
            transform: rotate(1440deg);
        }
    }

    .spin-animation {
        animation: spin 2s ease-in-out infinite;
    }
</style>
