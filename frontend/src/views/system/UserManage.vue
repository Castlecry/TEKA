<template>
  <div class="user-manage fade-in">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <div class="header-icon">
          <el-icon :size="24"><User /></el-icon>
        </div>
        <div>
          <h2>用户管理</h2>
          <p class="header-subtitle">管理系统用户账户、角色权限与状态</p>
        </div>
      </div>
      <el-button type="primary" icon="Plus" @click="showCreateDialog = true" class="create-btn">
        创建用户
      </el-button>
    </div>

    <!-- 搜索区域 -->
    <div class="search-section">
      <el-card shadow="never" class="search-card">
        <div class="search-bar">
          <el-input
            v-model="searchText"
            placeholder="搜索用户名..."
            prefix-icon="Search"
            clearable
            class="search-input"
            @keyup.enter="loadUsers"
          />
          <el-button type="primary" icon="Search" @click="loadUsers" class="search-btn">搜索</el-button>
        </div>
      </el-card>
    </div>

    <!-- 表格区域 -->
    <el-card shadow="never" class="table-card">
      <el-table
        :data="filteredUsers"
        :header-cell-style="{ background: 'var(--gray-50)', color: 'var(--gray-700)', fontWeight: 600 }"
        :row-class-name="tableRowClassName"
        class="user-table"
        v-loading="loading"
      >
        <el-table-column label="用户" min-width="180">
          <template #default="scope">
            <div class="user-cell">
              <div class="avatar" :style="{ background: getAvatarColor(scope.row.username) }">
                {{ getInitial(scope.row.username) }}
              </div>
              <div class="user-info">
                <span class="user-name">{{ scope.row.username }}</span>
                <span class="user-email">{{ scope.row.email }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="department" label="部门" min-width="120">
          <template #default="scope">
            <span class="dept-text">{{ scope.row.department || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="角色" min-width="140">
          <template #default="scope">
            <span
              class="role-badge"
              :class="getRoleClass(scope.row.role)"
            >
              {{ scope.row.role?.name || '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="状态" min-width="100" align="center">
          <template #default="scope">
            <el-switch
              :model-value="scope.row.status"
              @change="toggleStatus(scope.row)"
              inline-prompt
              active-text="启"
              inactive-text="禁"
              class="status-switch"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="160">
          <template #default="scope">
            <span class="time-text">{{ formatDate(scope.row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="150" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary" link @click="editUser(scope.row)">
              <el-icon><Edit /></el-icon> 编辑
            </el-button>
            <el-button size="small" type="danger" link @click="deleteUser(scope.row)">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </template>
        </el-table-column>

        <!-- 空状态 -->
        <template #empty>
          <div class="empty-state">
            <el-icon :size="48" color="var(--gray-300)"><User /></el-icon>
            <p class="empty-title">暂无用户数据</p>
            <p class="empty-desc">点击右上角「创建用户」按钮添加第一个用户</p>
          </div>
        </template>
      </el-table>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="isEdit ? '编辑用户' : '创建用户'"
      width="520px"
      destroy-on-close
      class="user-dialog"
    >
      <div class="dialog-header-icon" :class="isEdit ? 'edit' : 'create'">
        <el-icon :size="20">
          <Edit v-if="isEdit" />
          <Plus v-else />
        </el-icon>
      </div>
      <el-form :model="form" :rules="rules" ref="formRef" label-position="top" class="dialog-form">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="form.username" :disabled="isEdit" prefix-icon="User" placeholder="请输入用户名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="form.email" prefix-icon="Message" placeholder="请输入邮箱" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item :label="isEdit ? '密码（留空则不修改）' : '密码'" :prop="isEdit ? '' : 'password'">
          <el-input v-model="form.password" type="password" show-password prefix-icon="Lock" :placeholder="isEdit ? '留空则不修改' : '请输入密码'" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="部门" prop="department">
              <el-select v-model="form.department" placeholder="请选择部门" style="width: 100%">
                <el-option label="技术部" value="技术部" />
                <el-option label="产品部" value="产品部" />
                <el-option label="市场部" value="市场部" />
                <el-option label="人事部" value="人事部" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="角色" prop="role_id">
              <el-select v-model="form.role_id" placeholder="请选择角色" style="width: 100%">
                <el-option
                  v-for="role in roles"
                  :key="role.id"
                  :label="role.name"
                  :value="role.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createUser">{{ isEdit ? '更新' : '创建' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

const searchText = ref('')
const showCreateDialog = ref(false)
const formRef = ref(null)
const isEdit = ref(false)
const editingUserId = ref(null)
const roles = ref([])
const users = ref([])
const loading = ref(false)

const filteredUsers = computed(() => {
  if (!searchText.value) return users.value
  return users.value.filter(u => u.username?.includes(searchText.value))
})

const form = reactive({
  username: '',
  password: '',
  email: '',
  department: '',
  role_id: null,
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }],
  department: [{ required: true, message: '请选择部门', trigger: 'change' }],
  role_id: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

const resetForm = () => {
  isEdit.value = false
  editingUserId.value = null
  Object.assign(form, { username: '', password: '', email: '', department: '', role_id: null })
}

const getInitial = (username) => {
  if (!username) return '?'
  return username.charAt(0).toUpperCase()
}

const getAvatarColor = (username) => {
  if (!username) return 'var(--gray-400)'
  const colors = [
    '#4f6ef7', '#22c55e', '#f59e0b', '#ef4444',
    '#8b5cf6', '#ec4899', '#06b6d4', '#f97316',
  ]
  let hash = 0
  for (let i = 0; i < username.length; i++) {
    hash = username.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
}

const getRoleClass = (role) => {
  if (!role) return 'role-default'
  const name = role.name || ''
  if (name.includes('技术负责')) return 'role-danger'
  if (name.includes('团队负责')) return 'role-warning'
  if (name.includes('开发')) return 'role-success'
  return 'role-default'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit'
  })
}

const tableRowClassName = () => 'table-row-hover'

const loadUsers = async () => {
  loading.value = true
  try {
    const params = {}
    if (searchText.value) params.username = searchText.value
    const data = await request.get('/users/', { params })
    users.value = Array.isArray(data) ? data : []
  } catch (error) {
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

const loadRoles = async () => {
  try {
    const data = await request.get('/users/roles/')
    roles.value = Array.isArray(data) ? data : []
  } catch (error) {
    // 角色加载失败不阻塞
  }
}

const getRoleType = (role) => {
  if (!role) return 'info'
  const name = role.name || ''
  if (name.includes('技术负责')) return 'danger'
  if (name.includes('团队负责')) return 'warning'
  if (name.includes('开发')) return 'success'
  return 'info'
}

const toggleStatus = async (row) => {
  try {
    await request.put(`/users/${row.id}`, { status: !row.status })
    row.status = !row.status
    ElMessage.success(row.status ? '已启用' : '已禁用')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const editUser = (row) => {
  isEdit.value = true
  editingUserId.value = row.id
  Object.assign(form, {
    username: row.username,
    password: '',
    email: row.email,
    department: row.department,
    role_id: row.role?.id || null,
  })
  showCreateDialog.value = true
}

const deleteUser = async (row) => {
  try {
    await ElMessageBox.confirm('确定删除该用户？', '提示', { type: 'warning' })
    await request.delete(`/users/${row.id}`)
    ElMessage.success('删除成功')
    await loadUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const createUser = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate()
  if (!valid) return

  try {
    const payload = {
      username: form.username,
      email: form.email,
      department: form.department,
      role_id: form.role_id,
    }

    if (isEdit.value) {
      if (form.password) payload.password = form.password
      await request.put(`/users/${editingUserId.value}`, payload)
      ElMessage.success('更新成功')
    } else {
      payload.password = form.password
      await request.post('/users/', payload)
      ElMessage.success('创建成功')
    }
    showCreateDialog.value = false
    resetForm()
    await loadUsers()
  } catch (error) {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  }
}

onMounted(() => {
  loadUsers()
  loadRoles()
})
</script>

<style scoped>
.user-manage {
  padding: 24px;
  animation: fadeIn 0.35s ease-out;
}

/* 页面头部 */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  animation: slideDown 0.4s ease-out;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
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
  line-height: 1.3;
}

.header-subtitle {
  margin: 2px 0 0 0;
  font-size: 13px;
  color: var(--gray-400);
}

.create-btn {
  height: 40px;
  padding: 0 24px;
  border-radius: var(--radius-sm);
  font-weight: 500;
  transition: var(--transition);
}

.create-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 110, 247, 0.35);
}

/* 搜索区域 */
.search-section {
  margin-bottom: 20px;
  animation: slideDown 0.5s ease-out;
}

.search-card {
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-md);
}

.search-card :deep(.el-card__body) {
  padding: 16px 20px;
}

.search-bar {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-input {
  width: 260px;
}

.search-input :deep(.el-input__wrapper) {
  border-radius: var(--radius-sm);
  box-shadow: 0 0 0 1px var(--gray-200) inset;
  transition: var(--transition);
}

.search-input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--primary-light) inset;
}

.search-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--primary) inset;
}

.search-btn {
  height: 36px;
  border-radius: var(--radius-sm);
}

/* 表格区域 */
.table-card {
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-md);
  animation: slideUp 0.5s ease-out;
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

.user-table {
  border-radius: var(--radius-md);
  overflow: hidden;
}

.user-table :deep(.el-table__header th) {
  border-bottom: 2px solid var(--gray-200);
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.user-table :deep(.el-table__row) {
  transition: var(--transition);
}

.user-table :deep(.el-table__row:hover > td) {
  background: var(--primary-bg) !important;
}

/* 用户单元格 */
.user-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-name {
  font-weight: 600;
  color: var(--gray-800);
  font-size: 13px;
}

.user-email {
  font-size: 12px;
  color: var(--gray-400);
}

.dept-text {
  color: var(--gray-600);
  font-size: 13px;
}

/* 角色标签 */
.role-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.5;
}

.role-danger {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.role-warning {
  background: rgba(245, 158, 11, 0.1);
  color: #d97706;
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.role-success {
  background: rgba(34, 197, 94, 0.1);
  color: #16a34a;
  border: 1px solid rgba(34, 197, 94, 0.2);
}

.role-default {
  background: var(--gray-100);
  color: var(--gray-600);
  border: 1px solid var(--gray-200);
}

/* 状态开关 */
.status-switch :deep(.el-switch__core) {
  border-radius: 20px;
}

.time-text {
  color: var(--gray-500);
  font-size: 13px;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
}

.empty-title {
  margin-top: 16px;
  font-size: 16px;
  font-weight: 600;
  color: var(--gray-500);
}

.empty-desc {
  margin-top: 6px;
  font-size: 13px;
  color: var(--gray-400);
}

/* 对话框 */
.user-dialog :deep(.el-dialog) {
  border-radius: var(--radius-lg);
}

.dialog-header-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  color: #fff;
}

.dialog-header-icon.create {
  background: linear-gradient(135deg, var(--primary), var(--primary-light));
}

.dialog-header-icon.edit {
  background: linear-gradient(135deg, var(--warning), #fbbf24);
}

.dialog-form :deep(.el-form-item__label) {
  font-weight: 500;
  color: var(--gray-700);
  font-size: 13px;
}

.dialog-form :deep(.el-input__wrapper) {
  border-radius: var(--radius-sm);
}

.dialog-form :deep(.el-select) {
  width: 100%;
}

/* 动画 */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-12px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
