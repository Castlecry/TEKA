<template>
  <div class="user-manage">
    <div class="page-header">
      <h2>用户管理</h2>
      <el-button type="primary" icon="Plus" @click="showCreateDialog = true">创建用户</el-button>
    </div>

    <el-card>
      <div class="search-bar">
        <el-input placeholder="搜索用户名" v-model="searchText" style="width: 200px" />
        <el-select placeholder="选择角色" v-model="selectedRole" style="width: 120px">
          <el-option label="全部" value="" />
          <el-option label="超级管理员" value="admin" />
          <el-option label="部门管理员" value="dept_admin" />
          <el-option label="普通用户" value="user" />
        </el-select>
        <el-button icon="Search" @click="loadUsers">搜索</el-button>
      </div>

      <el-table :data="users" border>
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="department" label="部门" />
        <el-table-column prop="role" label="角色">
          <template #default="scope">
            <el-tag :type="getRoleType(scope.row.role)">
              {{ getRoleName(scope.row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态">
          <template #default="scope">
            <el-switch
              :value="scope.row.status === 'active'"
              @change="toggleStatus(scope.row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" />
        <el-table-column label="操作">
          <template #default="scope">
            <el-button size="small" @click="editUser(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteUser(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showCreateDialog" title="创建用户" width="500px">
      <el-form :model="form" :rules="rules" ref="formRef">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="部门" prop="department">
          <el-select v-model="form.department">
            <el-option label="技术部" value="技术部" />
            <el-option label="产品部" value="产品部" />
            <el-option label="市场部" value="市场部" />
            <el-option label="人事部" value="人事部" />
          </el-select>
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role">
            <el-option label="超级管理员" value="admin" />
            <el-option label="部门管理员" value="dept_admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createUser">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'

const searchText = ref('')
const selectedRole = ref('')
const showCreateDialog = ref(false)
const formRef = ref(null)

const form = reactive({
  username: '',
  password: '',
  email: '',
  department: '',
  role: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }],
}

const users = ref([
  { id: 1, username: 'admin', email: 'admin@example.com', department: '技术部', role: 'admin', status: 'active', created_at: '2024-01-01' },
  { id: 2, username: 'zhangsan', email: 'zhangsan@example.com', department: '技术部', role: 'dept_admin', status: 'active', created_at: '2024-01-10' },
  { id: 3, username: 'lisi', email: 'lisi@example.com', department: '产品部', role: 'user', status: 'active', created_at: '2024-01-15' },
  { id: 4, username: 'wangwu', email: 'wangwu@example.com', department: '市场部', role: 'user', status: 'inactive', created_at: '2024-01-20' },
])

const loadUsers = () => {}

const getRoleType = (role) => {
  const types = { admin: 'danger', dept_admin: 'warning', user: 'info' }
  return types[role] || 'info'
}

const getRoleName = (role) => {
  const names = { admin: '超级管理员', dept_admin: '部门管理员', user: '普通用户' }
  return names[role] || role
}

const toggleStatus = (row) => {
  row.status = row.status === 'active' ? 'inactive' : 'active'
  ElMessage.success(row.status === 'active' ? '已启用' : '已禁用')
}

const editUser = (row) => {}

const deleteUser = (row) => {
  ElMessageBox.confirm('确定删除该用户？', '提示', { type: 'warning' }).then(() => {
    ElMessage.success('删除成功')
  })
}

const createUser = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate()
  if (!valid) return

  showCreateDialog.value = false
  ElMessage.success('创建成功')
  Object.assign(form, { username: '', password: '', email: '', department: '', role: '' })
}
</script>

<style scoped>
.user-manage {
  padding: 20px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
</style>
