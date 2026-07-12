<template>
  <div class="dashboard">
    <!-- 页面头部 -->
    <div class="page-header fade-in-up" style="--delay: 0">
      <div class="header-content">
        <div class="header-text">
          <h2>欢迎回来，{{ userName }} 👋</h2>
          <p>智能检索企业知识，高效完成日常任务</p>
        </div>
        <div class="header-decoration">
          <div class="decoration-circle c1"></div>
          <div class="decoration-circle c2"></div>
          <div class="decoration-circle c3"></div>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div
        v-for="(item, idx) in statCards"
        :key="idx"
        class="stat-card fade-in-up"
        :style="{ '--delay': idx * 0.1 + 0.1 }"
      >
        <div class="stat-card-inner">
          <div class="stat-icon" :class="item.color">
            <Component :is="item.icon" />
          </div>
          <div class="stat-info">
            <div class="stat-value">
              <span class="stat-number">{{ animatedStats[item.key] }}</span>
            </div>
            <div class="stat-label">{{ item.label }}</div>
          </div>
        </div>
        <div class="stat-card-bg" :class="item.color"></div>
      </div>
    </div>

    <!-- 快捷操作 + 快速开始 -->
    <div class="content-grid">
      <div class="section-card fade-in-up" style="--delay: 0.5">
        <div class="section-header">
          <h3>
            <Component :is="icons.Lightning" class="section-icon" />
            快捷操作
          </h3>
        </div>
        <div class="action-grid">
          <div
            v-for="(action, idx) in quickActions"
            :key="idx"
            class="action-card"
            @click="action.handler"
          >
            <div class="action-icon" :style="{ background: action.gradient }">
              <Component :is="action.icon" />
            </div>
            <div class="action-text">
              <div class="action-title">{{ action.title }}</div>
              <div class="action-desc">{{ action.desc }}</div>
            </div>
            <div class="action-arrow">
              <Component :is="icons.ArrowRight" />
            </div>
          </div>
        </div>
      </div>

      <div class="section-card fade-in-up" style="--delay: 0.6">
        <div class="section-header">
          <h3>
            <Component :is="icons.Promotion" class="section-icon" />
            快速开始
          </h3>
        </div>
        <div class="quick-start-list">
          <div
            v-for="(item, idx) in quickStartItems"
            :key="idx"
            class="quick-start-item"
            @click="item.handler"
          >
            <div class="qs-number">{{ String(idx + 1).padStart(2, '0') }}</div>
            <div class="qs-content">
              <div class="qs-title">{{ item.title }}</div>
              <div class="qs-desc">{{ item.desc }}</div>
            </div>
            <div class="qs-arrow">
              <Component :is="icons.Right" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  FolderOpened, Document, ChatLineRound, UserFilled,
  Plus, Upload, Lightning, Promotion, ArrowRight, Right
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const icons = { FolderOpened, Document, ChatLineRound, UserFilled, Plus, Upload, Lightning, Promotion, ArrowRight, Right }

const userName = computed(() => {
  return userStore.user?.username || userStore.user?.name || '用户'
})

const stats = ref({
  knowledgeBases: 0,
  documents: 0,
  todayConversations: 0,
  activeUsers: 0,
})

const animatedStats = reactive({
  knowledgeBases: 0,
  documents: 0,
  todayConversations: 0,
  activeUsers: 0,
})

const statCards = [
  { key: 'knowledgeBases', label: '知识库数量', icon: FolderOpened, color: 'blue' },
  { key: 'documents', label: '文档数量', icon: Document, color: 'green' },
  { key: 'todayConversations', label: '今日对话', icon: ChatLineRound, color: 'purple' },
  { key: 'activeUsers', label: '活跃用户', icon: UserFilled, color: 'orange' },
]

const quickActions = [
  {
    title: '创建知识库',
    desc: '新建企业知识库，组织知识内容',
    icon: FolderOpened,
    gradient: 'linear-gradient(135deg, #4f6ef7, #6b8cff)',
    handler: () => router.push('/knowledge'),
  },
  {
    title: '上传文档',
    desc: '导入文档到知识库中',
    icon: Upload,
    gradient: 'linear-gradient(135deg, #22c55e, #4ade80)',
    handler: () => router.push('/documents'),
  },
  {
    title: '开始对话',
    desc: '与 AI 助手智能对话',
    icon: ChatLineRound,
    gradient: 'linear-gradient(135deg, #8b5cf6, #a78bfa)',
    handler: () => router.push('/chat'),
  },
]

