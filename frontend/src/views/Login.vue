<template>
  <div class="login-container">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="bg-circle bg-circle-1"></div>
      <div class="bg-circle bg-circle-2"></div>
      <div class="bg-circle bg-circle-3"></div>
      <div class="bg-grid"></div>
    </div>

    <div class="login-card">
      <div class="login-header">
        <div class="logo-wrapper">
          <div class="logo-icon-box">
            <div class="logo-shape">
              <div class="logo-ring"></div>
              <div class="logo-core"></div>
              <div class="logo-dot"></div>
            </div>
          </div>
        </div>
        <h1 class="logo-text">企业知识助手</h1>
        <p class="slogan">智能问答 · 知识检索 · 任务执行</p>
      </div>

      <!-- 登录表单 -->
      <el-form v-if="!isRegister" ref="formRef" :model="form" :rules="rules" class="login-form">
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            size="large"
            prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-btn"
            :loading="loading"
            @click="handleLogin"
          >
            <span v-if="!loading">登 录</span>
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 注册表单 -->
      <el-form v-else ref="regFormRef" :model="regForm" :rules="regRules" class="login-form">
        <el-form-item prop="username">
          <el-input
            v-model="regForm.username"
            placeholder="请输入用户名"
            size="large"
            prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="email">
          <el-input
            v-model="regForm.email"
            placeholder="请输入邮箱"
            size="large"
            prefix-icon="Message"
          />
        </el-form-item>

        <el-form-item prop="full_name">
          <el-input
            v-model="regForm.full_name"
            placeholder="请输入姓名"
            size="large"
            prefix-icon="UserFilled"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="regForm.password"
            type="password"
            placeholder="请输入密码（至少6位）"
            size="large"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item prop="confirm_password">
          <el-input
            v-model="regForm.confirm_password"
            type="password"
            placeholder="请再次输入密码"
            size="large"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-btn"
            :loading="loading"
            @click="handleRegister"
          >
            <span v-if="!loading">注 册</span>
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <div class="switch-link" @click="toggleMode">
          {{ isRegister ? '已有账号？去登录' : '没有账号？去注册' }}
        </div>
        <span class="default-account" v-if="!isRegister">默认账号：admin / admin123</span>
        <span class="copyright">© 2026 企业知识助手 · All Rights Reserved</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import request from '@/utils/request'

const router = useRouter()
const userStore = useUserStore()

