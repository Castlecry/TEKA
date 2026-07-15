<template>
  <div class="favorites-page">
    <!-- 页面头部 -->
    <div class="page-header fade-in-up" style="--delay: 0">
      <div class="header-content">
        <div class="header-text">
          <h2>
            <el-icon :size="22" color="#fff"><StarFilled /></el-icon>
            我的收藏
          </h2>
          <p>收藏的重要问答，随时回顾</p>
        </div>
      </div>
    </div>

    <!-- 收藏列表 -->
    <div class="favorites-list">
      <div v-if="loading" class="loading-state">
        <el-icon :size="32" class="is-loading"><Loading /></el-icon>
        <p>加载中...</p>
      </div>

      <div v-else-if="favorites.length === 0" class="empty-state">
        <el-icon :size="64" color="var(--gray-300)"><Star /></el-icon>
        <h3>暂无收藏</h3>
        <p>在对话中点击 AI 回复下方的星星图标即可收藏</p>
        <el-button type="primary" @click="$router.push('/chat')">
          去对话
        </el-button>
      </div>

      <div v-else class="favorites-grid">
        <div
          v-for="(fav, idx) in favorites"
          :key="fav.id"
          class="favorite-card fade-in-up"
          :style="{ '--delay': idx * 0.05 }"
          @click="showDetail(fav)"
        >
          <div class="favorite-card-header">
            <div class="favorite-icon">
              <el-icon :size="18" color="#f59e0b"><StarFilled /></el-icon>
            </div>
            <div class="favorite-module-tag" :style="{ background: getModuleColor(fav.module) + '18', color: getModuleColor(fav.module) }">
              {{ getModuleName(fav.module) }}
            </div>
            <button class="unfavorite-btn" @click.stop="removeFavorite(fav.id)" title="取消收藏">
              <el-icon :size="14"><Close /></el-icon>
            </button>
          </div>
          <div class="favorite-card-body">
            <div class="favorite-title">{{ fav.title || '未命名收藏' }}</div>
            <div class="favorite-preview">{{ fav.answer?.slice(0, 80) || '' }}{{ (fav.answer?.length || 0) > 80 ? '...' : '' }}</div>
            <div class="favorite-meta">
              <span class="favorite-time">{{ formatDate(fav.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 收藏详情对话框 -->
    <el-dialog
      v-model="detailVisible"
      :title="currentFav?.title || '收藏详情'"
      width="720px"
      class="favorite-detail-dialog"
      destroy-on-close
    >
      <div v-if="currentFav" class="detail-content">
        <!-- 用户问题 -->
        <div class="detail-section">
          <div class="detail-label">
            <el-icon :size="14"><ChatDotRound /></el-icon>
            <span>问题</span>
          </div>
          <div class="detail-query">{{ currentFav.query }}</div>
        </div>

        <!-- AI 回答 -->
        <div class="detail-section">
          <div class="detail-label">
            <el-icon :size="14"><Promotion /></el-icon>
            <span>回答</span>
          </div>
          <div class="detail-answer">
            <MarkdownRenderer :content="currentFav.answer" />
          </div>
        </div>

        <!-- 底部信息 -->
        <div class="detail-footer">
          <span class="detail-module" :style="{ color: getModuleColor(currentFav.module) }">
            {{ getModuleName(currentFav.module) }}
          </span>
          <span class="detail-time">{{ formatFullDate(currentFav.created_at) }}</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Star, StarFilled, Loading, Close, ChatDotRound, Promotion } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import request from '@/utils/request'

const favorites = ref([])
const loading = ref(true)
const detailVisible = ref(false)
const currentFav = ref(null)

const moduleColorMap = { policy: '#4f6ef7', tech: '#22c55e', admin: '#f59e0b', general: '#8b5cf6' }
const moduleNameMap = { policy: '规章制度', tech: '产品技术', admin: '行政服务', general: '自由问答' }
const getModuleColor = (mod) => moduleColorMap[mod] || '#8b5cf6'
const getModuleName = (mod) => moduleNameMap[mod] || '自由问答'

const loadFavorites = async () => {
  loading.value = true
  try {
    const data = await request.get('/chat/favorites')
    favorites.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error('加载收藏列表失败', error)
    ElMessage.error('加载收藏列表失败')
  } finally {
    loading.value = false
  }
}

const removeFavorite = async (favId) => {
  try {
    await ElMessageBox.confirm('确定要取消收藏这条问答吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })

    await request.delete(`/chat/favorites/${favId}`)
    ElMessage.success('已取消收藏')
    loadFavorites()
  } catch (e) {
    if (e !== 'cancel') {
      console.error('取消收藏失败', e)
      ElMessage.error('操作失败')
    }
  }
}

const showDetail = (fav) => {
  currentFav.value = fav
  detailVisible.value = true
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)} 天前`

  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
}

const formatFullDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(() => {
  loadFavorites()
})
</script>

<style scoped>
.favorites-page {
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
  background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%);
  border-radius: var(--radius-lg);
  padding: 28px 32px;
  color: #fff;
  overflow: hidden;
  position: relative;
}

.header-text h2 {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 8px 0;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-text p {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
}

/* 收藏列表 */
.favorites-list {
  min-height: 400px;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
}

.loading-state p,
.empty-state h3 {
  margin: 16px 0 8px;
  font-size: 18px;
  color: var(--gray-700);
}

.empty-state p {
  color: var(--gray-500);
  font-size: 14px;
  margin-bottom: 24px;
}

.favorites-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.favorite-card {
  background: #fff;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--gray-200);
  overflow: hidden;
  cursor: pointer;
  transition: var(--transition);
}

.favorite-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: #f59e0b;
}

.favorite-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px 0;
  gap: 8px;
}

.favorite-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background: rgba(245, 158, 11, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.favorite-module-tag {
  flex: 1;
  font-size: 12px;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 12px;
  text-align: center;
  white-space: nowrap;
}

.unfavorite-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  background: var(--gray-100);
  color: var(--gray-500);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--transition);
  flex-shrink: 0;
}

.unfavorite-btn:hover {
  background: #fee2e2;
  color: #ef4444;
}

.favorite-card-body {
  padding: 16px 20px 20px;
}

.favorite-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--gray-800);
  margin-bottom: 6px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.favorite-preview {
  font-size: 13px;
  color: var(--gray-500);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 10px;
}

.favorite-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.favorite-time {
  font-size: 12px;
  color: var(--gray-500);
}

/* 详情对话框 */
.detail-content {
  padding: 4px 0;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--gray-600);
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--gray-100);
}

.detail-query {
  font-size: 15px;
  color: var(--gray-800);
  line-height: 1.6;
  padding: 12px 16px;
  background: #f8f9fb;
  border-radius: var(--radius-md);
  border-left: 3px solid #4f6ef7;
}

.detail-answer {
  font-size: 14px;
  color: var(--gray-700);
  line-height: 1.7;
  padding: 12px 16px;
  background: #fafbfc;
  border-radius: var(--radius-md);
  border-left: 3px solid #f59e0b;
  max-height: 400px;
  overflow-y: auto;
}

.detail-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid var(--gray-100);
}

.detail-module {
  font-size: 13px;
  font-weight: 500;
}

.detail-time {
  font-size: 12px;
  color: var(--gray-400);
}

/* 响应式 */
@media (max-width: 768px) {
  .favorites-page {
    padding: 16px;
  }

  .favorites-grid {
    grid-template-columns: 1fr;
  }
}
</style>
