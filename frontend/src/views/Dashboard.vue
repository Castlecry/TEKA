<template>
  <div class="dashboard">
    <!-- 页面头部 -->
    <div class="page-header fade-in-up" style="--delay: 0">
      <div class="header-content">
        <div class="header-text">
          <h2>欢迎回来，{{ userName }}</h2>
          <p>智汇办公 AI 智能平台 · 让知识触手可及</p>
        </div>
        <div class="header-decoration">
          <div class="decoration-circle c1"></div>
          <div class="decoration-circle c2"></div>
          <div class="decoration-circle c3"></div>
        </div>
      </div>
    </div>

    <!-- 模块卡片 -->
    <div class="module-grid">
      <div
        v-for="(mod, idx) in modules"
        :key="mod.id"
        class="module-card fade-in-up"
        :style="{ '--delay': idx * 0.1 + 0.1 }"
        @click="enterModule(mod.id)"
      >
        <div class="module-card-inner">
          <div class="module-icon" :style="{ background: mod.color }">
            <el-icon :size="24"><Component :is="getModuleIcon(mod.icon)" /></el-icon>
          </div>
          <div class="module-info">
            <div class="module-name">{{ mod.name }}</div>
            <div class="module-desc">{{ mod.description }}</div>
          </div>
        </div>
        <!-- 示例问题 -->
        <div class="module-questions">
          <div class="questions-label">试试这样问：</div>
          <div class="questions-list">
            <span
              v-for="(q, qi) in mod.example_questions"
              :key="qi"
              class="question-tag"
              @click.stop="askQuestion(mod.id, q)"
            >
              {{ q }}
            </span>
          </div>
        </div>
        <div class="module-card-bg" :style="{ background: mod.color }"></div>
      </div>
    </div>

    <!-- 统计信息 -->
    <div class="stats-row fade-in-up" style="--delay: 0.5">
      <div class="stat-item">
        <span class="stat-number">{{ stats.knowledgeBases }}</span>
        <span class="stat-label">知识库</span>
      </div>
      <div class="stat-item">
        <span class="stat-number">{{ stats.documents }}</span>
        <span class="stat-label">文档</span>
      </div>
      <div class="stat-item">
        <span class="stat-number">{{ stats.todayConversations }}</span>
        <span class="stat-label">今日对话</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Document, Monitor, OfficeBuilding, ChatLineRound
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const modules = ref([])

const iconMap = { Document, Monitor, OfficeBuilding, ChatLineRound }

const getModuleIcon = (iconName) => iconMap[iconName] || ChatLineRound

const userName = computed(() => {
  return userStore.user?.username || userStore.user?.name || '用户'
})

const stats = ref({
  knowledgeBases: 0,
  documents: 0,
  todayConversations: 0,
})

const enterModule = (moduleId) => {
  router.push({ path: '/chat', query: { module: moduleId } })
}

const askQuestion = (moduleId, question) => {
  router.push({ path: '/chat', query: { module: moduleId, question } })
}

const loadModules = async () => {
  try {
    const data = await request.get('/knowledge-bases/modules')
    modules.value = data
  } catch (error) {
    ElMessage.error('加载模块列表失败')
  }
}

const loadStats = async () => {
  try {
    const [knowledgeBases, documents, sessions] = await Promise.all([
      request.get('/knowledge-bases/'),
      request.get('/documents/'),
      request.get('/chat/sessions'),
    ])

    stats.value.knowledgeBases = knowledgeBases.length || 0
    stats.value.documents = documents.length || 0

    const today = new Date().toISOString().split('T')[0]
    stats.value.todayConversations = sessions.filter(s =>
      s.created_at && s.created_at.startsWith(today)
    ).length || 0
  } catch (error) {
    // 静默失败
  }
}

onMounted(() => {
  loadModules()
  loadStats()
})
</script>

<style scoped>
.dashboard {
  padding: 28px 32px;
  min-height: 100%;
}

.fade-in-up {
  opacity: 0;
  transform: translateY(24px);
  animation: fadeInUp 0.6s cubic-bezier(0.22, 1, 0.36, 1) forwards;
  animation-delay: calc(var(--delay) * 1s);
}

@keyframes fadeInUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 页面头部 */
.page-header {
  margin-bottom: 28px;
}

.header-content {
  position: relative;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
  border-radius: var(--radius-lg);
  padding: 32px 36px;
  color: #fff;
  overflow: hidden;
}

.header-text h2 {
  font-size: 26px;
  font-weight: 700;
  margin: 0 0 8px 0;
  color: #fff;
}

.header-text p {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.85);
  margin: 0;
}

.header-decoration {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 300px;
  pointer-events: none;
}

.decoration-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
}

.decoration-circle.c1 {
  width: 200px;
  height: 200px;
  right: -40px;
  top: -60px;
}

.decoration-circle.c2 {
  width: 120px;
  height: 120px;
  right: 60px;
  bottom: -40px;
}

.decoration-circle.c3 {
  width: 80px;
  height: 80px;
  right: 160px;
  top: -10px;
  background: rgba(255, 255, 255, 0.05);
}

/* 模块卡片 */
.module-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 28px;
}

.module-card {
  position: relative;
  border-radius: var(--radius-md);
  background: #fff;
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  transition: var(--transition);
  cursor: pointer;
  border: 1px solid var(--gray-200);
}

.module-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-lg);
  border-color: var(--primary-light);
}

.module-card-inner {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 22px 20px 16px;
  position: relative;
  z-index: 1;
}

.module-icon {
  width: 52px;
  height: 52px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
  font-size: 22px;
}

.module-info {
  flex: 1;
}

.module-name {
  font-size: 17px;
  font-weight: 700;
  color: var(--gray-800);
}

.module-desc {
  font-size: 12px;
  color: var(--gray-500);
  margin-top: 4px;
  line-height: 1.4;
}

.module-questions {
  padding: 0 20px 18px;
  position: relative;
  z-index: 1;
}

.questions-label {
  font-size: 11px;
  color: var(--gray-400);
  margin-bottom: 8px;
}

.questions-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.question-tag {
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 12px;
  background: var(--gray-100);
  color: var(--gray-600);
  cursor: pointer;
  transition: var(--transition);
  white-space: nowrap;
}

.question-tag:hover {
  background: var(--primary-bg);
  color: var(--primary);
}

.module-card-bg {
  position: absolute;
  right: -20px;
  bottom: -20px;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  opacity: 0.05;
  transition: var(--transition);
}

.module-card:hover .module-card-bg {
  transform: scale(1.5);
  opacity: 0.08;
}

/* 统计行 */
.stats-row {
  display: flex;
  gap: 32px;
  padding: 20px 28px;
  background: #fff;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
}

.stat-item {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.stat-number {
  font-size: 28px;
  font-weight: 800;
  color: var(--gray-800);
}

.stat-label {
  font-size: 13px;
  color: var(--gray-500);
}

/* 响应式 */
@media (max-width: 1200px) {
  .module-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .dashboard {
    padding: 16px;
  }
  .module-grid {
    grid-template-columns: 1fr;
  }
  .stats-row {
    flex-wrap: wrap;
    gap: 20px;
  }
}
</style>
