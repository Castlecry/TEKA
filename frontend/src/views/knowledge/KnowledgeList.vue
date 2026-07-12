<template>
  <div class="knowledge-list">
    <div class="page-header">
      <h2>知识库管理</h2>
      <el-button type="primary" icon="Plus" @click="showCreateDialog = true">创建知识库</el-button>
    </div>

    <el-card>
      <div class="search-bar">
        <el-input placeholder="搜索知识库名称" v-model="searchText" style="width: 200px" />
        <el-select placeholder="选择部门" v-model="selectedDept" style="width: 150px">
          <el-option label="全部" value="" />
          <el-option label="技术部" value="技术部" />
          <el-option label="产品部" value="产品部" />
          <el-option label="市场部" value="市场部" />
        </el-select>
        <el-button icon="Search" @click="loadKnowledgeBases">搜索</el-button>
      </div>

      <el-table :data="knowledgeBases" border>
        <el-table-column prop="name" label="知识库名称" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="department" label="所属部门" />
        <el-table-column prop="owner" label="负责人" />
        <el-table-column prop="document_count" label="文档数量" />
        <el-table-column prop="created_at" label="创建时间" />
        <el-table-column prop="status" label="状态">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'active' ? 'success' : 'danger'">
              {{ scope.row.status === 'active' ? '活跃' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作">
          <template #default="scope">
            <el-button size="small" @click="viewDetail(scope.row)">详情</el-button>
            <el-button size="small" @click="editKnowledge(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteKnowledge(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showCreateDialog" title="创建知识库" width="500px">
      <el-form :model="form" :rules="rules" ref="formRef">
        <el-form-item label="知识库名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
        <el-form-item label="所属部门" prop="department">
          <el-select v-model="form.department">
            <el-option label="技术部" value="技术部" />
            <el-option label="产品部" value="产品部" />
            <el-option label="市场部" value="市场部" />
            <el-option label="人事部" value="人事部" />
          </el-select>
        </el-form-item>
        <el-form-item label="负责人" prop="owner">
          <el-input v-model="form.owner" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createKnowledge">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/utils/request'

const router = useRouter()

const searchText = ref('')
const selectedDept = ref('')
const showCreateDialog = ref(false)
const formRef = ref(null)

const form = reactive({
  name: '',
  description: '',
  department: '',
  owner: '',
})

const rules = {
  name: [{ required: true, message: '请输入知识库名称', trigger: 'blur' }],
  department: [{ required: true, message: '请选择所属部门', trigger: 'change' }],
}

const knowledgeBases = ref([
  {
    id: 1,
    name: '公司规章制度',
    description: '包含员工手册、考勤制度、报销制度等',
    department: '人事部',
    owner: '张三',
    document_count: 5,
    created_at: '2024-01-15',
    status: 'active',
  },
  {
    id: 2,
    name: '产品技术文档',
    description: '产品API文档、技术架构文档',
    department: '技术部',
    owner: '李四',
    document_count: 8,
    created_at: '2024-01-20',
    status: 'active',
  },
])

const loadKnowledgeBases = () => {}

const viewDetail = (row) => {
  router.push(`/knowledge/${row.id}`)
}

const editKnowledge = (row) => {}

const deleteKnowledge = (row) => {
  ElMessageBox.confirm('确定删除该知识库？', '提示', { type: 'warning' }).then(() => {
    ElMessage.success('删除成功')
  })
}

const createKnowledge = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate()
  if (!valid) return

  showCreateDialog.value = false
  ElMessage.success('创建成功')
  form.name = ''
  form.description = ''
  form.department = ''
  form.owner = ''
}
</script>

<style scoped>
.knowledge-list {
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
