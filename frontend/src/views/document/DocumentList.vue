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
        <el-table-column prop="knowledge_base" label="所属知识库" />
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
import { ref } from 'vue'

const searchText = ref('')
const selectedKB = ref('')
const showUploadDialog = ref(false)

const documents = ref([
  { id: 1, filename: '员工手册.pdf', knowledge_base: '公司规章制度', size: '2.3MB', upload_time: '2024-01-15', chunk_count: 45, status: 'indexed' },
  { id: 2, filename: '考勤制度.md', knowledge_base: '公司规章制度', size: '15KB', upload_time: '2024-01-16', chunk_count: 3, status: 'indexed' },
  { id: 3, filename: '报销流程.docx', knowledge_base: '公司规章制度', size: '56KB', upload_time: '2024-01-17', chunk_count: 8, status: 'indexed' },
  { id: 4, filename: 'API文档.pdf', knowledge_base: '产品技术文档', size: '5.1MB', upload_time: '2024-01-20', chunk_count: 120, status: 'indexed' },
])

const loadDocuments = () => {}

const previewDocument = (row) => {}

const regenerateVector = (row) => {
  ElMessage.success('向量重新生成中')
}

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
