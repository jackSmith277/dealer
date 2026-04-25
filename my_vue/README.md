# ASSPIS Project

本项目是一个基于 Vue 2 的前端应用，用于销售预测与智能分析系统。

## 目录结构说明

```
my_vue/
├── public/                 # 静态资源目录
│   ├── map/               # 地图数据文件
│   │   └── *_full.json    # 各省市地图 GeoJSON 数据
│   ├── favicon.ico        # 网站图标
│   └── index.html         # HTML 入口文件
├── src/                   # 源代码目录
│   ├── DS/               # DeepSeek AI 相关模块
│   │   ├── dataExtractor.js  # 数据提取工具
│   │   └── deepseek.js       # DeepSeek API 集成
│   ├── api/              # API 接口层
│   │   ├── index.js          # API 主入口
│   │   ├── mock.js           # 模拟数据接口
│   │   └── prediction.js     # 预测相关 API
│   ├── assets/           # 静态资源
│   │   ├── dealerData.json   # 经销商数据
│   │   ├── fiveForcesData.json # 五力分析数据
│   │   ├── logo.png          # 项目 Logo
│   │   └── 中国省加市.json    # 中国省市数据
│   ├── components/       # 公共组件
│   │   ├── layout/           # 布局组件
│   │   │   ├── LayoutContainer.vue  # 布局容器
│   │   │   ├── SideMenu.vue         # 侧边菜单
│   │   │   └── TopNavbar.vue        # 顶部导航栏
│   │   ├── AIAssistant.vue      # AI 助手组件
│   │   ├── CustomSelect.vue     # 自定义选择器
│   │   ├── DealerSelector.vue   # 经销商选择器
│   │   ├── RegionCascader.vue   # 地区级联选择器
│   │   └── ReportModal.vue      # 报告弹窗组件
│   ├── router/           # 路由配置
│   │   └── index.js          # 路由定义
│   ├── store/            # Vuex 状态管理
│   │   └── index.js          # Store 配置
│   ├── views/            # 页面视图
│   │   ├── AdminDealers.vue       # 经销商管理页
│   │   ├── AdvancedSalesPrediction.vue  # 高级销售预测
│   │   ├── AnalysisReports.vue    # 分析报告页
│   │   ├── Comment.vue            # 评论页
│   │   ├── DealerDashboard.vue    # 经销商仪表盘
│   │   ├── DealerForm.vue         # 经销商表单
│   │   ├── FiveForcesRadar.vue    # 五力分析雷达图
│   │   ├── HistoryRecords.vue     # 历史记录页
│   │   ├── Index.vue              # 首页
│   │   ├── Login.vue              # 登录页
│   │   ├── Policy.vue             # 政策页
│   │   ├── Profile.vue            # 个人中心
│   │   ├── Register.vue           # 注册页
│   │   ├── SalesPrediction.vue    # 销售预测页
│   │   └── StoreRanking.vue       # 门店排名页
│   ├── App.css           # 全局样式
│   ├── App.vue           # 根组件
│   └── main.js           # 应用入口
├── .gitignore            # Git 忽略配置
├── babel.config.js       # Babel 配置
├── jsconfig.json         # JS 配置
├── package.json          # 项目依赖配置
├── package-lock.json     # 依赖版本锁定
└── vue.config.js         # Vue CLI 配置
```

## 快速开始

### 安装依赖
```
npm install
```

### 开发模式运行
```
npm run serve
```

### 生产环境构建
```
npm run build
```

## 技术栈

- **Vue 2** - 前端框架
- **Vue Router** - 路由管理
- **Vuex** - 状态管理
- **Ant Design Vue** - UI 组件库
- **ECharts** - 数据可视化
- **Axios** - HTTP 请求库

## 配置说明

详细配置请参考 [Vue CLI 配置文档](https://cli.vuejs.org/config/)。
