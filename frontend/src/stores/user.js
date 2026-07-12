import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const login = async (username, password) => {
    const res = await request.post('/auth/login', { username, password })
    if (res.code === 200) {
      token.value = res.data.token
      user.value = res.data.user
      localStorage.setItem('token', token.value)
      localStorage.setItem('user', JSON.stringify(user.value))
    }
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
    if (res.code === 200) {
      user.value = res.data
      localStorage.setItem('user', JSON.stringify(user.value))
    }
    return res
  }

  return { token, user, login, logout, getProfile }
})
