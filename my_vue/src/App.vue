<template>
  <div id="app">
    <router-view/>
    <AIAssistant />
    <footer class="beian-footer">
      <a href="https://beian.mps.gov.cn/#/query/webSearch?code=34072202000304" rel="noreferrer" target="_blank" class="beian-link">
        <img src="/备案图标.png" alt="公安备案" class="beian-icon" />
        皖公网安备34072202000304号
      </a>
    </footer>
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

.beian-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #fff;
  border-top: 1px solid #e8e8e8;
  padding: 8px 0;
  text-align: center;
  z-index: 100;
}

.beian-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #666;
  text-decoration: none;
  font-size: 12px;
  transition: color 0.3s;
}

.beian-link:hover {
  color: #3498db;
}

.beian-icon {
  width: 16px;
  height: 16px;
}
</style>
