import Vue from 'vue'
import Router from 'vue-router'

Vue.use(Router)

/* Layout */
import Layout from '@/layout'

/**
 * Note: sub-menu only appear when route children.length >= 1
 * Detail see: https://panjiachen.github.io/vue-element-admin-site/guide/essentials/router-and-nav.html
 *
 * hidden: true                   if set true, item will not show in the sidebar(default is false)
 * alwaysShow: true               if set true, will always show the root menu
 *                                if not set alwaysShow, when item has more than one children route,
 *                                it will becomes nested mode, otherwise not show the root menu
 * redirect: noRedirect           if set noRedirect will no redirect in the breadcrumb
 * name:'router-name'             the name is used by <keep-alive> (must set!!!)
 * meta : {
    roles: ['admin','editor']    control the page roles (you can set multiple roles)
    title: 'title'               the name show in sidebar and breadcrumb (recommend set)
    icon: 'svg-name'/'el-icon-x' the icon show in the sidebar
    breadcrumb: false            if set false, the item will hidden in breadcrumb(default is true)
    activeMenu: '/example/list'  if set path, the sidebar will highlight the path you set
  }
 */

/**
 * constantRoutes
 * a base page that does not have permission requirements
 * all roles can be accessed
 */
export const constantRoutes = [
  {
    path: '/login',
    component: () => import('@/views/login/index'),
    hidden: true
  },

  {
    path: '/404',
    component: () => import('@/views/404'),
    hidden: true
  },

  {
    path: '/',
    redirect: '/stock/index',
    hidden: true
  },

  {
    path: '/stock',
    component: Layout,
    redirect: '/stock/index',
    name: 'Stock',
    meta: { title: '股票分析', icon: 'el-icon-s-home' },
    children: [
      {
        path: 'index',
        name: 'StockIndex',
        component: () => import('@/views/stock/index'),
        meta: { title: '股票分析', icon: 'el-icon-s-home' }
      },
      {
        path: 'single',
        name: 'StockSingle',
        component: () => import('@/views/stock/single'),
        meta: { title: '单股分析' },
        hidden: true
      },
      {
        path: 'batch',
        name: 'StockBatch',
        component: () => import('@/views/stock/batch'),
        meta: { title: '批量分析' },
        hidden: true
      },
      {
        path: 'history',
        name: 'StockHistory',
        component: () => import('@/views/stock/history'),
        meta: { title: '历史记录' },
        hidden: true
      }
    ]
  },

  {
    path: '/selection',
    component: Layout,
    redirect: '/selection/mainforce',
    name: 'Selection',
    alwaysShow: true,
    meta: { title: '选股板块', icon: 'el-icon-medal' },
    children: [
      {
        path: 'mainforce',
        name: 'MainforceIndex',
        component: () => import('@/views/mainforce/index'),
        meta: { title: '主力选股', icon: 'el-icon-star-on' }
      },
      {
        path: 'mainforce/batch',
        name: 'MainforceBatch',
        component: () => import('@/views/mainforce/batch'),
        meta: { title: '批量分析' },
        hidden: true
      },
      {
        path: 'mainforce/history',
        name: 'MainforceHistory',
        component: () => import('@/views/mainforce/history'),
        meta: { title: '历史记录' },
        hidden: true
      }
    ]
  },

  {
    path: '/strategy',
    component: Layout,
    redirect: '/strategy/sector',
    name: 'Strategy',
    alwaysShow: true,
    meta: { title: '策略分析', icon: 'el-icon-guide' },
    children: [
      {
        path: 'sector',
        name: 'SectorIndex',
        component: () => import('@/views/sector/index'),
        meta: { title: '智策板块', icon: 'el-icon-s-marketing' }
      },
      {
        path: 'sector/schedule',
        name: 'SectorSchedule',
        component: () => import('@/views/sector/schedule'),
        meta: { title: '定时任务' },
        hidden: true
      },
      {
        path: 'sector/history',
        name: 'SectorHistory',
        component: () => import('@/views/sector/history'),
        meta: { title: '历史报告' },
        hidden: true
      },
      {
        path: 'longhubang',
        name: 'LonghubangIndex',
        component: () => import('@/views/longhubang/index'),
        meta: { title: '智瞰龙虎', icon: 'el-icon-trophy' }
      },
      {
        path: 'longhubang/scoring',
        name: 'LonghubangScoring',
        component: () => import('@/views/longhubang/scoring'),
        meta: { title: '评分排名' },
        hidden: true
      },
      {
        path: 'longhubang/batch',
        name: 'LonghubangBatch',
        component: () => import('@/views/longhubang/batch'),
        meta: { title: '批量分析' },
        hidden: true
      },
      {
        path: 'longhubang/history',
        name: 'LonghubangHistory',
        component: () => import('@/views/longhubang/history'),
        meta: { title: '历史报告' },
        hidden: true
      }
    ]
  },

  {
    path: '/management',
    component: Layout,
    redirect: '/management/portfolio',
    name: 'Management',
    alwaysShow: true,
    meta: { title: '投资管理', icon: 'el-icon-briefcase' },
    children: [
      {
        path: 'portfolio',
        name: 'PortfolioIndex',
        component: () => import('@/views/portfolio/index'),
        meta: { title: '持仓分析', icon: 'el-icon-s-finance' }
      },
      {
        path: 'portfolio/analyze',
        name: 'PortfolioAnalyze',
        component: () => import('@/views/portfolio/analyze'),
        meta: { title: '批量分析' },
        hidden: true
      },
      {
        path: 'portfolio/schedule',
        name: 'PortfolioSchedule',
        component: () => import('@/views/portfolio/schedule'),
        meta: { title: '定时配置' },
        hidden: true
      },
      {
        path: 'portfolio/history',
        name: 'PortfolioHistory',
        component: () => import('@/views/portfolio/history'),
        meta: { title: '分析历史' },
        hidden: true
      },
      {
        path: 'monitor',
        name: 'MonitorIndex',
        component: () => import('@/views/monitor/index'),
        meta: { title: 'AI 盯盘', icon: 'el-icon-view' }
      },
      {
        path: 'monitor/positions',
        name: 'MonitorPositions',
        component: () => import('@/views/monitor/positions'),
        meta: { title: '持仓管理' },
        hidden: true
      },
      {
        path: 'monitor/history',
        name: 'MonitorHistory',
        component: () => import('@/views/monitor/history'),
        meta: { title: '决策历史' },
        hidden: true
      },
      {
        path: 'realtime',
        name: 'RealtimeIndex',
        component: () => import('@/views/realtime/index'),
        meta: { title: '实时监测', icon: 'el-icon-bell' }
      },
      {
        path: 'realtime/notifications',
        name: 'RealtimeNotifications',
        component: () => import('@/views/realtime/notifications'),
        meta: { title: '通知历史' },
        hidden: true
      }
    ]
  },

  {
    path: '/history',
    component: Layout,
    children: [
      {
        path: 'index',
        name: 'History',
        component: () => import('@/views/history/index'),
        meta: { title: '历史记录', icon: 'el-icon-document' }
      }
    ]
  },

  {
    path: '/config',
    component: Layout,
    children: [
      {
        path: 'index',
        name: 'ConfigIndex',
        component: () => import('@/views/config/index'),
        meta: { title: '环境配置', icon: 'el-icon-setting' }
      }
    ]
  },

  {
    path: '/data',
    component: Layout,
    children: [
      {
        path: 'index',
        name: 'DataManagement',
        component: () => import('@/views/data/index'),
        meta: { title: '数据管理', icon: 'el-icon-coin' }
      }
    ]
  },

  // 404 page must be placed at the end !!!
  { path: '*', redirect: '/404', hidden: true }
]

const createRouter = () => new Router({
  // mode: 'history', // require service support
  scrollBehavior: () => ({ y: 0 }),
  routes: constantRoutes
})

const router = createRouter()

// Detail see: https://github.com/vuejs/vue-router/issues/1234#issuecomment-357941465
export function resetRouter() {
  const newRouter = createRouter()
  router.matcher = newRouter.matcher // reset router
}

export default router
