<template>
  <div class="profile-page fade-in">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <div class="header-icon">
          <el-icon :size="20"><UserFilled /></el-icon>
        </div>
        <div>
          <h2>个人中心</h2>
          <p class="header-subtitle">管理您的个人信息和账户设置</p>
        </div>
      </div>
    </div>

    <el-row :gutter="24">
      <!-- 左侧：头像与基本信息 -->
      <el-col :span="8">
        <el-card shadow="never" class="profile-card">
          <div class="avatar-section">
            <div class="avatar-wrapper">
              <div class="avatar-display" :style="{ background: avatarGradient }">
                <span class="avatar-text">{{ avatarText }}</span>
              </div>
              <button class="avatar-change-btn" @click="showAvatarDialog = true">
                <el-icon :size="14"><Camera /></el-icon>
              </button>
            </div>
            <h3 class="user-display-name">{{ profile.full_name || profile.username }}</h3>
            <p class="user-display-username">@{{ profile.username }}</p>
            <el-tag v-if="profile.department" type="info" size="small" effect="plain" round>
              {{ profile.department }}
            </el-tag>
          </div>

          <div class="info-list">
            <div class="info-item">
              <span class="info-label">用户名</span>
              <span class="info-value">{{ profile.username }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">邮箱</span>
              <span class="info-value">{{ profile.email || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">部门</span>
              <span class="info-value">{{ profile.department || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">注册时间</span>
              <span class="info-value">{{ formatDate(profile.created_at) }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：编辑表单 -->
      <el-col :span="16">
        <!-- 基本信息编辑 -->
        <el-card shadow="never" class="profile-card form-card">
          <div class="card-title">
            <el-icon :size="16" color="var(--primary)"><Edit /></el-icon>
            <span>基本信息</span>
          </div>
          <el-form :model="form" label-width="80px" class="profile-form">
            <el-form-item label="姓名">
              <el-input v-model="form.full_name" placeholder="请输入姓名" />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="form.email" placeholder="请输入邮箱" />
            </el-form-item>
            <el-form-item label="部门">
              <el-input v-model="form.department" placeholder="请输入部门" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveProfile" :loading="saving">
                保存修改
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 修改密码 -->
        <el-card shadow="never" class="profile-card form-card">
          <div class="card-title">
            <el-icon :size="16" color="var(--warning)"><Lock /></el-icon>
            <span>修改密码</span>
          </div>
          <el-form :model="passwordForm" label-width="80px" class="profile-form">
            <el-form-item label="原密码">
              <el-input
                v-model="passwordForm.old_password"
                type="password"
                placeholder="请输入原密码"
                show-password
              />
            </el-form-item>
            <el-form-item label="新密码">
              <el-input
                v-model="passwordForm.new_password"
                type="password"
                placeholder="请输入新密码（至少6位）"
                show-password
              />
            </el-form-item>
            <el-form-item label="确认密码">
              <el-input
                v-model="passwordForm.confirm_password"
                type="password"
                placeholder="请再次输入新密码"
                show-password
              />
            </el-form-item>
            <el-form-item>
              <el-button type="warning" @click="savePassword" :loading="changingPwd">
                修改密码
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <!-- 头像修改对话框 -->
    <el-dialog v-model="showAvatarDialog" title="修改头像" width="420px" destroy-on-close>
      <div class="avatar-dialog-body">
        <p class="avatar-hint">选择一个喜欢的头像风格</p>
        <div class="avatar-options">
          <div
            v-for="(opt, idx) in avatarOptions"
            :key="idx"
            class="avatar-option"
            :class="{ selected: selectedAvatarIdx === idx }"
            @click="selectedAvatarIdx = idx"
          >
            <div class="avatar-preview" :style="{ background: opt.gradient }">
              <span>{{ opt.text }}</span>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showAvatarDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmAvatar">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UserFilled, Camera, Edit, Lock } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

const profile = ref({
  id: 0,
  username: '',
  email: '',
  full_name: '',
  department: '',
  avatar: '',
  created_at: '',
})

const form = reactive({
  full_name: '',
  email: '',
  department: '',
})

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const saving = ref(false)
const changingPwd = ref(false)
const showAvatarDialog = ref(false)
const selectedAvatarIdx = ref(0)

const avatarOptions = [
  { gradient: 'linear-gradient(135deg, #4f6ef7, #6b8cff)', text: 'A' },
  { gradient: 'linear-gradient(135deg, #22c55e, #4ade80)', text: 'B' },
  { gradient: 'linear-gradient(135deg, #8b5cf6, #a78bfa)', text: 'C' },
  { gradient: 'linear-gradient(135deg, #f59e0b, #fbbf24)', text: 'D' },
  { gradient: 'linear-gradient(135deg, #ec4899, #f472b6)', text: 'E' },
  { gradient: 'linear-gradient(135deg, #06b6d4, #22d3ee)', text: 'F' },
]

const avatarGradient = computed(() => {
  if (profile.value.avatar) return profile.value.avatar
  return avatarOptions[0].gradient
})

const avatarText = computed(() => {
  const name = profile.value.full_name || profile.value.username || '?'
  return name.charAt(0).toUpperCase()
})

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

const loadProfile = async () => {
  try {
    const data = await request.get('/profile/')
    profile.value = data
    form.full_name = data.full_name || ''
    form.email = data.email || ''
    form.department = data.department || ''
    if (data.avatar) {
      const idx = avatarOptions.findIndex((o) => o.gradient === data.avatar)
      if (idx >= 0) selectedAvatarIdx.value = idx
    }
  } catch (e) {
    ElMessage.error('加载个人信息失败')
  }
}

const saveProfile = async () => {
  saving.value = true
  try {
    const data = await request.put('/profile/', {
      full_name: form.full_name || null,
      email: form.email || null,
      department: form.department || null,
      avatar: avatarOptions[selectedAvatarIdx.value]?.gradient || null,
    })
    profile.value = { ...profile.value, ...data }
    // 同步更新 user store
    await userStore.getProfile()
    ElMessage.success('个人信息已更新')
  } catch (e) {
    const msg = e?.response?.data?.detail || '保存失败'
    ElMessage.error(msg)
  } finally {
    saving.value = false
  }
}

const savePassword = async () => {
  if (!passwordForm.old_password || !passwordForm.new_password || !passwordForm.confirm_password) {
    ElMessage.warning('请填写完整密码信息')
    return
  }
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    ElMessage.error('两次输入的新密码不一致')
    return
  }
  if (passwordForm.new_password.length < 6) {
    ElMessage.error('新密码长度不能少于6位')
    return
  }
  changingPwd.value = true
  try {
    await request.put('/profile/password', {
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password,
    })
    ElMessage.success('密码修改成功')
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
  } catch (e) {
    const msg = e?.response?.data?.detail || '密码修改失败'
    ElMessage.error(msg)
  } finally {
    changingPwd.value = false
  }
}

const confirmAvatar = () => {
  showAvatarDialog.value = false
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.profile-page {
  padding: 24px;
  animation: fadeIn 0.35s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* 页面头部 */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--primary), var(--primary-light));
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 4px 12px rgba(79, 110, 247, 0.3);
}

.page-header h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: var(--gray-800);
}

.header-subtitle {
  margin: 2px 0 0 0;
  font-size: 13px;
  color: var(--gray-400);
}

/* 卡片通用 */
.profile-card {
  background: #fff;
  border: 1px solid var(--gray-200);
  border-radius: 12px;
  margin-bottom: 20px;
}

/* 左侧头像卡片 */
.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px 20px 20px;
  border-bottom: 1px solid var(--gray-100);
}

.avatar-wrapper {
  position: relative;
  margin-bottom: 16px;
}

.avatar-display {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 32px;
  font-weight: 700;
  box-shadow: 0 4px 16px rgba(79, 110, 247, 0.3);
}

.avatar-change-btn {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid #fff;
  background: var(--primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  transition: var(--transition);
}

.avatar-change-btn:hover {
  transform: scale(1.1);
}

.user-display-name {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--gray-800);
}

.user-display-username {
  margin: 0 0 12px 0;
  font-size: 13px;
  color: var(--gray-400);
}

/* 信息列表 */
.info-list {
  padding: 16px 20px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--gray-50);
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 13px;
  color: var(--gray-400);
}

.info-value {
  font-size: 13px;
  color: var(--gray-700);
  font-weight: 500;
}

/* 右侧表单卡片 */
.form-card {
  padding: 24px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--gray-800);
  margin-bottom: 20px;
}

.profile-form {
  max-width: 480px;
}

.profile-form :deep(.el-form-item__label) {
  font-size: 14px;
  color: var(--gray-600);
}

.profile-form :deep(.el-input__wrapper) {
  border-radius: 8px;
}

/* 头像对话框 */
.avatar-dialog-body {
  text-align: center;
}

.avatar-hint {
  font-size: 14px;
  color: var(--gray-500);
  margin: 0 0 20px 0;
}

.avatar-options {
  display: flex;
  justify-content: center;
  gap: 16px;
  flex-wrap: wrap;
}

.avatar-option {
  cursor: pointer;
  transition: var(--transition);
}

.avatar-option:hover {
  transform: scale(1.1);
}

.avatar-option.selected {
  transform: scale(1.15);
}

.avatar-preview {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 22px;
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  border: 3px solid transparent;
  transition: var(--transition);
}

.avatar-option.selected .avatar-preview {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-bg), 0 2px 8px rgba(0, 0, 0, 0.15);
}

/* 响应式 */
@media (max-width: 992px) {
  .el-col {
    flex: 0 0 100%;
    max-width: 100%;
  }
}
</style>
