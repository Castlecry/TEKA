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
            <el-descriptions-item label="负责人">{{ knowledge.owner }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ knowledge.created_at }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="knowledge.status === 'active' ? 'success' : 'danger'">
                {{ knowledge.status === 'active' ? '活跃' : '停用' }}
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
            <el-table-column prop="size" label="大小" />
            <el-table-column prop="upload_time" label="上传时间" />
            <el-table-column prop="chunk_count" label="切片数量" />
            <el-table-column prop="status" label="状态">
              <template #default="scope">
                <el-tag :type="scope.row.status === 'indexed' ? 'success' : 'warning'">
                  {{ scope.row.status === 'indexed' ? '已索引' : '处理中' }}
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

const route = useRoute()

const knowledge = reactive({
  name: '公司规章制度',
  description: '包含员工手册、考勤制度、报销制度等',
  department: '人事部',
  owner: '张三',
  created_at: '2024-01-15',
  status: 'active',
})

const showEditDialog = ref(false)
const showUploadDialog = ref(false)
const documents = ref([])

onMounted(() => {
  documents.value = [
    { id: 1, filename: '员工手册.pdf', size: '2.3MB', upload_time: '2024-01-15', chunk_count: 45, status: 'indexed' },
    { id: 2, filename: '考勤制度.md', size: '15KB', upload_time: '2024-01-16', chunk_count: 3, status: 'indexed' },
    { id: 3, filename: '报销流程.docx', size: '56KB', upload_time: '2024-01-17', chunk_count: 8, status: 'indexed' },
  ]
})

const loadDocuments = () => {}

const previewDocument = (row) => {}

const deleteDocument = (row) => {
  ElMessageBox.confirm('确定删除该文档？', '提示', { type: 'warning' }).then(() => {
    ElMessage.success('删除成功')
  })
}

const handleFileChange = () => {}

const uploadFiles = () => {
  showUploadDialog.value = false
  ElMessage.success('上传成功')
}
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
