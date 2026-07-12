<template>
  <div class="conversation-log fade-in">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <div class="header-icon">
          <el-icon :size="24"><ChatLineSquare /></el-icon>
        </div>
        <div>
          <h2>对话日志</h2>
          <p class="header-subtitle">查看与检索用户对话记录及回答详情</p>
        </div>
      </div>
    </div>

    <!-- 搜索区域 -->
    <div class="search-section">
      <el-card shadow="never" class="search-card">
        <div class="search-bar">
          <el-input
            v-model="searchText"
            placeholder="搜索关键词..."
            prefix-icon="Search"
            clearable
            class="search-input"
            @keyup.enter="loadLogs"
          />
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            class="date-picker"
            prefix-icon="Calendar"
          />
          <el-select v-model="selectedUser" placeholder="选择用户" class="user-select" v-if="isAdmin">
            <el-option label="全部用户" value="" />
            <el-option
              v-for="u in userList"
              :key="u.id"
              :label="u.username"
              :value="u.id"
            />
          </el-select>
          <el-button type="primary" icon="Search" @click="loadLogs" class="search-btn">搜索</el-button>
          <el-button
            v-if="isAdmin && selectedLogIds.length > 0"
            type="danger"
            icon="Delete"
            @click="batchDelete"
            class="batch-delete-btn"
          >
            批量删除 ({{ selectedLogIds.length }})
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 表格区域 -->
    <el-card shadow="never" class="table-card">
      <el-table
        :data="logs"
        :header-cell-style="{ background: 'var(--gray-50)', color: 'var(--gray-700)', fontWeight: 600 }"
        class="log-table"
        v-loading="loading"
        @selection-change="handleSelectionChange"
      >
        <el-table-column v-if="isAdmin" type="selection" width="50" />
        <el-table-column prop="conversation_id" label="会话ID" min-width="180">
          <template #default="scope">
            <span class="id-text">{{ scope.row.conversation_id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="user_id" label="用户" min-width="120">
          <template #default="scope">
            <div class="user-badge">
              <div class="user-avatar" :style="{ background: getAvatarColor(scope.row.user_id) }">
                {{ getInitial(scope.row.user_id) }}
              </div>
              <span class="user-name">{{ scope.row.user_id }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="query" label="问题" min-width="200" show-overflow-tooltip>
          <template #default="scope">
            <span class="query-text">{{ scope.row.query }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="answer" label="回答" min-width="200" show-overflow-tooltip>
          <template #default="scope">
            <span class="answer-text">{{ scope.row.answer }}</span>
          </template>
        </el-table-column>
        <el-table-column label="来源知识库" min-width="140">
          <template #default="scope">
            <template v-if="scope.row.sources && scope.row.sources.length > 0">
              <el-tag v-for="s in scope.row.sources.slice(0,2)" :key="s" size="small" type="info" effect="plain" round>
                {{ typeof s === 'string' ? s : s.source || s }}
              </el-tag>
            </template>
            <span v-else class="no-data">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" min-width="160">
          <template #default="scope">
            <span class="time-text">{{ formatDate(scope.row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="160" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary" link @click="viewDetail(scope.row)">
              <el-icon><View /></el-icon> 详情
            </el-button>
            <el-button
              v-if="isAdmin"
              size="small"
              type="danger"
              link
              @click="deleteLog(scope.row)"
            >
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </template>
        </el-table-column>

        <!-- 空状态 -->
        <template #empty>
          <div class="empty-state">
            <el-icon :size="48" color="var(--gray-300)"><ChatLineSquare /></el-icon>
            <p class="empty-title">暂无对话日志</p>
            <p class="empty-desc">当用户发起对话后，日志记录将在此显示</p>
          </div>
        </template>
      </el-table>
    </el-card>

    <!-- 详情对话框 - 左右分栏布局 -->
    <el-dialog
      v-model="showDetailDialog"
      title="对话详情"
      width="900px"
      destroy-on-close
      class="detail-dialog"
    >
      <div v-if="selectedLog" class="detail-layout">
        <!-- 左侧：元数据 -->
        <div class="detail-meta">
          <div class="meta-item">
            <span class="meta-label">会话ID</span>
            <span class="meta-value id-value">{{ selectedLog.conversation_id }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">用户</span>
            <div class="meta-user">
              <div class="meta-avatar" :style="{ background: getAvatarColor(selectedLog.user_id) }">
                {{ getInitial(selectedLog.user_id) }}
              </div>
              <span>{{ selectedLog.user_id }}</span>
            </div>
          </div>
          <div class="meta-item">
            <span class="meta-label">时间</span>
            <span class="meta-value">{{ formatDate(selectedLog.created_at) }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">来源</span>
            <span class="meta-value">
              {{ (selectedLog.sources && selectedLog.sources.length) ? selectedLog.sources.join(', ') : '-' }}
            </span>
          </div>
        </div>

        <!-- 右侧：问答内容 -->
        <div class="detail-content">
          <div class="qa-section">
            <div class="qa-label question-label">
              <el-icon :size="16"><QuestionFilled /></el-icon>
              <span>问题</span>
            </div>
            <div class="qa-body question-body">
              <p>{{ selectedLog.query }}</p>
            </div>
          </div>
          <div class="qa-divider"></div>
          <div class="qa-section">
            <div class="qa-label answer-label">
              <el-icon :size="16"><ChatDotRound /></el-icon>
              <span>回答</span>
            </div>
            <div class="qa-body answer-body">
              <MarkdownRenderer :content="selectedLog.answer" />
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import request from '@/utils/request'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const isAdmin = computed(() => userStore.isAdmin)

const searchText = ref('')
const dateRange = ref([])
const selectedUser = ref('')
const showDetailDialog = ref(false)
const selectedLog = ref(null)
const loading = ref(false)
const selectedLogIds = ref([])
const userList = ref([])

const logs = ref([])

const getInitial = (userId) => {
  if (!userId && userId !== 0) return '?'
  const str = String(userId)
  return str.charAt(0).toUpperCase()
}

const getAvatarColor = (userId) => {
  if (!userId && userId !== 0) return 'var(--gray-400)'
  const str = String(userId)
  const colors = [
    '#4f6ef7', '#22c55e', '#f59e0b', '#ef4444',
    '#8b5cf6', '#ec4899', '#06b6d4', '#f97316',
  ]
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
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

const loadLogs = async () => {
  loading.value = true
  try {
    const params = {}
    if (searchText.value) params.search = searchText.value
    if (selectedUser.value) params.user_id = selectedUser.value
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const data = await request.get('/chat/logs', { params })
    logs.value = Array.isArray(data) ? data : []
  } catch (error) {
    ElMessage.error('加载对话日志失败')
  } finally {
    loading.value = false
  }
}

const loadUsers = async () => {
  if (!isAdmin.value) return
  try {
    const data = await request.get('/users/')
    userList.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error('加载用户列表失败', error)
  }
}

const viewDetail = async (row) => {
  try {
    const data = await request.get(`/chat/history/${row.conversation_id}`)
    selectedLog.value = { ...row, ...data }
    showDetailDialog.value = true
  } catch (error) {
    ElMessage.error('加载对话详情失败')
  }
}

const handleSelectionChange = (rows) => {
  selectedLogIds.value = rows.map(r => r.id)
}

const deleteLog = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除这条对话日志吗？此操作不可恢复。`,
      '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
    await request.delete(`/chat/logs/${row.id}`)
    ElMessage.success('日志已删除')
    loadLogs()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error?.detail || '删除失败')
    }
  }
}

const batchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedLogIds.value.length} 条日志吗？此操作不可恢复。`,
      '批量删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
    await request.delete('/chat/logs', { data: selectedLogIds.value })
    ElMessage.success('批量删除成功')
    selectedLogIds.value = []
    loadLogs()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error?.detail || '批量删除失败')
    }
  }
}

onMounted(() => {
  loadLogs()
  loadUsers()
})
</script>

<style scoped>
.conversation-log {
  padding: 24px;
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
  flex-wrap: wrap;
}

.search-input {
  width: 220px;
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

.date-picker {
  width: 280px;
}

.date-picker :deep(.el-input__wrapper) {
  border-radius: var(--radius-sm);
  box-shadow: 0 0 0 1px var(--gray-200) inset;
  transition: var(--transition);
}

.date-picker :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--primary-light) inset;
}

.user-select {
  width: 150px;
}

.user-select :deep(.el-input__wrapper) {
  border-radius: var(--radius-sm);
  box-shadow: 0 0 0 1px var(--gray-200) inset;
  transition: var(--transition);
}

.user-select :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--primary-light) inset;
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

.log-table {
  border-radius: var(--radius-md);
  overflow: hidden;
}

.log-table :deep(.el-table__header th) {
  border-bottom: 2px solid var(--gray-200);
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.log-table :deep(.el-table__row) {
  transition: var(--transition);
}

.log-table :deep(.el-table__row:hover > td) {
  background: var(--primary-bg) !important;
}

.id-text {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--gray-500);
}

/* 用户徽章 */
.user-badge {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 600;
  font-size: 12px;
  flex-shrink: 0;
}

.user-name {
  font-weight: 500;
  color: var(--gray-700);
  font-size: 13px;
}

.query-text {
  color: var(--gray-700);
  font-size: 13px;
}

.answer-text {
  color: var(--gray-600);
  font-size: 13px;
}

.no-data {
  color: var(--gray-400);
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

/* 详情对话框 */
.detail-dialog :deep(.el-dialog) {
  border-radius: var(--radius-lg);
}

.detail-layout {
  display: flex;
  gap: 24px;
  min-height: 400px;
}

/* 左侧元数据 */
.detail-meta {
  width: 220px;
  flex-shrink: 0;
  background: var(--gray-50);
  border-radius: var(--radius-md);
  padding: 20px;
  border: 1px solid var(--gray-200);
}

.meta-item {
  margin-bottom: 20px;
}

.meta-item:last-child {
  margin-bottom: 0;
}

.meta-label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  color: var(--gray-400);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}

.meta-value {
  font-size: 13px;
  color: var(--gray-700);
  word-break: break-all;
}

.id-value {
  font-family: var(--font-mono);
  font-size: 12px;
}

.meta-user {
  display: flex;
  align-items: center;
  gap: 8px;
}

.meta-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 600;
  font-size: 12px;
  flex-shrink: 0;
}

/* 右侧问答内容 */
.detail-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.qa-section {
  flex: 1;
}

.qa-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}

.question-label {
  color: var(--primary);
}

.answer-label {
  color: var(--success);
}

.qa-body {
  border-radius: var(--radius-md);
  padding: 16px;
}

.question-body {
  background: var(--primary-bg);
  border: 1px solid rgba(79, 110, 247, 0.15);
}

.question-body p {
  margin: 0;
  color: var(--gray-800);
  font-size: 14px;
  line-height: 1.6;
}

.qa-divider {
  height: 1px;
  background: var(--gray-200);
  margin: 20px 0;
}

.answer-body {
  background: var(--gray-50);
  border: 1px solid var(--gray-200);
}

/* 动画 */
@keyframes slideDown {
  from { opacity: 0; transform: translateY(-12px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
