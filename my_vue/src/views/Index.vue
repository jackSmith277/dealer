<!-- 代码已包含 CSS：使用 TailwindCSS , 安装 TailwindCSS 后方可看到布局样式效果 -->
<template>
<div class="app-container bg-gray-900 min-h-screen text-white">
<!-- 顶部导航区 -->
<header class="top-nav flex items-center justify-between px-8 py-4 border-b border-gray-700">
<div class="left-section flex items-center space-x-6">
<div class="brand text-sm opacity-75">智慧课堂数据可视化平台</div>
</div>
<div class="center-section flex justify-center">
<h1 class="text-xl font-bold">智慧课堂数据可视化平台</h1>
</div>
<div class="right-section flex items-center space-x-4">
<button class="nav-tab px-4 py-2 rounded-md bg-blue-600 text-white !rounded-button whitespace-nowrap">课程</button>
<button class="nav-tab px-4 py-2 rounded-md hover:bg-gray-700 !rounded-button whitespace-nowrap">课堂</button>
<button class="back-btn px-4 py-2 rounded-md hover:bg-gray-700 !rounded-button whitespace-nowrap">
<i class="fas fa-arrow-left mr-2"></i>返回
</button>
</div>
</header>
<!-- 主体内容区 -->
<main class="main-content p-8 grid grid-cols-3 gap-8 h-[calc(100vh-120px)]">
<!-- 左侧卡片 - 课程简介 -->
<div class="module-card bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
<div class="card-header p-6 border-b border-gray-700">
<h2 class="text-lg font-semibold">课程简介</h2>
</div>
<div class="card-body p-6 h-[calc(100%-60px)]">
<div class="flex flex-col h-full">
<div class="flex-1 flex">
<div class="w-2/5 flex items-center justify-center">
<img
src="https://ai-public.mastergo.com/ai/img_res/1772780808928a3K9mP2xQ7vN4rT8wY.jpg"
alt="课程图示"
class="w-full h-full object-contain"
/>
</div>
<div class="w-3/5 pl-4 flex flex-col justify-center">
<h3 class="text-xl font-medium mb-3 text-blue-400">物联网概论</h3>
<p class="text-sm text-gray-300 leading-relaxed">
本课程系统介绍了物联网的起源与发展、概念与特征、体系结构与关键技术。
通过理论讲解与实践结合，帮助学生掌握物联网的核心技术原理和应用方法。
</p>
</div>
</div>
<div class="mt-4">
<button class="action-btn w-full py-2 bg-blue-600 hover:bg-blue-700 rounded-md !rounded-button whitespace-nowrap">
选择课堂
</button>
</div>
</div>
</div>
</div>
<!-- 中间卡片 - 课程资源占比 -->
<div class="module-card bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
<div class="card-header p-6 border-b border-gray-700">
<h2 class="text-lg font-semibold">课程资源占比</h2>
</div>
<div class="card-body p-6 h-[calc(100%-60px)] flex flex-col items-center justify-center">
<div class="chart-container w-48 h-48 relative">
<div class="relative w-full h-full">
<!-- 圆形图表容器 -->
<div class="absolute inset-0 rounded-full border-8 border-gray-600"></div>
<div class="absolute inset-4 rounded-full border-8 border-blue-400 transform rotate-45"></div>
<div class="absolute inset-8 rounded-full border-8 border-green-400 transform rotate-90"></div>
<div class="absolute inset-12 rounded-full border-8 border-orange-400 transform rotate-135"></div>
<!-- 中心图标 -->
<div class="absolute inset-0 flex items-center justify-center">
<i class="fas fa-graduation-cap text-3xl text-white"></i>
</div>
</div>
</div>
<div class="legend mt-6 w-full">
<div class="flex justify-center space-x-6 mb-2">
<div class="flex items-center">
<div class="w-3 h-3 bg-blue-400 rounded mr-2"></div>
<span class="text-xs">视频</span>
</div>
<div class="flex items-center">
<div class="w-3 h-3 bg-green-400 rounded mr-2"></div>
<span class="text-xs">PPT</span>
</div>
<div class="flex items-center">
<div class="w-3 h-3 bg-orange-400 rounded mr-2"></div>
<span class="text-xs">作业</span>
</div>
<div class="flex items-center">
<div class="w-3 h-3 bg-red-400 rounded mr-2"></div>
<span class="text-xs">文档</span>
</div>
</div>
</div>
</div>
</div>
<!-- 右侧卡片 - 学生排行榜 -->
<div class="module-card bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
<div class="card-header p-6 border-b border-gray-700">
<h2 class="text-lg font-semibold">学生排行榜</h2>
</div>
<div class="card-body p-6 h-[calc(100%-60px)]">
<div class="table-container">
<table class="w-full text-sm">
<thead>
<tr class="border-b border-gray-700">
<th class="py-2 text-left">排名</th>
<th class="py-2 text-left">姓名</th>
<th class="py-2 text-right">测试平均成绩</th>
</tr>
</thead>
<tbody>
<tr class="border-b border-gray-700 hover:bg-gray-750">
<td class="py-3">
<span class="inline-flex items-center justify-center w-6 h-6 bg-yellow-500 text-black rounded-full text-xs font-bold">1</span>
</td>
<td class="py-3">马*罗</td>
<td class="py-3 text-right text-yellow-400 font-medium">92.1</td>
</tr>
<tr class="border-b border-gray-700 hover:bg-gray-750">
<td class="py-3">
<span class="inline-flex items-center justify-center w-6 h-6 bg-gray-400 text-black rounded-full text-xs font-bold">2</span>
</td>
<td class="py-3">张*承</td>
<td class="py-3 text-right">91.3</td>
</tr>
<tr class="border-b border-gray-700 hover:bg-gray-750">
<td class="py-3">
<span class="inline-flex items-center justify-center w-6 h-6 bg-amber-600 text-white rounded-full text-xs font-bold">3</span>
</td>
<td class="py-3">王*</td>
<td class="py-3 text-right">89.2</td>
</tr>
<tr class="border-b border-gray-700 hover:bg-gray-750">
<td class="py-3">
<span class="inline-flex items-center justify-center w-6 h-6 bg-gray-600 text-white rounded-full text-xs font-bold">4</span>
</td>
<td class="py-3">夏*</td>
<td class="py-3 text-right">88</td>
</tr>
<tr class="hover:bg-gray-750">
<td class="py-3">
<span class="inline-flex items-center justify-center w-6 h-6 bg-gray-700 text-white rounded-full text-xs font-bold">5</span>
</td>
<td class="py-3">李*圆</td>
<td class="py-3 text-right">87.6</td>
</tr>
</tbody>
</table>
</div>
</div>
</div>
<!-- 下方左侧卡片 - 课程信息 -->
<div class="module-card bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
<div class="card-header p-6 border-b border-gray-700">
<h2 class="text-lg font-semibold">课程信息</h2>
</div>
<div class="card-body p-6 h-[calc(100%-60px)]">
<div class="grid grid-cols-2 gap-6">
<div class="info-item">
<label class="text-sm text-gray-400 block mb-1">课程性质</label>
<div class="text-white font-medium">专业主干课</div>
</div>
<div class="info-item">
<label class="text-sm text-gray-400 block mb-1">课程数量</label>
<div class="text-white font-medium">2</div>
</div>
<div class="info-item">
<label class="text-sm text-gray-400 block mb-1">课程学分</label>
<div class="text-white font-medium">3</div>
</div>
<div class="info-item">
<label class="text-sm text-gray-400 block mb-1">课程分钟</label>
<div class="text-white font-medium">45</div>
</div>
<div class="info-item">
<label class="text-sm text-gray-400 block mb-1">授课教师</label>
<div class="text-white font-medium">戴*诚、向*</div>
</div>
<div class="info-item">
<label class="text-sm text-gray-400 block mb-1">上课地点</label>
<div class="text-white font-medium">n101、n109</div>
</div>
<div class="info-item">
<label class="text-sm text-gray-400 block mb-1">上课时间</label>
<div class="text-white font-medium">周二7-8节、周四5-6节、周一8-9节、周三1-2节</div>
</div>
<div class="info-item">
<label class="text-sm text-gray-400 block mb-1">课堂人数</label>
<div class="text-white font-medium">15、20</div>
</div>
</div>
</div>
</div>
<!-- 下方中间卡片 - 学习进度统计 -->
<div class="module-card bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
<div class="card-header p-6 border-b border-gray-700">
<h2 class="text-lg font-semibold">学习进度统计</h2>
</div>
<div class="card-body p-6 h-[calc(100%-60px)] flex flex-col">
<div class="progress-item mb-4">
<label class="text-sm text-gray-400 block mb-2">视频观看进度</label>
<div class="w-full bg-gray-700 rounded-full h-2">
<div class="bg-blue-500 h-2 rounded-full" style="width: 75%"></div>
</div>
<div class="text-right text-sm text-blue-400 mt-1">75%</div>
</div>
<div class="progress-item mb-4">
<label class="text-sm text-gray-400 block mb-2">作业完成率</label>
<div class="w-full bg-gray-700 rounded-full h-2">
<div class="bg-green-500 h-2 rounded-full" style="width: 60%"></div>
</div>
<div class="text-right text-sm text-green-400 mt-1">60%</div>
</div>
<div class="progress-item mb-4">
<label class="text-sm text-gray-400 block mb-2">课堂参与度</label>
<div class="w-full bg-gray-700 rounded-full h-2">
<div class="bg-purple-500 h-2 rounded-full" style="width: 85%"></div>
</div>
<div class="text-right text-sm text-purple-400 mt-1">85%</div>
</div>
<div class="progress-item">
<label class="text-sm text-gray-400 block mb-2">测验通过率</label>
<div class="w-full bg-gray-700 rounded-full h-2">
<div class="bg-yellow-500 h-2 rounded-full" style="width: 70%"></div>
</div>
<div class="text-right text-sm text-yellow-400 mt-1">70%</div>
</div>
</div>
</div>
</div>
<!-- 下方右侧卡片 - 课堂互动分布 -->
<div class="module-card bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
<div class="card-header p-6 border-b border-gray-700">
<h2 class="text-lg font-semibold">课堂互动分布</h2>
</div>
<div class="card-body p-6 h-[calc(100%-60px)] flex items-center justify-center">
<div class="chart-placeholder text-center text-gray-500">
<i class="fas fa-chart-pie text-4xl mb-2"></i>
<p class="text-sm">互动分布图表</p>
</div>
</div>
</div>
</main>
</div>
</template>
<script>
export default {
name: 'Dashboard',
data() {
return {
// 数据将在后续扩展中使用
};
},
methods: {
// 方法将在后续扩展中使用
}
};
</script>
<style scoped>
.app-container {
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
.top-nav {
background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}
.module-card {
transition: all 0.3s ease;
display: flex;
flex-direction: column;
}
.module-card:hover {
transform: translateY(-2px);
box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
}
.card-header {
background: rgba(30, 41, 59, 0.6);
}
.card-body {
background: rgba(17, 24, 39, 0.4);
}
.nav-tab.active {
background: #3b82f6;
}
.action-btn {
transition: all 0.2s ease;
}
.action-btn:hover {
transform: scale(1.02);
}
.table-container table {
border-collapse: separate;
border-spacing: 0;
}
.table-container th,
.table-container td {
padding-left: 0.5rem;
padding-right: 0.5rem;
}
.info-item {
padding: 0.75rem 0;
border-bottom: 1px solid rgba(55, 65, 81, 0.5);
}
.info-item:last-child {
border-bottom: none;
}
.chart-placeholder {
opacity: 0.6;
}
/* 自定义滚动条 */
::-webkit-scrollbar {
width: 6px;
height: 6px;
}
::-webkit-scrollbar-track {
background: rgba(30, 41, 59, 0.3);
}
::-webkit-scrollbar-thumb {
background: rgba(75, 85, 99, 0.5);
border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
background: rgba(75, 85, 99, 0.8);
}
</style>