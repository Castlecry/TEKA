import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/components/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
      },
      {
        path: '/knowledge',
        name: 'KnowledgeList',
        component: () => import('@/views/knowledge/KnowledgeList.vue'),
      },
      {
        path: '/knowledge/:id',
        name: 'KnowledgeDetail',
        component: () => import('@/views/knowledge/KnowledgeDetail.vue'),
      },
      {
        path: '/documents',
        name: 'DocumentList',
        component: () => import('@/views/document/DocumentList.vue'),
      },
      {
        path: '/chat',
        name: 'Chat',
        component: () => import('@/views/chat/ChatView.vue'),
      },
      {
        path: '/system/users',
        name: 'UserManage',
        component: () => import('@/views/system/UserManage.vue'),
      },
      {
        path: '/system/config',
        name: 'SystemConfig',
        component: () => import('@/views/system/SystemConfig.vue'),
      },
      {
        path: '/logs',
        name: 'ConversationLog',
        component: () => import('@/views/log/ConversationLog.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  if (to.meta.requiresAuth && !userStore.token) {
    next('/login')
  } else if (!to.meta.requiresAuth && userStore.token) {
    next('/')
  } else {
    next()
  }
})

export default router
