import { defineStore } from 'pinia'
import { ref } from 'vue'
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

  return { token, user, login, logout, getProfile }
})
