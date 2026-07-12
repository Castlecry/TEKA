<template>
  <div class="knowledge-detail">
    <!-- 面包屑导航 -->
    <div class="breadcrumb-section fade-in">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/knowledge' }">
          <el-icon><Collection /></el-icon>
          <span>知识库管理</span>
        </el-breadcrumb-item>
        <el-breadcrumb-item>
          <el-icon><FolderOpened /></el-icon>
          <span>{{ knowledge.name || '知识库详情' }}</span>
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <!-- 页面头部 -->
    <div class="page-header fade-in-delay">
      <div class="header-left">
        <el-button class="back-btn" @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回</span>
        </el-button>
        <div class="header-icon">
          <el-icon :size="28"><FolderOpened /></el-icon>
        </div>
        <div class="header-text">
          <h2>{{ knowledge.name }}</h2>
          <p class="subtitle">{{ knowledge.department }} · 创建于 {{ knowledge.created_at }}</p>
        </div>
      </div>
      <el-button type="primary" class="edit-btn" @click="showEditDialog = true">
        <el-icon><Edit /></el-icon>
        <span>编辑</span>
      </el-button>
    </div>

    <!-- 内容区域 -->
    <el-row :gutter="24" class="content-section fade-in-delay-2">
      <!-- 基本信息卡片 -->
      <el-col :span="8">
        <el-card shadow="never" class="info-card">
          <template #header>
            <div class="card-header">
              <el-icon :size="20"><InfoFilled /></el-icon>
              <span>基本信息</span>
            </div>
          </template>
          <div class="info-content">
            <div class="info-item">
              <div class="info-label">
                <el-icon><Document /></el-icon>
                <span>描述</span>
              </div>
              <div class="info-value">{{ knowledge.description || '暂无描述' }}</div>
            </div>
            <div class="info-item">
              <div class="info-label">
                <el-icon><OfficeBuilding /></el-icon>
                <span>所属部门</span>
              </div>
              <div class="info-value">
                <span class="dept-badge">{{ knowledge.department }}</span>
              </div>
            </div>
            <div class="info-item">
              <div class="info-label">
                <el-icon><Calendar /></el-icon>
                <span>创建时间</span>
              </div>
              <div class="info-value">{{ knowledge.created_at }}</div>
            </div>
            <div class="info-item">
              <div class="info-label">
                <el-icon><CircleCheck /></el-icon>
                <span>状态</span>
              </div>
              <div class="info-value">
                <span :class="['status-indicator', knowledge.status ? 'active' : 'inactive']">
                  <span class="status-dot"></span>
                  <el-tag :type="knowledge.status ? 'success' : 'danger'" size="small" effect="light" round>
                    {{ knowledge.status ? '活跃' : '停用' }}
                  </el-tag>
                </span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 文档列表 -->
      <el-col :span="16">
        <el-card shadow="never" class="docs-card">
          <template #header>
            <div class="card-header">
              <div class="card-title">
                <el-icon :size="20"><Document /></el-icon>
                <span>文档列表</span>
                <span class="doc-count-badge">{{ documents.length }}</span>
              </div>
              <div class="doc-actions">
                <el-button type="primary" class="upload-btn" @click="showUploadDialog = true">
                  <el-icon><Upload /></el-icon>
                  <span>上传文档</span>
                </el-button>
                <el-button @click="loadDocuments">
                  <el-icon><Refresh /></el-icon>
                  <span>刷新</span>
                </el-button>
              </div>
            </div>
          </template>

          <el-table
            :data="documents"
            class="docs-table"
            v-if="documents.length > 0"
          >
            <el-table-column prop="filename" label="文件名" min-width="200">
              <template #default="scope">
                <div class="file-name-cell">
                  <div :class="['file-icon', getFileType(scope.row.filename)]">
                    <el-icon :size="16"><Document /></el-icon>
                  </div>
                  <span class="file-name">{{ scope.row.filename }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="大小" width="110" align="center">
              <template #default="scope">
                <span class="file-size">{{ formatFileSize(scope.row.size) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="uploaded_at" label="上传时间" width="170" />
            <el-table-column prop="chunk_count" label="切片数量" width="110" align="center">
              <template #default="scope">
                <span class="chunk-count">{{ scope.row.chunk_count || 0 }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="120" align="center">
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.status)" size="small" effect="light" round>
                  {{ getStatusText(scope.row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="240" align="center" fixed="right">
              <template #default="scope">
                <div class="action-btns">
                  <el-button type="primary" link size="small" @click="previewDocument(scope.row)">
                    <el-icon><View /></el-icon>
                    <span>预览</span>
                  </el-button>
                  <el-button
                    type="warning" link size="small"
                    @click="regenerateDocument(scope.row)"
                    :loading="scope.row._regenerating"
                  >
                    <el-icon><RefreshRight /></el-icon>
                    <span>重新生成</span>
                  </el-button>
                  <el-button type="danger" link size="small" @click="deleteDocument(scope.row)">
                    <el-icon><Delete /></el-icon>
                    <span>删除</span>
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>

          <div v-else class="empty-docs">
            <el-icon :size="48"><Document /></el-icon>
            <p>暂无文档</p>
            <el-button type="primary" @click="showUploadDialog = true">
              <el-icon><Upload /></el-icon>
              <span>上传第一个文档</span>
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 上传对话框 -->
    <el-dialog v-model="showUploadDialog" title="" width="560px" class="upload-dialog">
      <template #header>
        <div class="dialog-header">
          <div class="dialog-icon">
            <el-icon :size="22"><Upload /></el-icon>
          </div>
          <div>
            <h3>上传文档</h3>
            <p>支持 PDF、DOCX、TXT、MD 格式，可批量上传</p>
          </div>
        </div>
      </template>

      <el-upload
        class="upload-area"
        drag
        action="/api/documents/upload"
        :auto-upload="false"
        :on-change="handleFileChange"
        accept=".pdf,.docx,.txt,.md"
        multiple
      >
        <el-icon class="upload-icon"><Upload /></el-icon>
        <div class="upload-text">
          <p class="upload-title">将文件拖到此处，或<em>点击上传</em></p>
          <p class="upload-hint">支持 PDF、DOCX、TXT、MD 格式</p>
        </div>
      </el-upload>

      <div v-if="fileList.length > 0" class="file-list">
        <div class="file-list-title">
          <el-icon><Document /></el-icon>
          <span>待上传文件 ({{ fileList.length }})</span>
        </div>
        <div class="file-list-items">
          <div v-for="(file, index) in fileList" :key="index" class="file-item">
            <div :class="['file-icon', getFileType(file.name)]">
              <el-icon :size="14"><Document /></el-icon>
            </div>
            <span class="file-item-name">{{ file.name }}</span>
            <span class="file-item-size">{{ formatFileSize(file.size) }}</span>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showUploadDialog = false">取消</el-button>
          <el-button type="primary" @click="uploadFiles">
            <el-icon><Upload /></el-icon>
            <span>开始上传</span>
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 预览对话框 -->
    <el-dialog v-model="showPreviewDialog" title="文档预览" width="800px" destroy-on-close>
      <div v-if="previewLoading" class="preview-loading">
        <el-icon class="is-loading" :size="32"><Loading /></el-icon>
        <p>加载预览内容...</p>
      </div>
      <div v-else-if="previewContent" class="preview-body">
        <div class="preview-meta">
          <span class="preview-filename">{{ previewFilename }}</span>
          <el-tag :type="previewStatus === 'completed' ? 'success' : 'warning'" size="small" round>
            {{ previewStatus }}
          </el-tag>
        </div>
        <div class="preview-text">{{ previewContent }}</div>
      </div>
      <div v-else class="preview-error">
        <p>无法加载预览内容</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Collection, FolderOpened, ArrowLeft, Edit, InfoFilled, Document,
  OfficeBuilding, Calendar, CircleCheck, Upload, Refresh, View, Delete,
  RefreshRight, Loading
} from '@element-plus/icons-vue'
import request from '@/utils/request'

const route = useRoute()
const knowledgeId = route.params.id

const formatFileSize = (bytes) => {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const getStatusType = (status) => {
  const types = { pending: 'info', processing: 'warning', completed: 'success', failed: 'danger' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { pending: '待处理', processing: '处理中', completed: '已完成', failed: '失败' }
  return texts[status] || status
}

const getFileType = (filename) => {
  if (!filename) return 'default'
  const ext = filename.split('.').pop().toLowerCase()
  const types = { pdf: 'pdf', docx: 'word', doc: 'word', txt: 'text', md: 'markdown' }
  return types[ext] || 'default'
}

const getFileIcon = (filename) => {
  if (!filename) return 'Document'
  const ext = filename.split('.').pop().toLowerCase()
  const icons = { pdf: 'Document', docx: 'Document', doc: 'Document', txt: 'Document', md: 'Document' }
  return icons[ext] || 'Document'
}

const knowledge = reactive({
  name: '',
  description: '',
  department: '',
  created_at: '',
  status: true,
})

const showEditDialog = ref(false)
const showUploadDialog = ref(false)
const documents = ref([])
const fileList = ref([])

const loadKnowledgeBase = async () => {
  try {
    const data = await request.get(`/knowledge-bases/${knowledgeId}`)
    Object.assign(knowledge, data)
  } catch (error) {
    ElMessage.error('加载知识库信息失败')
  }
}

const loadDocuments = async () => {
  try {
    const data = await request.get('/documents/', {
      params: { knowledge_base_id: knowledgeId }
    })
    documents.value = data
  } catch (error) {
    ElMessage.error('加载文档列表失败')
  }
}

const showPreviewDialog = ref(false)
const previewLoading = ref(false)
const previewContent = ref('')
const previewFilename = ref('')
const previewStatus = ref('')

const previewDocument = async (row) => {
  showPreviewDialog.value = true
  previewLoading.value = true
  previewContent.value = ''
  previewFilename.value = row.filename
  previewStatus.value = row.status

  try {
    const data = await request.get(`/documents/${row.id}/preview`)
    previewContent.value = data.content || '(空内容)'
  } catch (error) {
    previewContent.value = '预览加载失败: ' + (error?.detail || error?.message || '未知错误')
  } finally {
    previewLoading.value = false
  }
}

const regenerateDocument = async (row) => {
  row._regenerating = true
  try {
    const res = await request.post(`/documents/${row.id}/regenerate`)
    if (res.status === 'completed') {
      ElMessage.success(`向量重新生成完成！切片数: ${res.chunk_count}`)
    } else {
      ElMessage.error(res.message || '向量生成失败')
    }
    await loadDocuments()
  } catch (error) {
    ElMessage.error('重新生成失败: ' + (error?.detail || error?.message || ''))
  } finally {
    row._regenerating = false
  }
}

const deleteDocument = async (row) => {
  try {
    await ElMessageBox.confirm('确定删除该文档？', '提示', { type: 'warning' })
    await request.delete(`/documents/${row.id}`)
    ElMessage.success('删除成功')
    await loadDocuments()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleFileChange = (file) => {
  fileList.value.push(file)
}

const uploadFiles = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请选择文件')
    return
  }

  try {
    for (const file of fileList.value) {
      const formData = new FormData()
      formData.append('file', file.raw)
      await request.post(`/documents/upload?knowledge_base_id=${knowledgeId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
    }
    showUploadDialog.value = false
    fileList.value = []
    ElMessage.success('上传成功')
    await loadDocuments()
  } catch (error) {
    ElMessage.error('上传失败')
  }
}

onMounted(() => {
  loadKnowledgeBase()
  loadDocuments()
})
</script>

<style scoped>
.knowledge-detail {
  padding: 24px;
  min-height: 100%;
  background: var(--gray-50, #f9fafb);
}

/* 动画 */
.fade-in {
  animation: fadeInUp 0.5s ease-out;
}
.fade-in-delay {
  animation: fadeInUp 0.5s ease-out 0.1s both;
}
.fade-in-delay-2 {
  animation: fadeInUp 0.5s ease-out 0.2s both;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 面包屑 */
.breadcrumb-section {
  margin-bottom: 20px;
}
.breadcrumb-section :deep(.el-breadcrumb__inner) {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
}
.breadcrumb-section :deep(.el-breadcrumb__item) {
  color: var(--gray-500, #6b7280);
}
.breadcrumb-section :deep(.el-breadcrumb__item:last-child) {
  color: var(--gray-800, #1f2937);
}

/* 页面头部 */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  padding: 24px 28px;
  background: #fff;
  border-radius: var(--radius-lg, 16px);
  box-shadow: var(--shadow-sm, 0 1px 2px rgba(0,0,0,0.04));
  border: 1px solid var(--gray-100, #f3f4f6);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  border-radius: var(--radius-sm, 6px);
  font-weight: 500;
  color: var(--gray-600, #4b5563);
  border: 1px solid var(--gray-200, #e5e7eb);
  background: #fff;
  transition: var(--transition, all 0.25s cubic-bezier(0.4,0,0.2,1));
}
.back-btn:hover {
  border-color: var(--primary, #4f6ef7);
  color: var(--primary, #4f6ef7);
  background: var(--primary-bg, #f0f3ff);
}

.header-icon {
  width: 52px;
  height: 52px;
  border-radius: var(--radius-md, 10px);
  background: linear-gradient(135deg, var(--primary, #4f6ef7), var(--primary-light, #6b8cff));
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.header-text h2 {
  margin: 0 0 4px 0;
  font-size: 22px;
  font-weight: 700;
  color: var(--gray-800, #1f2937);
  letter-spacing: -0.02em;
}

.subtitle {
  margin: 0;
  font-size: 14px;
  color: var(--gray-500, #6b7280);
}

.edit-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 22px;
  border-radius: var(--radius-sm, 6px);
  font-weight: 600;
  font-size: 14px;
  transition: var(--transition, all 0.25s cubic-bezier(0.4,0,0.2,1));
  box-shadow: 0 2px 8px rgba(79, 110, 247, 0.3);
}
.edit-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(79, 110, 247, 0.4);
}

/* 内容区域 */
.content-section {
  margin-top: 0;
}

/* 信息卡片 */
.info-card {
  border-radius: var(--radius-lg, 16px);
  border: 1px solid var(--gray-100, #f3f4f6);
  overflow: hidden;
  height: 100%;
}
.info-card :deep(.el-card__header) {
  padding: 18px 24px;
  border-bottom: 1px solid var(--gray-100, #f3f4f6);
  background: var(--gray-50, #f9fafb);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 700;
  color: var(--gray-800, #1f2937);
}

.info-content {
  padding: 8px 0;
}

.info-item {
  padding: 16px 0;
  border-bottom: 1px solid var(--gray-100, #f3f4f6);
}
.info-item:last-child {
  border-bottom: none;
}

.info-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--gray-500, #6b7280);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.info-value {
  font-size: 14px;
  color: var(--gray-800, #1f2937);
  line-height: 1.6;
}

.dept-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  background: var(--primary-bg, #f0f3ff);
  color: var(--primary, #4f6ef7);
  font-size: 13px;
  font-weight: 600;
}

.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.status-indicator.active .status-dot {
  background: var(--success, #22c55e);
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.4);
}
.status-indicator.inactive .status-dot {
  background: var(--danger, #ef4444);
  box-shadow: 0 0 8px rgba(239, 68, 68, 0.4);
}

/* 文档卡片 */
.docs-card {
  border-radius: var(--radius-lg, 16px);
  border: 1px solid var(--gray-100, #f3f4f6);
  overflow: hidden;
}
.docs-card :deep(.el-card__header) {
  padding: 18px 24px;
  border-bottom: 1px solid var(--gray-100, #f3f4f6);
  background: var(--gray-50, #f9fafb);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 700;
  color: var(--gray-800, #1f2937);
}

.doc-count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  padding: 0 8px;
  border-radius: 12px;
  background: var(--primary, #4f6ef7);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
}

.doc-actions {
  display: flex;
  gap: 10px;
}

.upload-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border-radius: var(--radius-sm, 6px);
  font-weight: 600;
}

/* 文档表格 */
.docs-table {
  --el-table-border-color: var(--gray-100, #f3f4f6);
}

.docs-table :deep(.el-table__header th) {
  background: var(--gray-50, #f9fafb);
  color: var(--gray-600, #4b5563);
  font-weight: 600;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  padding: 14px 0;
  border-bottom: 2px solid var(--gray-100, #f3f4f6);
}

.docs-table :deep(.el-table__row) {
  transition: var(--transition, all 0.25s cubic-bezier(0.4,0,0.2,1));
}
.docs-table :deep(.el-table__row:hover > td) {
  background: var(--primary-bg, #f0f3ff) !important;
}
.docs-table :deep(td) {
  padding: 14px 0;
  font-size: 14px;
  color: var(--gray-700, #374151);
}

.file-name-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.file-icon {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-sm, 6px);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.file-icon.pdf {
  background: #fef2f2;
  color: #dc2626;
}
.file-icon.word {
  background: #eff6ff;
  color: #2563eb;
}
.file-icon.text {
  background: var(--gray-100, #f3f4f6);
  color: var(--gray-600, #4b5563);
}
.file-icon.markdown {
  background: #f0f9ff;
  color: #0891b2;
}
.file-icon.default {
  background: var(--gray-100, #f3f4f6);
  color: var(--gray-500, #6b7280);
}

.file-name {
  font-weight: 600;
  color: var(--gray-800, #1f2937);
}

.file-size {
  font-size: 13px;
  color: var(--gray-600, #4b5563);
  font-weight: 500;
}

.chunk-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 28px;
  border-radius: 14px;
  background: var(--gray-100, #f3f4f6);
  font-weight: 600;
  font-size: 13px;
  color: var(--gray-700, #374151);
}

.action-btns {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}
.action-btns .el-button {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 13px;
  padding: 4px 8px;
  border-radius: var(--radius-sm, 6px);
  transition: var(--transition, all 0.25s cubic-bezier(0.4,0,0.2,1));
}
.action-btns .el-button:hover {
  background: var(--gray-50, #f9fafb);
}

/* 空状态 */
.empty-docs {
  text-align: center;
  padding: 60px 20px;
  color: var(--gray-400, #9ca3af);
}
.empty-docs p {
  margin: 16px 0 24px;
  font-size: 15px;
  color: var(--gray-500, #6b7280);
}

/* 上传对话框 */
.upload-dialog :deep(.el-dialog) {
  border-radius: var(--radius-lg, 16px);
  overflow: hidden;
}

.dialog-header {
  display: flex;
  align-items: center;
  gap: 14px;
}
.dialog-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md, 10px);
  background: linear-gradient(135deg, var(--primary, #4f6ef7), var(--primary-light, #6b8cff));
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.dialog-header h3 {
  margin: 0 0 2px 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--gray-800, #1f2937);
}
.dialog-header p {
  margin: 0;
  font-size: 13px;
  color: var(--gray-500, #6b7280);
}

.upload-area {
  margin: 8px 0 20px;
}

.upload-area :deep(.el-upload-dragger) {
  padding: 40px 20px;
  border-radius: var(--radius-md, 10px);
  border: 2px dashed var(--gray-300, #d1d5db);
  background: var(--gray-50, #f9fafb);
  transition: var(--transition, all 0.25s cubic-bezier(0.4,0,0.2,1));
}
.upload-area :deep(.el-upload-dragger:hover) {
  border-color: var(--primary, #4f6ef7);
  background: var(--primary-bg, #f0f3ff);
}

.upload-icon {
  font-size: 48px;
  color: var(--primary, #4f6ef7);
  margin-bottom: 16px;
}

.upload-text {
  margin-top: 12px;
}
.upload-title {
  margin: 0;
  font-size: 15px;
  color: var(--gray-700, #374151);
  font-weight: 500;
}
.upload-title em {
  color: var(--primary, #4f6ef7);
  font-style: normal;
  font-weight: 600;
}
.upload-hint {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--gray-500, #6b7280);
}

.file-list {
  margin-top: 20px;
  padding: 16px;
  background: var(--gray-50, #f9fafb);
  border-radius: var(--radius-md, 10px);
  border: 1px solid var(--gray-200, #e5e7eb);
}

.file-list-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-700, #374151);
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--gray-200, #e5e7eb);
}

.file-list-items {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #fff;
  border-radius: var(--radius-sm, 6px);
  border: 1px solid var(--gray-200, #e5e7eb);
}

.file-item-name {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: var(--gray-800, #1f2937);
}

.file-item-size {
  font-size: 13px;
  color: var(--gray-500, #6b7280);
  font-weight: 500;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
.dialog-footer .el-button {
  padding: 8px 20px;
  border-radius: var(--radius-sm, 6px);
  font-weight: 600;
}

/* 预览对话框 */
.preview-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  color: var(--gray-500);
  gap: 16px;
}

.preview-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--gray-200);
}

.preview-filename {
  font-weight: 600;
  font-size: 15px;
  color: var(--gray-800);
}

.preview-text {
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 14px;
  line-height: 1.8;
  color: var(--gray-700);
  max-height: 60vh;
  overflow-y: auto;
  background: var(--gray-50);
  padding: 20px;
  border-radius: var(--radius-md, 10px);
  border: 1px solid var(--gray-200);
}

.preview-error {
  text-align: center;
  padding: 60px 0;
  color: var(--gray-500);
}
</style>
