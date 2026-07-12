<template>
  <div class="dashboard">
    <div class="page-header">
      <h2>欢迎使用企业知识助手</h2>
      <p>智能检索企业知识，高效完成日常任务</p>
    </div>

    <div class="stats-grid">
      <el-card class="stat-card">
        <div class="stat-icon blue">
          <Component :is="icons.FolderOpen" />
        </div>
        <div class="stat-info">
          <div class="stat-value">0</div>
          <div class="stat-label">知识库数量</div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-icon green">
          <Component :is="icons.FileText" />
        </div>
        <div class="stat-info">
          <div class="stat-value">0</div>
          <div class="stat-label">文档数量</div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-icon purple">
          <Component :is="icons.MessageSquare" />
        </div>
        <div class="stat-info">
          <div class="stat-value">0</div>
          <div class="stat-label">今日对话</div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-icon orange">
          <Component :is="icons.Users" />
        </div>
        <div class="stat-info">
          <div class="stat-value">0</div>
          <div class="stat-label">活跃用户</div>
        </div>
      </el-card>
    </div>

    <div class="quick-actions">
      <el-card header="快捷操作">
        <div class="action-buttons">
          <el-button type="primary" icon="Plus" @click="$router.push('/knowledge')">
            创建知识库
          </el-button>
          <el-button icon="Upload" @click="$router.push('/documents')">
            上传文档
          </el-button>
          <el-button icon="MessageSquare" @click="$router.push('/chat')">
            开始对话
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { FolderOpen, FileText, MessageSquare, Users } from '@element-plus/icons-vue'

const icons = { FolderOpen, FileText, MessageSquare, Users }
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.page-header p {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: #fff;
}

.stat-icon.blue {
  background: #3b82f6;
}

.stat-icon.green {
  background: #10b981;
}

.stat-icon.purple {
  background: #8b5cf6;
}

.stat-icon.orange {
  background: #f59e0b;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
}

.action-buttons {
  display: flex;
  gap: 12px;
}
</style>
