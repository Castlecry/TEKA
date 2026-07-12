<template>
  <div class="knowledge-detail">
    <div class="page-header">
      <el-button icon="ArrowLeft" @click="$router.back()">返回</el-button>
      <h2>{{ knowledge.name }}</h2>
      <el-button type="primary" icon="Edit" @click="showEditDialog = true">编辑</el-button>
    </div>

    <el-row :gutter="20">
      <el-col :span="8">
        <el-card title="基本信息">
          <el-descriptions :column="1">
            <el-descriptions-item label="描述">{{ knowledge.description }}</el-descriptions-item>
            <el-descriptions-item label="所属部门">{{ knowledge.department }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ knowledge.created_at }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="knowledge.status ? 'success' : 'danger'">
                {{ knowledge.status ? '活跃' : '停用' }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card title="文档列表">
          <div class="doc-actions">
            <el-button type="primary" icon="Upload" @click="showUploadDialog = true">上传文档</el-button>
            <el-button icon="Refresh" @click="loadDocuments">刷新</el-button>
          </div>

          <el-table :data="documents" border>
            <el-table-column prop="filename" label="文件名" />
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
                <el-button size="small" type="danger" @click="deleteDocument(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="showUploadDialog" title="上传文档" width="500px">
      <el-upload
        class="upload-demo"
        action="/api/documents/upload"
        :auto-upload="false"
        :on-change="handleFileChange"
        accept=".pdf,.docx,.txt,.md"
      >
        <el-button type="primary" icon="Upload">点击上传</el-button>
        <template #tip>
          <div class="el-upload__tip">支持 PDF、DOCX、TXT、MD 格式</div>
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
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
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

const previewDocument = (row) => {
  ElMessage.info('预览功能开发中')
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
  padding: 20px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
}

.doc-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
</style>
