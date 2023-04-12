<script lang="ts">
    import PixelBackground from '../lib/PixelBackground.svelte'
    import AnimatedSearchBar from '../lib/AnimatedSearchBar.svelte'
  </script>
  
  <main>
    
    <PixelBackground />
  
    <div class="searchBarContainer">
      <AnimatedSearchBar />
    </div>
  
  </main>
  
  <style>
    
    .searchBarContainer { /**Positon the bar in the page center*/
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      height: 7vh;
      width: 7vh;
    }
  
    .searchBarContainer:hover {
      width : 35vh;
    }
  
  </style>
  