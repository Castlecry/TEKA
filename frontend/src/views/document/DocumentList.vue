<template>
  <div class="document-list">
    <!-- 页面头部 -->
    <div class="page-header fade-in">
      <div class="header-left">
        <div class="header-icon">
          <el-icon :size="20"><Document /></el-icon>
        </div>
        <div class="header-text">
          <h2>文档管理</h2>
          <p class="subtitle">集中管理所有知识库文档，支持批量上传和向量生成</p>
        </div>
      </div>
      <el-button type="primary" class="upload-btn" @click="showUploadDialog = true">
        <el-icon><Upload /></el-icon>
        <span>上传文档</span>
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
              placeholder="搜索文件名..."
              class="search-input"
              @keyup.enter="loadDocuments"
            />
          </div>
          <el-select v-model="selectedKB" placeholder="选择知识库" class="kb-select" clearable>
            <el-option label="全部知识库" value="" />
            <el-option v-for="kb in knowledgeBases" :key="kb.id" :label="kb.name" :value="kb.id" />
          </el-select>
          <el-button type="primary" @click="loadDocuments" class="search-btn">
            <el-icon><Search /></el-icon>
            <span>搜索</span>
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 表格区域 -->
    <div class="table-section fade-in-delay-2">
      <el-card shadow="never" class="table-card" v-if="documents.length > 0">
        <el-table :data="documents" class="custom-table">
          <el-table-column prop="filename" label="文件名" min-width="220">
            <template #default="scope">
              <div class="file-name-cell">
                <div :class="['file-icon', getFileType(scope.row.filename)]">
                  <el-icon :size="16"><Document /></el-icon>
                </div>
                <span class="file-name">{{ scope.row.filename }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="knowledge_base_id" label="知识库ID" width="130" align="center">
            <template #default="scope">
              <span class="kb-id-badge">{{ scope.row.knowledge_base_id }}</span>
            </template>
          </el-table-column>
          <el-table-column label="大小" width="110" align="center">
            <template #default="scope">
              <span class="file-size">{{ formatFileSize(scope.row.size) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="上传时间" width="180">
            <template #default="scope">
              <span class="upload-time">{{ formatDate(scope.row.uploaded_at) }}</span>
            </template>
          </el-table-column>
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
          <el-table-column label="操作" width="260" align="center" fixed="right">
            <template #default="scope">
              <div class="action-btns">
                <el-button type="primary" link size="small" @click="previewDocument(scope.row)">
                  <el-icon><View /></el-icon>
                  <span>预览</span>
                </el-button>
                <el-button type="warning" link size="small" @click="regenerateVector(scope.row)">
                  <el-icon><RefreshRight /></el-icon>
                  <span>重新生成向量</span>
                </el-button>
                <el-button type="danger" link size="small" @click="deleteDocument(scope.row)">
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
          <el-icon :size="48"><Document /></el-icon>
        </div>
        <h3>暂无文档</h3>
        <p>您还没有上传任何文档，点击下方按钮开始上传</p>
        <el-button type="primary" @click="showUploadDialog = true">
          <el-icon><Upload /></el-icon>
          <span>上传第一个文档</span>
        </el-button>
      </div>
    </div>

    <!-- 上传对话框 -->
    <el-dialog v-model="showUploadDialog" title="" width="560px" class="upload-dialog">
      <template #header>
        <div class="dialog-header">
          <div class="dialog-icon">
            <el-icon :size="18"><Upload /></el-icon>
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
          <p class="upload-hint">支持 PDF、DOCX、TXT、MD 格式，可批量上传</p>
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
    <el-dialog v-model="showPreviewDialog" width="720px" class="preview-dialog" destroy-on-close>
      <template #header>
        <div class="dialog-header">
          <div class="dialog-icon" style="background: linear-gradient(135deg, #0891b2, #06b6d4);">
            <el-icon :size="18"><View /></el-icon>
          </div>
          <div>
            <h3>{{ previewFilename }}</h3>
            <p>
              <el-tag :type="getStatusType(previewStatus)" size="small" effect="light" round>
                {{ getStatusText(previewStatus) }}
              </el-tag>
            </p>
          </div>
        </div>
      </template>

      <div v-loading="previewLoading" class="preview-body">
        <pre v-if="previewContent" class="preview-content">{{ previewContent }}</pre>
        <div v-else-if="!previewLoading" class="preview-empty">
          <el-icon :size="48" color="var(--gray-300)"><Document /></el-icon>
          <p>暂无可预览的内容</p>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="showPreviewDialog = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Document, Upload, View, Delete, RefreshRight, Search
} from '@element-plus/icons-vue'
import request from '@/utils/request'

const formatFileSize = (bytes) => {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
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

const searchText = ref('')
const selectedKB = ref('')
const showUploadDialog = ref(false)
const fileList = ref([])

const documents = ref([])
const knowledgeBases = ref([])

const loadKnowledgeBases = async () => {
  try {
    knowledgeBases.value = await request.get('/knowledge-bases/')
  } catch (error) {
    console.error('加载知识库列表失败', error)
  }
}

const loadDocuments = async () => {
  try {
    const params = {}
    if (searchText.value) params.filename = searchText.value
    if (selectedKB.value) params.knowledge_base_id = selectedKB.value
    const data = await request.get('/documents/', { params })
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

const regenerateVector = async (row) => {
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
    ElMessage.error('重新生成失败')
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
      const url = selectedKB.value
        ? `/documents/upload?knowledge_base_id=${selectedKB.value}`
        : '/documents/upload'
      await request.post(url, formData, {
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
  loadDocuments()
})
</script>

<style scoped>
.document-list {
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

.header-icon {
  width: 48px;
  height: 48px;
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

.upload-btn {
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
.upload-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(79, 110, 247, 0.4);
}

/* 搜索区域 */
.search-card {
  border-radius: var(--radius-lg, 16px);
  border: 1px solid var(--gray-100, #f3f4f6);
  overflow: hidden;
}
.search-card :deep(.el-card__body) {
  padding: 16px 20px;
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-input-wrapper {
  position: relative;
  flex: 1;
  max-width: 320px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--gray-400, #9ca3af);
  z-index: 1;
  font-size: 16px;
}

.search-input :deep(.el-input__wrapper) {
  padding-left: 38px;
  border-radius: var(--radius-sm, 6px);
  box-shadow: none;
  border: 1px solid var(--gray-200, #e5e7eb);
  transition: var(--transition, all 0.25s cubic-bezier(0.4,0,0.2,1));
}
.search-input :deep(.el-input__wrapper):hover,
.search-input :deep(.el-input__wrapper.is-focus) {
  border-color: var(--primary, #4f6ef7);
  box-shadow: 0 0 0 3px rgba(79, 110, 247, 0.1);
}

.kb-select {
  width: 180px;
}
.kb-select :deep(.el-input__wrapper) {
  border-radius: var(--radius-sm, 6px);
  box-shadow: none;
  border: 1px solid var(--gray-200, #e5e7eb);
}

.search-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  border-radius: var(--radius-sm, 6px);
  padding: 8px 18px;
}

/* 表格区域 */
.table-card {
  border-radius: var(--radius-lg, 16px);
  border: 1px solid var(--gray-100, #f3f4f6);
  overflow: hidden;
}
.table-card :deep(.el-card__body) {
  padding: 0;
}

.custom-table {
  --el-table-border-color: var(--gray-100, #f3f4f6);
}

.custom-table :deep(.el-table__header th) {
  background: var(--gray-50, #f9fafb);
  color: var(--gray-600, #4b5563);
  font-weight: 600;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  padding: 14px 0;
  border-bottom: 2px solid var(--gray-100, #f3f4f6);
}

.custom-table :deep(.el-table__row) {
  transition: var(--transition, all 0.25s cubic-bezier(0.4,0,0.2,1));
}
.custom-table :deep(.el-table__row:hover > td) {
  background: var(--primary-bg, #f0f3ff) !important;
}
.custom-table :deep(.el-table__row:hover) {
  box-shadow: inset 0 0 0 1px var(--primary-bg, #f0f3ff);
}
.custom-table :deep(td) {
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

.kb-id-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  height: 28px;
  padding: 0 10px;
  border-radius: 14px;
  background: var(--primary-bg, #f0f3ff);
  color: var(--primary, #4f6ef7);
  font-weight: 600;
  font-size: 13px;
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
.empty-state {
  text-align: center;
  padding: 80px 20px;
  background: #fff;
  border-radius: var(--radius-lg, 16px);
  border: 1px solid var(--gray-100, #f3f4f6);
}
.empty-icon {
  color: var(--gray-300, #d1d5db);
  margin-bottom: 20px;
}
.empty-state h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: var(--gray-700, #374151);
  font-weight: 600;
}
.empty-state p {
  margin: 0 0 24px 0;
  font-size: 14px;
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
.preview-dialog :deep(.el-dialog) {
  border-radius: var(--radius-lg, 16px);
  overflow: hidden;
}

.preview-body {
  min-height: 400px;
  max-height: 600px;
  overflow: auto;
  background: var(--gray-50, #f9fafb);
  border-radius: var(--radius-md, 10px);
  border: 1px solid var(--gray-200, #e5e7eb);
  padding: 20px;
}

.preview-content {
  margin: 0;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: var(--gray-700, #374151);
  white-space: pre-wrap;
  word-break: break-word;
}

.preview-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: var(--gray-400, #9ca3af);
}

.preview-empty p {
  margin-top: 12px;
  font-size: 14px;
}
</style>
