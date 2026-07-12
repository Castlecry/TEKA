<template>
  <div class="conversation-log">
    <div class="page-header">
      <h2>对话日志</h2>
    </div>

    <el-card>
      <div class="search-bar">
        <el-input placeholder="搜索关键词" v-model="searchText" style="width: 200px" />
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 300px"
        />
        <el-select placeholder="选择用户" v-model="selectedUser" style="width: 150px">
          <el-option label="全部" value="" />
          <el-option label="admin" value="admin" />
          <el-option label="zhangsan" value="zhangsan" />
        </el-select>
        <el-button icon="Search" @click="loadLogs">搜索</el-button>
      </div>

      <el-table :data="logs" border>
        <el-table-column prop="conversation_id" label="会话ID" />
        <el-table-column prop="user_id" label="用户" />
        <el-table-column prop="query" label="问题" show-overflow-tooltip />
        <el-table-column prop="answer" label="回答" show-overflow-tooltip />
        <el-table-column prop="source" label="来源知识库" />
        <el-table-column prop="created_at" label="时间" />
        <el-table-column label="操作">
          <template #default="scope">
            <el-button size="small" @click="viewDetail(scope.row)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showDetailDialog" title="对话详情" width="700px">
      <div v-if="selectedLog" class="log-detail">
        <div class="detail-item">
          <span class="detail-label">会话ID：</span>
          <span>{{ selectedLog.conversation_id }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">用户：</span>
          <span>{{ selectedLog.user_id }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">时间：</span>
          <span>{{ selectedLog.created_at }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">来源：</span>
          <span>{{ selectedLog.source }}</span>
        </div>
        <div class="detail-section">
          <h4>问题</h4>
          <p>{{ selectedLog.query }}</p>
        </div>
        <div class="detail-section">
          <h4>回答</h4>
          <MarkdownRenderer :content="selectedLog.answer" />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import request from '@/utils/request'

const searchText = ref('')
const dateRange = ref([])
const selectedUser = ref('')
const showDetailDialog = ref(false)
const selectedLog = ref(null)

const logs = ref([])

const loadLogs = async () => {
  try {
    const params = {}
    if (searchText.value) params.search = searchText.value
    if (selectedUser.value) params.user_id = selectedUser.value
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const data = await request.get('/chat/sessions', { params })
    logs.value = data
  } catch (error) {
    ElMessage.error('加载对话日志失败')
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

onMounted(() => {
  loadLogs()
})
</script>

<style scoped>
.conversation-log {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  align-items: center;
}

.log-detail {
  padding: 16px;
}

.detail-item {
  margin-bottom: 12px;
}

.detail-label {
  font-weight: 600;
  color: #6b7280;
}

.detail-section {
  margin-top: 20px;
}

.detail-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #1f2937;
}

.detail-section p {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 8px;
  margin: 0;
}
</style>