const quickStartItems = [
  {
    title: '配置知识库',
    desc: '创建并配置您的第一个知识库',
    handler: () => router.push('/knowledge'),
  },
  {
    title: '导入文档数据',
    desc: '批量上传文档，构建企业知识体系',
    handler: () => router.push('/documents'),
  },
  {
    title: '发起智能对话',
    desc: '基于知识库进行智能问答对话',
    handler: () => router.push('/chat'),
  },
]

// 数字动画
const animateNumber = (key, target) => {
  const duration = 1200
  const start = animatedStats[key]
  const diff = target - start
  if (diff === 0) return
  const startTime = performance.now()

  const step = (currentTime) => {
    const elapsed = currentTime - startTime
    const progress = Math.min(elapsed / duration, 1)
    // easeOutExpo
    const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress)
    animatedStats[key] = Math.round(start + diff * eased)
    if (progress < 1) {
      requestAnimationFrame(step)
    }
  }
  requestAnimationFrame(step)
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

    // 计算今日对话数
    const today = new Date().toISOString().split('T')[0]
    stats.value.todayConversations = sessions.filter(s =>
      s.created_at && s.created_at.startsWith(today)
    ).length || 0

    // 计算活跃用户数（有对话记录的用户）
    const uniqueUsers = new Set(sessions.map(s => s.user_id))
    stats.value.activeUsers = uniqueUsers.size || 0

    // 触发动画
    Object.keys(stats.value).forEach(key => {
      animateNumber(key, stats.value[key])
    })
  } catch (error) {
    ElMessage.error('加载统计数据失败')
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.dashboard {
  padding: 28px 32px;
  min-height: 100%;
}

/* 入场动画 */
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

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 28px;
}

.stat-card {
  position: relative;
  border-radius: var(--radius-md);
  background: #fff;
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  transition: var(--transition);
  cursor: default;
}

.stat-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-lg);
}

.stat-card-inner {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 22px 20px;
  position: relative;
  z-index: 1;
}

.stat-card-bg {
  position: absolute;
  right: -20px;
  bottom: -20px;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  opacity: 0.06;
  transition: var(--transition);
}

.stat-card:hover .stat-card-bg {
  transform: scale(1.5);
  opacity: 0.1;
}

.stat-card-bg.blue { background: var(--primary); }
.stat-card-bg.green { background: var(--success); }
.stat-card-bg.purple { background: #8b5cf6; }
.stat-card-bg.orange { background: var(--warning); }

.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  color: #fff;
  flex-shrink: 0;
}

.stat-icon.blue {
  background: linear-gradient(135deg, #4f6ef7, #6b8cff);
}

.stat-icon.green {
  background: linear-gradient(135deg, #22c55e, #4ade80);
}

.stat-icon.purple {
  background: linear-gradient(135deg, #8b5cf6, #a78bfa);
}

.stat-icon.orange {
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 30px;
  font-weight: 800;
  color: var(--gray-800);
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: var(--gray-500);
  margin-top: 4px;
}

/* 内容区域 */
.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.section-card {
  background: #fff;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  padding: 24px;
}

.section-header {
  margin-bottom: 20px;
}

.section-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--gray-800);
  margin: 0;
}

.section-icon {
  font-size: 20px;
  color: var(--primary);
}

/* 快捷操作卡片 */
.action-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--gray-200);
  cursor: pointer;
  transition: var(--transition);
}

.action-card:hover {
  border-color: var(--primary-light);
  background: var(--primary-bg);
  transform: translateX(4px);
}

.action-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  color: #fff;
  flex-shrink: 0;
}

.action-text {
  flex: 1;
}

.action-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-800);
}

.action-desc {
  font-size: 12px;
  color: var(--gray-500);
  margin-top: 2px;
}

.action-arrow {
  font-size: 16px;
  color: var(--gray-400);
  transition: var(--transition);
}

.action-card:hover .action-arrow {
  color: var(--primary);
  transform: translateX(4px);
}

/* 快速开始 */
.quick-start-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quick-start-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: var(--transition);
  border: 1px solid transparent;
}

.quick-start-item:hover {
  background: var(--gray-50);
  border-color: var(--gray-200);
}

.qs-number {
  font-size: 20px;
  font-weight: 800;
  color: var(--gray-200);
  width: 32px;
  text-align: center;
  flex-shrink: 0;
  transition: var(--transition);
}

.quick-start-item:hover .qs-number {
  color: var(--primary-light);
}

.qs-content {
  flex: 1;
}

.qs-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-800);
}

.qs-desc {
  font-size: 12px;
  color: var(--gray-500);
  margin-top: 2px;
}

.qs-arrow {
  font-size: 16px;
  color: var(--gray-400);
  transition: var(--transition);
}

.quick-start-item:hover .qs-arrow {
  color: var(--primary);
  transform: translateX(4px);
}

/* 响应式 */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .dashboard {
    padding: 16px;
  }
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
