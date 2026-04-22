import Vue from 'vue'
import VueRouter from 'vue-router'
import Index from '../views/Index.vue'
import DealerDashboard from '../views/DealerDashboard.vue'
import FiveForcesRadar from '../views/FiveForcesRadar.vue'
import SalesPrediction from '../views/SalesPrediction.vue'
import AdvancedSalesPrediction from '../views/AdvancedSalesPrediction.vue'
import HistoryRecords from '../views/HistoryRecords.vue'
import AnalysisReports from '../views/AnalysisReports.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Profile from '../views/Profile.vue'
import Policy from '../views/Policy.vue'
import Comment from '../views/Comment.vue'
import AdminDealers from '../views/AdminDealers.vue'
import DealerForm from '../views/DealerForm.vue'
import DecisionSupport from '../views/DecisionSupport.vue'
import LayoutContainer from '../components/layout/LayoutContainer.vue'

Vue.use(VueRouter)

const routes = [
  {
    path: '/login',
    name: 'login',
    component: Login
  },
  {
    path: '/register',
    name: 'register',
    component: Register
  },
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/dashboard',
    component: LayoutContainer,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        component: DealerDashboard
      },
      {
        path: 'index',
        name: 'index',
        component: Index
      },
      {
        path: 'radar',
        name: 'radar',
        component: FiveForcesRadar
      },
      {
        path: 'prediction',
        name: 'prediction',
        component: SalesPrediction
      },
      {
        path: 'advanced-prediction',
        name: 'advancedPrediction',
        component: AdvancedSalesPrediction
      },
      {
        path: 'history',
        name: 'history',
        component: HistoryRecords
      },
      {
        path: 'analysis-reports',
        name: 'analysisReports',
        component: AnalysisReports
      },
      {
        path: 'profile',
        name: 'profile',
        component: Profile
      },
      {
        path: 'policy',
        name: 'policy',
        component: Policy
      },
      {
        path: 'comment',
        name: 'comment',
        component: Comment
      },
      {
        path: 'admin/dealers',
        name: 'adminDealers',
        component: AdminDealers,
        meta: { requiresAuth: true, requiresAdmin: true }
      },
      {
        path: 'decision-support',
        name: 'decisionSupport',
        component: DecisionSupport,
        meta: { requiresAuth: true }
      }
    ]
  },
  {
    path: '/admin/dealers/add',
    name: 'addDealer',
    component: DealerForm,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/dealers/edit/:id',
    name: 'editDealer',
    component: DealerForm,
    meta: { requiresAuth: true, requiresAdmin: true }
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }
    return { x: 0, y: 0 }
  }
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 获取用户信息
  const user = JSON.parse(localStorage.getItem('user')) || {}

  // 检查路由是否需要认证
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const requiresAdmin = to.matched.some(record => record.meta.requiresAdmin)

  // 不需要认证的路由（登录、注册）直接通过
  if (!requiresAuth) {
    next()
    return
  }

  // 需要认证的路由，如果用户未登录则重定向到登录页面
  if (!user.username) {
    next('/login')
    return
  }

  // 需要管理员权限的路由
  if (requiresAdmin && user.role !== 'admin') {
    alert('您没有权限访问此页面')
    next('/dashboard')
    return
  }

  next()
})

export default router
