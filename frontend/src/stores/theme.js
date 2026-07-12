import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  // 预设主题色
  const presetThemes = {
    blue: {
      name: '科技蓝',
      primary: '#4f6ef7',
      primaryLight: '#6b8cff',
      primaryDark: '#3b5de7',
      primaryBg: '#f0f3ff'
    },
    purple: {
      name: '优雅紫',
      primary: '#8b5cf6',
      primaryLight: '#a78bfa',
      primaryDark: '#7c3aed',
      primaryBg: '#f5f3ff'
    },
    green: {
      name: '清新绿',
      primary: '#22c55e',
      primaryLight: '#4ade80',
      primaryDark: '#16a34a',
      primaryBg: '#f0fdf4'
    },
    orange: {
      name: '活力橙',
      primary: '#f59e0b',
      primaryLight: '#fbbf24',
      primaryDark: '#d97706',
      primaryBg: '#fffbeb'
    },
    pink: {
      name: '浪漫粉',
      primary: '#ec4899',
      primaryLight: '#f472b6',
      primaryDark: '#db2777',
      primaryBg: '#fdf2f8'
    },
    cyan: {
      name: '湖光青',
      primary: '#06b6d4',
      primaryLight: '#22d3ee',
      primaryDark: '#0891b2',
      primaryBg: '#ecfeff'
    }
  }

  // 当前主题key
  const currentTheme = ref(localStorage.getItem('theme') || 'blue')

  // 应用主题到CSS变量
  const applyTheme = (themeKey) => {
    const theme = presetThemes[themeKey]
    if (!theme) return

    document.documentElement.style.setProperty('--primary', theme.primary)
    document.documentElement.style.setProperty('--primary-light', theme.primaryLight)
    document.documentElement.style.setProperty('--primary-dark', theme.primaryDark)
    document.documentElement.style.setProperty('--primary-bg', theme.primaryBg)
  }

  // 切换主题
  const setTheme = (themeKey) => {
    currentTheme.value = themeKey
    localStorage.setItem('theme', themeKey)
    applyTheme(themeKey)
  }

  // 初始化时应用保存的主题
  const initTheme = () => {
    applyTheme(currentTheme.value)
  }

  // 监听主题变化
  watch(currentTheme, (newTheme) => {
    applyTheme(newTheme)
  })

  return {
    currentTheme,
    presetThemes,
    setTheme,
    initTheme,
    applyTheme
  }
})
