<template>
  <div class="document-list">
    <div class="page-header">
      <h2>文档管理</h2>
      <el-button type="primary" icon="Upload" @click="showUploadDialog = true">上传文档</el-button>
    </div>

    <el-card>
      <div class="search-bar">
        <el-input placeholder="搜索文件名" v-model="searchText" style="width: 200px" />
        <el-select placeholder="选择知识库" v-model="selectedKB" style="width: 150px">
          <el-option label="全部" value="" />
          <el-option label="公司规章制度" value="1" />
          <el-option label="产品技术文档" value="2" />
        </el-select>
        <el-button icon="Search" @click="loadDocuments">搜索</el-button>
      </div>

      <el-table :data="documents" border>
        <el-table-column prop="filename" label="文件名" />
        <el-table-column prop="knowledge_base_id" label="知识库ID" />
        <el-table-column label="大小">
          <template #default="scope">
            {{ formatFileSize(scope.row.size) }}
          </template>
        </el-table-column>
        <el-table-column prop="uploaded_at" label="上传时间" />
        <el-table-column prop="chunk_count" label="切片数量" />
        <el-table-column prop="status" label="状态">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作">
          <template #default="scope">
            <el-button size="small" @click="previewDocument(scope.row)">预览</el-button>
            <el-button size="small" @click="regenerateVector(scope.row)">重新生成向量</el-button>
            <el-button size="small" type="danger" @click="deleteDocument(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showUploadDialog" title="上传文档" width="500px">
      <el-upload
        class="upload-demo"
        action="/api/documents/upload"
        :auto-upload="false"
        :on-change="handleFileChange"
        accept=".pdf,.docx,.txt,.md"
        multiple
      >
        <el-button type="primary" icon="Upload">点击上传</el-button>
        <template #tip>
          <div class="el-upload__tip">支持 PDF、DOCX、TXT、MD 格式，可批量上传</div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="uploadFiles">开始上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

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

const searchText = ref('')
const selectedKB = ref('')
const showUploadDialog = ref(false)
const fileList = ref([])

const documents = ref([])

const loadDocuments = async () => {
  try {
    const params = {}
    if (selectedKB.value) params.knowledge_base_id = selectedKB.value
    const data = await request.get('/documents/', { params })
    documents.value = data
  } catch (error) {
    ElMessage.error('加载文档列表失败')
  }
}

const previewDocument = (row) => {
  ElMessage.info('预览功能开发中')
}

const regenerateVector = (row) => {
  ElMessage.success('向量重新生成中')
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
