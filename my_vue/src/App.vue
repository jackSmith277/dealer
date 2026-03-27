<template>
  <div id="app">
    <router-view/>
    <AIAssistant />
  </div>
</template>

<script>
import AIAssistant from '@/components/AIAssistant.vue'

export default {
  name: 'App',
  components: {
    AIAssistant
  }
}
</script>

<style>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body {
  font-family: 微软雅黑, MicrosoftYahei, sans-serif;
  font-size: 14px;
  color: #333;
  background-color: #f5f7fa;
  height: 100%;
}

#app {
  height: 100%;
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
