<script lang="ts">
  //pageJSON = { expected JSON format should be a list of these
  //    "title": page.title,
  //        "url": page.url,
  //        "lastModified": lastModified,
  //        "topKeywords": topKeywords,
  //        "childLinks": childLinks,
  //        "content": page.content
  //    }

  import { onMount } from "svelte";
  import { Accordion, AccordionItem } from "@skeletonlabs/skeleton";

  export let resultsJSON: string; //the JSON string of the results

  interface ResultPage {
    title: string;
    url: string;
    lastModified: string;
    topKeywords: Array<[string, number]>;
    childLinks: Array<string>;
    content: string;
    ranking: number;
  }

  let hasPrevious = false;
  let hasNext = false;
  let resultPages = new Array<ResultPage>();

  // function to process the JSON and create a list of resultPages
  function processJSON(json: string) {
    let results = JSON.parse(json);
    for (let i = 0; i < results.length; i++) {
      let result = results[i];
      let title: string;
      let url: string;
      let lastModified: string;
      let topKeywords: Array<[string, number]>;
      let childLinks: Array<string>;
      let content: string;
      try {
        title = result.title; //a string of the title
        url = result.url; //a string of the url
        lastModified = result.lastModified; //a string of the date / time
        topKeywords = result.topKeywords; //list of tuples of keyword and frequency
        childLinks = result.childLinks; //list of links
        content = result.content; //a string of the content
      } catch {
        console.log("Error processing JSON: " + result);
        break;
      }
      //update the array of resultPages with the new resultPage
      //the i value is used for the rank of the result, and the first result is rank 1
      let newResultPage: ResultPage = {
        title: title,
        url: url,
        lastModified: lastModified,
        topKeywords: topKeywords,
        childLinks: childLinks,
        content: content,
        ranking: i + 1,
      };
      resultPages.push(newResultPage);
    }
  }

  processJSON(resultsJSON);
</script>

<div class="accordionsContainer flex flex-col overflow-y-auto">
  <Accordion
    autocollapse
    rounded="rounded-none"
    class=" variant-ghost-error p-4"
  >
    <!--Now to include the current 10 accordions-->
    {#each resultPages as resultPage (resultPage.ranking)}
      <!--Using key identification-->
      <!--
        //Now to create the accordion item with the data
        // rank value in the lead slot
        //the summary slot will be a link to the page as the title
        //get the last modified as the trailing slot (and if we can't do that, put in summary with another div flex justify-around to replicate)
        //the content slot will contain two divs, one for the top keywords and one for the child links
        //we'll bullet point them in
        -->
      <AccordionItem class="text-black truncate">
        <svelte:fragment slot="lead">
          <span class="text-l text-center">
            # {resultPage.ranking}
          </span></svelte:fragment
        >
        <svelte:fragment slot="summary">
          <a
            href={resultPage.url}
            class="text-l underline overflow-hidden decoration-primary-500 underline-offset-1"
            >{resultPage.title}</a
          >
        </svelte:fragment>
        <svelte:fragment slot="content">
          <!--Now to display the 10 keywords and 10 child urls-->
          <div class="contentContainer flex">
            <div class="keywordsContainer flex-1">
              <div class="keywordsTitle text-center">
                <span class="text-l underline-offset-2 underline"
                  >Top Keywords</span
                >
              </div>
              <div class="keywordsList flex justify-around">
                <ol class="list-decimal">
                  {#each resultPage.topKeywords as keyword (keyword[0])}
                    <li>{keyword[0]}, {keyword[1]}</li>
                  {/each}
                </ol>
              </div>
            </div>
            <div class="childLinksContainer flex-1">
              <div class="childLinksTitle text-center">
                <span class="text-l underline-offset-2 underline"
                  >Child Links</span
                >
              </div>
              <div class="childLinksList flex justify-start">
                <ul>
                  {#each resultPage.childLinks as childLink (childLink)}
                    <li>
                      <a
                        href={childLink}
                        class="underline decoration-primary-500">{childLink}</a
                      >
                    </li>
                  {/each}
                </ul>
              </div>
            </div>
          </div>
        </svelte:fragment>
      </AccordionItem>
    {/each}
  </Accordion>
</div>

<style lang="scss">
  .contentContainer {
    font-family: "Rubik", sans-serif;
  }

  .childLinksContainer {
    max-width: 50%;
    text-overflow: ellipsis;
    overflow: hidden;
  }
</style>
