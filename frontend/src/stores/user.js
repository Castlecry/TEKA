import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/utils/request'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const login = async (username, password) => {
    const res = await request.post('/auth/login/json', { username, password })
    token.value = res.access_token
    localStorage.setItem('token', token.value)
    // 登录后获取用户信息
    await getProfile()
    return res
  }

  const logout = () => {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  const getProfile = async () => {
    const res = await request.get('/auth/me')
    user.value = res
    localStorage.setItem('user', JSON.stringify(user.value))
    return res
  }

  // 检查用户是否有特定权限
  const hasPermission = (permission) => {
    if (!user.value || !user.value.role) return false
    const permissions = user.value.role.permissions || []
    // 如果有'all'权限，则拥有所有权限
    if (permissions.includes('all')) return true
    return permissions.includes(permission)
  }

  // 检查用户是否是管理员（技术负责人）
  const isAdmin = computed(() => {
    if (!user.value || !user.value.role) return false
    return user.value.role.name === '管理员' || user.value.role.permissions?.includes('all')
  })

  return { token, user, login, logout, getProfile, hasPermission, isAdmin }
})
