<!--
    The component that encloses the search bar & results display
    the results will appear once a search is sent, and will disappear once the search bar is empty
    the results is a paginated list of stepper cards for each result (displaying 10 per page by default for 5 pages)
    The first step will be the description, second will be keywords & frequencies, and third will be links
-->
<script lang="ts">
    import { Stepper, Step } from '@skeletonlabs/skeleton';

    function onNextHandler(e: any): void {
        console.log("event:next", e.detail);
    }
    function onBackHandler(e: any): void {
        console.log("event:prev", e.detail);
    }
    function onStepHandler(e: any): void {
        console.log("event:step", e.detail);
    }
    function onCompleteHandler(e: any): void {
        console.log("event:complete", e.detail);
        alert("Complete!");
    }
</script>

<div id="resultsContainer" class="">
    <div class="w-full card p-4 text-token">
        <Stepper on:next={onNextHandler} on:back={onBackHandler} on:step={onStepHandler} on:complete={onCompleteHandler}>
            <Step stepTerm="Description">
                <svelte:fragment slot="header">
                    <!--The title of the page & an avatar of its icon (serving as the link)-->
                    <!--How to display its rank?-->
                </svelte:fragment>
                <!--We'll display the last modified date & other metadata here-->
            </Step>
            <Step stepTerm="Keywords">
                <svelte:fragment slot="header">Keywords & Frequencies</svelte:fragment>
                <!--A ul going over a parsed list of Keywords will go here-->
            </Step>
            <Step stepTerm="Links">
                <svelte:fragment slot="header">Child Links</svelte:fragment>
                <!--A ul going over a parsed list of links will go here-->
            </Step>
        </Stepper>
    </div>
</div>

<style lang="postcss">
</style>
