<template>
  <div class="layout-container">
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="logo">
          <Component :is="icons.Bot" class="logo-icon" />
          <span class="logo-text">企业知识助手</span>
        </div>
      </div>
      <nav class="sidebar-nav">
        <div
          v-for="item in menuItems"
          :key="item.path"
          class="nav-item"
          :class="{ active: $route.path === item.path }"
        >
          <router-link :to="item.path">
            <Component :is="item.icon" class="nav-icon" />
            <span class="nav-text">{{ item.label }}</span>
          </router-link>
        </div>
      </nav>
    </aside>

    <main class="main-content">
      <header class="top-bar">
        <div class="top-bar-left">
          <span class="page-title">{{ currentPageTitle }}</span>
        </div>
        <div class="top-bar-right">
          <div class="user-info">
            <span class="user-name">{{ userStore.user?.username }}</span>
            <el-dropdown @command="handleCommand">
              <span class="user-avatar">
                <Component :is="icons.User" class="avatar-icon" />
                <Component :is="icons.ArrowDown" class="arrow-icon" />
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </header>

      <div class="content-area">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  Bot,
  LayoutDashboard,
  FolderOpen,
  FileText,
  MessageSquare,
  Users,
  Settings,
  FileHistory,
  User,
  ArrowDown,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const icons = {
  Bot,
  LayoutDashboard,
  FolderOpen,
  FileText,
  MessageSquare,
  Users,
  Settings,
  FileHistory,
  User,
  ArrowDown,
}

const menuItems = [
  { path: '/', label: '仪表盘', icon: LayoutDashboard },
  { path: '/knowledge', label: '知识库管理', icon: FolderOpen },
  { path: '/documents', label: '文档管理', icon: FileText },
  { path: '/chat', label: '对话机器人', icon: MessageSquare },
  { path: '/system/users', label: '用户管理', icon: Users },
  { path: '/system/config', label: '系统配置', icon: Settings },
  { path: '/logs', label: '对话日志', icon: FileHistory },
]

const currentPageTitle = computed(() => {
  const item = menuItems.find((i) => i.path === route.path)
  return item?.label || '首页'
})

const handleCommand = (command) => {
  if (command === 'logout') {
    userStore.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.layout-container {
  display: flex;
  height: 100vh;
  background: #f5f7fa;
}

.sidebar {
  width: 240px;
  background: #1f2937;
  color: #fff;
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #374151;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  font-size: 28px;
  color: #3b82f6;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
}

.sidebar-nav {
  flex: 1;
  padding: 16px 0;
}

.nav-item {
  margin: 4px 12px;
  border-radius: 8px;
  transition: all 0.2s;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.nav-item.active {
  background: #3b82f6;
}

.nav-item a {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  color: #e5e7eb;
  text-decoration: none;
}

.nav-icon {
  font-size: 20px;
}

.nav-text {
  font-size: 14px;
}

.main-content {
  flex: 1;
  margin-left: 240px;
  display: flex;
  flex-direction: column;
}

.top-bar {
  height: 60px;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-name {
  font-size: 14px;
  color: #4b5563;
}

.user-avatar {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 20px;
  background: #f3f4f6;
}

.avatar-icon {
  font-size: 20px;
  color: #6b7280;
}

.arrow-icon {
  font-size: 14px;
  color: #6b7280;
}

.content-area {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}
</style>