const isRegister = ref(false)
const formRef = ref(null)
const regFormRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const regForm = reactive({
  username: '',
  email: '',
  full_name: '',
  password: '',
  confirm_password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const regRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为3-20个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
  full_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== regForm.password) {
          callback(new Error('两次输入密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

const toggleMode = () => {
  isRegister.value = !isRegister.value
}

const handleLogin = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate()
  if (!valid) return

  loading.value = true
  try {
    await userStore.login(form.username, form.password)
    // 强制刷新页面以重置所有页面状态（包括 chat 历史）
    window.location.href = '/'
  } catch (error) {
    const msg = error?.detail || '登录失败，请检查用户名和密码'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  if (!regFormRef.value) return
  const valid = await regFormRef.value.validate()
  if (!valid) return

  loading.value = true
  try {
    await request.post('/auth/register', {
      username: regForm.username,
      email: regForm.email,
      full_name: regForm.full_name,
      password: regForm.password,
    })
    ElMessage.success('注册成功，请登录')
    isRegister.value = false
    form.username = regForm.username
    regForm.username = ''
    regForm.email = ''
    regForm.full_name = ''
    regForm.password = ''
    regForm.confirm_password = ''
  } catch (error) {
    const msg = error?.response?.data?.detail || '注册失败，请重试'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1f3c 0%, #2d1b69 40%, #1e3a5f 100%);
  position: relative;
  overflow: hidden;
}

/* 背景装饰 */
.bg-decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.35;
  animation: float 8s ease-in-out infinite;
}

.bg-circle-1 {
  width: 500px;
  height: 500px;
  background: var(--primary);
  top: -150px;
  right: -100px;
  animation-delay: 0s;
}

.bg-circle-2 {
  width: 400px;
  height: 400px;
  background: #7c3aed;
  bottom: -100px;
  left: -80px;
  animation-delay: -3s;
}

.bg-circle-3 {
  width: 300px;
  height: 300px;
  background: #06b6d4;
  top: 50%;
  left: 60%;
  animation-delay: -5s;
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
  background-size: 60px 60px;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -20px) scale(1.05); }
  66% { transform: translate(-20px, 15px) scale(0.95); }
}

/* 登录卡片 */
.login-card {
  width: 420px;
  padding: 48px 40px 36px;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-radius: var(--radius-xl);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255,255,255,0.1);
  position: relative;
  z-index: 1;
  animation: cardEnter 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
}

@keyframes cardEnter {
  from {
    opacity: 0;
    transform: translateY(32px) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Logo 区域 */
.login-header {
  text-align: center;
  margin-bottom: 36px;
  animation: fadeDown 0.5s 0.2s cubic-bezier(0.16, 1, 0.3, 1) both;
}

@keyframes fadeDown {
  from { opacity: 0; transform: translateY(-12px); }
  to { opacity: 1; transform: translateY(0); }
}

.logo-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.logo-icon-box {
  width: 64px;
  height: 64px;
  border-radius: 18px;
  background: linear-gradient(135deg, var(--primary), #7c3aed);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(79, 110, 247, 0.35);
  position: relative;
}

.logo-shape {
  width: 36px;
  height: 36px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-ring {
  position: absolute;
  inset: 0;
  border: 2.5px solid rgba(255, 255, 255, 0.6);
  border-radius: 50%;
  border-top-color: transparent;
  border-right-color: transparent;
  transform: rotate(45deg);
}

.logo-core {
  width: 14px;
  height: 14px;
  background: #fff;
  border-radius: 4px;
  transform: rotate(45deg);
}

.logo-dot {
  width: 6px;
  height: 6px;
  background: #fff;
  border-radius: 50%;
  position: absolute;
  top: 2px;
  right: 2px;
  opacity: 0.8;
}

.logo-text {
  font-size: 26px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 1px;
  margin-bottom: 8px;
}

.slogan {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.55);
  letter-spacing: 2px;
}

/* 表单 */
.login-form {
  margin-bottom: 24px;
  animation: fadeUp 0.5s 0.35s cubic-bezier(0.16, 1, 0.3, 1) both;
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.login-form :deep(.el-form-item) {
  margin-bottom: 22px;
}

.login-form :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: var(--radius-md);
  box-shadow: none;
  padding: 4px 16px;
  transition: var(--transition);
}

.login-form :deep(.el-input__wrapper:hover) {
  border-color: rgba(255, 255, 255, 0.25);
  background: rgba(255, 255, 255, 0.12);
}

.login-form :deep(.el-input__wrapper.is-focus) {
  border-color: var(--primary-light);
  background: rgba(255, 255, 255, 0.12);
  box-shadow: 0 0 0 3px rgba(79, 110, 247, 0.2);
}

.login-form :deep(.el-input__inner) {
  color: #fff;
}

.login-form :deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.35);
}

.login-form :deep(.el-input__prefix .icon) {
  color: rgba(255, 255, 255, 0.45);
  font-size: 16px;
}

.login-form :deep(.el-input__suffix .icon) {
  color: rgba(255, 255, 255, 0.45);
}

/* 登录按钮 */
.login-btn {
  width: 100%;
  height: 48px;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 4px;
  border: none;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--primary), #7c3aed);
  box-shadow: 0 4px 16px rgba(79, 110, 247, 0.35);
  transition: var(--transition);
  position: relative;
  overflow: hidden;
}

.login-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, var(--primary-light), #8b5cf6);
  opacity: 0;
  transition: opacity 0.3s;
}

.login-btn:hover::before {
  opacity: 1;
}

.login-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(79, 110, 247, 0.45);
}

.login-btn:active {
  transform: translateY(0);
}

.login-btn span {
  position: relative;
  z-index: 1;
}

/* 底部 */
.login-footer {
  text-align: center;
  animation: fadeUp 0.5s 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.switch-link {
  display: block;
  font-size: 13px;
  color: var(--primary-light);
  cursor: pointer;
  margin-bottom: 8px;
  transition: var(--transition);
}

.switch-link:hover {
  color: #fff;
}

.default-account {
  display: block;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.35);
  margin-bottom: 8px;
}

.copyright {
  display: block;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.2);
}
</style>
