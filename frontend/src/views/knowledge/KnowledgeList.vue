<template>
  <div class="knowledge-list">
    <!-- 页面头部 -->
    <div class="page-header fade-in">
      <div class="header-left">
        <div class="header-icon">
          <el-icon :size="28"><Collection /></el-icon>
        </div>
        <div class="header-text">
          <h2>知识库管理</h2>
          <p class="subtitle">管理和组织知识库资源，支持多模块协作</p>
        </div>
      </div>
      <el-button v-if="isAdmin || true" type="primary" class="create-btn" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        <span>创建知识库</span>
      </el-button>
    </div>

    <!-- 搜索和筛选区域 -->
    <div class="search-section fade-in-delay">
      <el-card shadow="never" class="search-card">
        <div class="search-bar">
          <div class="search-input-wrapper">
            <el-icon class="search-icon"><Search /></el-icon>
            <el-input
              v-model="searchText"
              placeholder="搜索知识库名称..."
              class="search-input"
              @keyup.enter="loadKnowledgeBases"
            />
          </div>
          <el-select v-model="selectedModule" placeholder="选择模块" class="module-select" clearable>
            <el-option label="全部模块" value="" />
            <el-option v-for="mod in modules" :key="mod.id" :label="mod.name" :value="mod.id" />
          </el-select>
          <el-button type="primary" @click="loadKnowledgeBases" class="search-btn">
            <el-icon><Search /></el-icon>
            <span>搜索</span>
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 表格区域 -->
    <div class="table-section fade-in-delay-2">
      <el-card shadow="never" class="table-card" v-if="knowledgeBases.length > 0">
        <el-table
          :data="knowledgeBases"
          class="custom-table"
          :row-class-name="'table-row'"
          @row-mouseenter="handleRowHover"
        >
          <el-table-column prop="name" label="知识库名称" min-width="180">
            <template #default="scope">
              <div class="kb-name-cell">
                <div class="kb-icon" :style="{ background: getModuleColor(scope.row.module) + '15', color: getModuleColor(scope.row.module) }">
                  <el-icon :size="18"><FolderOpened /></el-icon>
                </div>
                <div>
                  <span class="kb-name">{{ scope.row.name }}</span>
                  <div class="kb-meta">
                    <el-tag size="small" :type="getModuleTagType(scope.row.module)" effect="plain">
                      {{ getModuleName(scope.row.module) }}
                    </el-tag>
                    <el-tag v-if="scope.row.is_shared" size="small" type="warning" effect="plain">共享</el-tag>
                    <el-tag v-if="scope.row.is_personal" size="small" type="info" effect="plain">个人</el-tag>
                    <el-tag v-if="scope.row.is_locked" size="small" type="danger" effect="plain">内置</el-tag>
                  </div>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          <el-table-column prop="document_count" label="文档数量" width="110" align="center">
            <template #default="scope">
              <span class="doc-count">{{ scope.row.document_count || 0 }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="scope">
              {{ formatDate(scope.row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="scope">
              <span :class="['status-dot', scope.row.status ? 'active' : 'inactive']"></span>
              <el-tag :type="scope.row.status ? 'success' : 'danger'" size="small" effect="light" round>
                {{ scope.row.status ? '活跃' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="220" align="center" fixed="right">
            <template #default="scope">
              <div class="action-btns">
                <el-button type="primary" link size="small" @click="viewDetail(scope.row)">
                  <el-icon><View /></el-icon>
                  <span>详情</span>
                </el-button>
                <el-button
                  v-if="canEdit(scope.row)"
                  type="warning" link size="small" @click="editKnowledge(scope.row)"
                >
                  <el-icon><Edit /></el-icon>
                  <span>编辑</span>
                </el-button>
                <el-button
                  v-if="canDelete(scope.row)"
                  type="danger" link size="small" @click="deleteKnowledge(scope.row)"
                >
                  <el-icon><Delete /></el-icon>
                  <span>删除</span>
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 空状态 -->
      <div v-else class="empty-state">
        <div class="empty-icon">
          <el-icon :size="64"><FolderOpened /></el-icon>
        </div>
        <h3>暂无知识库</h3>
        <p>您还没有创建任何知识库，点击下方按钮开始创建</p>
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          <span>创建第一个知识库</span>
        </el-button>
      </div>
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="showDialog" title="" width="520px" class="create-dialog" :show-close="true">
      <template #header>
        <div class="dialog-header">
          <div class="dialog-icon">
            <el-icon :size="22"><Plus /></el-icon>
          </div>
          <div>
            <h3>{{ isEditing ? '编辑知识库' : '创建知识库' }}</h3>
            <p>{{ isEditing ? '修改知识库信息' : '填写以下信息来创建一个新的知识库' }}</p>
          </div>
        </div>
      </template>
      <el-form :model="form" :rules="rules" ref="formRef" class="create-form" label-position="top">
        <el-form-item label="知识库名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入知识库描述（可选）"
          />
        </el-form-item>
        <el-form-item label="所属模块" prop="module">
          <el-select v-model="form.module" placeholder="请选择所属模块" style="width: 100%">
            <el-option v-for="mod in modules" :key="mod.id" :label="mod.name" :value="mod.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="isAdmin" label="类型">
          <el-radio-group v-model="form.is_personal">
            <el-radio :value="false">共享知识库（所有用户可见）</el-radio>
            <el-radio :value="true">个人知识库（仅自己可见）</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showDialog = false">取消</el-button>
          <el-button type="primary" @click="saveKnowledge">
            <el-icon><Check /></el-icon>
            <span>{{ isEditing ? '保存' : '创建' }}</span>
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const isAdmin = computed(() => userStore.isAdmin)

const searchText = ref('')
const selectedModule = ref('')
const showDialog = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const formRef = ref(null)
const modules = ref([])

const form = reactive({
  name: '',
  description: '',
  module: 'general',
  is_personal: false,
})

const rules = {
  name: [{ required: true, message: '请输入知识库名称', trigger: 'blur' }],
  module: [{ required: true, message: '请选择所属模块', trigger: 'change' }],
}

const knowledgeBases = ref([])

const moduleColorMap = { policy: '#4f6ef7', tech: '#22c55e', admin: '#f59e0b', general: '#8b5cf6' }
const moduleNameMap = { policy: '规章制度', tech: '产品技术', admin: '行政服务', general: '自由问答' }

const getModuleColor = (mod) => moduleColorMap[mod] || '#8b5cf6'
const getModuleName = (mod) => moduleNameMap[mod] || mod
const getModuleTagType = (mod) => {
  const types = { policy: '', tech: 'success', admin: 'warning', general: 'info' }
  return types[mod] || 'info'
}

const canEdit = (row) => {
  if (row.is_locked) return false
  if (isAdmin.value) return true
  if (row.is_personal && row.owner_id === userStore.user?.id) return true
  return false
}

const canDelete = (row) => {
  if (row.is_locked) return false
  if (isAdmin.value) return true
  if (row.is_personal && row.owner_id === userStore.user?.id) return true
  return false
}

const loadModules = async () => {
  try {
    modules.value = await request.get('/knowledge-bases/modules')
  } catch (e) {
    console.error('加载模块列表失败', e)
  }
}

const loadKnowledgeBases = async () => {
  try {
    const params = {}
    if (searchText.value) params.name = searchText.value
    if (selectedModule.value) params.module = selectedModule.value
    const data = await request.get('/knowledge-bases/', { params })
    knowledgeBases.value = data
  } catch (error) {
    ElMessage.error('加载知识库列表失败')
  }
}

const viewDetail = (row) => {
  router.push(`/knowledge/${row.id}`)
}

const openCreateDialog = () => {
  isEditing.value = false
  editingId.value = null
  form.name = ''
  form.description = ''
  form.module = 'general'
  form.is_personal = !isAdmin.value
  showDialog.value = true
}

const editKnowledge = (row) => {
  isEditing.value = true
  editingId.value = row.id
  form.name = row.name
  form.description = row.description || ''
  form.module = row.module || 'general'
  form.is_personal = row.is_personal || false
  showDialog.value = true
}

const handleRowHover = () => {}

const deleteKnowledge = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除知识库「${row.name}」？`, '提示', { type: 'warning' })
    await request.delete(`/knowledge-bases/${row.id}`)
    ElMessage.success('删除成功')
    await loadKnowledgeBases()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error?.response?.data?.detail || '删除失败')
    }
  }
}

const saveKnowledge = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  try {
    if (isEditing.value) {
      await request.put(`/knowledge-bases/${editingId.value}`, {
        name: form.name,
        description: form.description,
        module: form.module,
      })
      ElMessage.success('修改成功')
    } else {
      await request.post('/knowledge-bases/', {
        name: form.name,
        description: form.description,
        module: form.module,
      }, { params: { is_personal: form.is_personal } })
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    await loadKnowledgeBases()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '操作失败')
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  loadModules()
  loadKnowledgeBases()
})
</script>

<style scoped>
.knowledge-list { padding: 24px; min-height: 100%; background: var(--gray-50, #f9fafb); }
.fade-in { animation: fadeInUp 0.5s ease-out; }
.fade-in-delay { animation: fadeInUp 0.5s ease-out 0.1s both; }
.fade-in-delay-2 { animation: fadeInUp 0.5s ease-out 0.2s both; }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }

.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; padding: 24px 28px; background: #fff; border-radius: 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); border: 1px solid var(--gray-100, #f3f4f6); }
.header-left { display: flex; align-items: center; gap: 16px; }
.header-icon { width: 52px; height: 52px; border-radius: 10px; background: linear-gradient(135deg, var(--primary, #4f6ef7), var(--primary-light, #6b8cff)); display: flex; align-items: center; justify-content: center; color: #fff; flex-shrink: 0; }
.header-text h2 { margin: 0 0 4px 0; font-size: 22px; font-weight: 700; color: var(--gray-800, #1f2937); }
.subtitle { margin: 0; font-size: 14px; color: var(--gray-500, #6b7280); }
.create-btn { display: flex; align-items: center; gap: 6px; padding: 10px 22px; border-radius: 6px; font-weight: 600; font-size: 14px; transition: all 0.25s; box-shadow: 0 2px 8px rgba(79, 110, 247, 0.3); }
.create-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(79, 110, 247, 0.4); }

.search-card { border-radius: 16px; border: 1px solid var(--gray-100, #f3f4f6); }
.search-card :deep(.el-card__body) { padding: 16px 20px; }
.search-bar { display: flex; align-items: center; gap: 12px; }
.search-input-wrapper { position: relative; flex: 1; max-width: 320px; }
.search-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: var(--gray-400, #9ca3af); z-index: 1; font-size: 16px; }
.search-input :deep(.el-input__wrapper) { padding-left: 38px; border-radius: 6px; box-shadow: none; border: 1px solid var(--gray-200, #e5e7eb); }
.search-input :deep(.el-input__wrapper):hover, .search-input :deep(.el-input__wrapper).is-focus { border-color: var(--primary, #4f6ef7); box-shadow: 0 0 0 3px rgba(79, 110, 247, 0.1); }
.module-select { width: 160px; }
.module-select :deep(.el-input__wrapper) { border-radius: 6px; box-shadow: none; border: 1px solid var(--gray-200, #e5e7eb); }
.search-btn { display: flex; align-items: center; gap: 4px; border-radius: 6px; padding: 8px 18px; }

.table-card { border-radius: 16px; border: 1px solid var(--gray-100, #f3f4f6); }
.table-card :deep(.el-card__body) { padding: 0; }
.custom-table { --el-table-border-color: var(--gray-100, #f3f4f6); }
.custom-table :deep(.el-table__header th) { background: var(--gray-50, #f9fafb); color: var(--gray-600, #4b5563); font-weight: 600; font-size: 13px; padding: 14px 0; border-bottom: 2px solid var(--gray-100, #f3f4f6); }
.custom-table :deep(.el-table__row:hover > td) { background: var(--primary-bg, #f0f3ff) !important; }
.custom-table :deep(td) { padding: 14px 0; font-size: 14px; color: var(--gray-700, #374151); }

.kb-name-cell { display: flex; align-items: center; gap: 10px; }
.kb-icon { width: 34px; height: 34px; border-radius: 6px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.kb-name { font-weight: 600; color: var(--gray-800, #1f2937); }
.kb-meta { display: flex; gap: 6px; margin-top: 4px; }

.doc-count { display: inline-flex; align-items: center; justify-content: center; min-width: 28px; height: 28px; border-radius: 14px; background: var(--gray-100, #f3f4f6); font-weight: 600; font-size: 13px; color: var(--gray-700, #374151); }

.status-dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; margin-right: 6px; vertical-align: middle; }
.status-dot.active { background: var(--success, #22c55e); box-shadow: 0 0 6px rgba(34, 197, 94, 0.4); }
.status-dot.inactive { background: var(--danger, #ef4444); box-shadow: 0 0 6px rgba(239, 68, 68, 0.4); }

.action-btns { display: flex; align-items: center; justify-content: center; gap: 4px; }
.action-btns .el-button { display: flex; align-items: center; gap: 3px; font-size: 13px; padding: 4px 8px; border-radius: 6px; }
.action-btns .el-button:hover { background: var(--gray-50, #f9fafb); }

.empty-state { text-align: center; padding: 80px 20px; background: #fff; border-radius: 16px; border: 1px solid var(--gray-100, #f3f4f6); }
.empty-icon { color: var(--gray-300, #d1d5db); margin-bottom: 20px; }
.empty-state h3 { margin: 0 0 8px 0; font-size: 18px; color: var(--gray-700, #374151); font-weight: 600; }
.empty-state p { margin: 0 0 24px 0; font-size: 14px; color: var(--gray-500, #6b7280); }

.create-dialog :deep(.el-dialog) { border-radius: 16px; overflow: hidden; }
.dialog-header { display: flex; align-items: center; gap: 14px; }
.dialog-icon { width: 44px; height: 44px; border-radius: 10px; background: linear-gradient(135deg, var(--primary, #4f6ef7), var(--primary-light, #6b8cff)); display: flex; align-items: center; justify-content: center; color: #fff; flex-shrink: 0; }
.dialog-header h3 { margin: 0 0 2px 0; font-size: 18px; font-weight: 700; color: var(--gray-800, #1f2937); }
.dialog-header p { margin: 0; font-size: 13px; color: var(--gray-500, #6b7280); }
.create-form { padding-top: 8px; }
.create-form :deep(.el-form-item__label) { font-weight: 600; color: var(--gray-700, #374151); font-size: 13px; }
.create-form :deep(.el-input__wrapper), .create-form :deep(.el-textarea__inner) { border-radius: 6px; border: 1px solid var(--gray-200, #e5e7eb); }
.create-form :deep(.el-input__wrapper):hover, .create-form :deep(.el-input__wrapper).is-focus, .create-form :deep(.el-textarea__inner:hover), .create-form :deep(.el-textarea__inner:focus) { border-color: var(--primary, #4f6ef7); box-shadow: 0 0 0 3px rgba(79, 110, 247, 0.1); }
.dialog-footer { display: flex; justify-content: flex-end; gap: 10px; }
.dialog-footer .el-button { padding: 8px 20px; border-radius: 6px; font-weight: 600; }
</style>
