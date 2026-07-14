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
          <p>收藏的重要对话，随时回顾</p>
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
        <p>在对话中点击星星图标即可收藏重要对话</p>
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
          @click="openConversation(fav.conversation_id)"
        >
          <div class="favorite-card-header">
            <div class="favorite-icon">
              <el-icon :size="18" color="#f59e0b"><StarFilled /></el-icon>
            </div>
            <button class="unfavorite-btn" @click.stop="removeFavorite(fav.id, fav.conversation_id)" title="取消收藏">
              <el-icon :size="14"><Close /></el-icon>
            </button>
          </div>
          <div class="favorite-card-body">
            <div class="favorite-title">{{ fav.title || '未命名对话' }}</div>
            <div class="favorite-meta">
              <span class="favorite-time">{{ formatDate(fav.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Star, StarFilled, Loading, Close } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

const router = useRouter()
const favorites = ref([])
const loading = ref(true)

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

const removeFavorite = async (favId, conversationId) => {
  try {
    await ElMessageBox.confirm('确定要取消收藏这个对话吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })

    await request.post('/chat/favorite', { conversation_id: conversationId })
    ElMessage.success('已取消收藏')
    loadFavorites()
  } catch (e) {
    if (e !== 'cancel') {
      console.error('取消收藏失败', e)
      ElMessage.error('操作失败')
    }
  }
}

const openConversation = (conversationId) => {
  router.push({ path: '/chat', query: { session: conversationId } })
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
}

.favorite-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background: rgba(245, 158, 11, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
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
  margin-bottom: 8px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
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
