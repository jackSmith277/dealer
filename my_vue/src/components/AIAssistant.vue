<template>
  <div class="ai-assistant">
    <div v-if="isOpen" class="ai-panel">
      <button class="close-btn" @click="isOpen = false">×</button>
      <iframe 
        ref="aiIframe"
        :src="iframeSrc" 
        class="ai-iframe"
        frameborder="0"
        allow="microphone; camera"
      ></iframe>
    </div>
    
    <div class="float-btn" @click="isOpen = !isOpen" :class="{ active: isOpen }">
      <span v-if="!isOpen">🤖</span>
      <span v-else>✕</span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AIAssistant',
  data() {
    return {
      isOpen: false,
      iframeSrc: '/ai-plugin/sidepanel.html'
    }
  }
}
</script>

<style scoped>
.ai-assistant {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 9999;
}

.float-btn {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  transition: all 0.3s;
}

.float-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.5);
}

.float-btn.active {
  background: #ff4444;
}

.ai-panel {
  position: absolute;
  bottom: 70px;
  right: 0;
  width: 400px;
  height: 600px;
  background: white;
  border-radius: 12px;
  overflow: hidden;
}

.close-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 10;
  background: rgba(255, 255, 255, 0.3);
  border: none;
  color: white;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.5);
}

.ai-iframe {
  width: 100%;
  height: 100%;
  border: none;
  background: white;
}
</style>
