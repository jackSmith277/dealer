const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    },
    onBeforeSetupMiddleware: function(devServer) {
      if (!devServer) return
      
      const express = require('express')
      const path = require('path')
      const aiPluginPath = path.resolve(__dirname, '../aiplugin/插件')
      
      devServer.app.use('/ai-plugin', express.static(aiPluginPath))
    }
  }
})
