<template>
  <div class="chat-container">
    <aside class="chat-sidebar">
      <div class="sidebar-header">
        <h3>对话历史</h3>
        <el-button size="small" icon="Plus" @click="createNewSession">新对话</el-button>
      </div>
      <div class="session-list">
        <div
          v-for="session in sessions"
          :key="session.session_id"
          class="session-item"
          :class="{ active: currentSessionId === session.session_id }"
          @click="switchSession(session.session_id)"
        >
          <Component :is="icons.MessageSquare" class="session-icon" />
          <div class="session-info">
            <div class="session-name">{{ session.last_message || '新对话' }}</div>
            <div class="session-time">{{ session.last_message_at }}</div>
          </div>
          <el-button
            size="small"
            icon="Delete"
            class="delete-btn"
            @click.stop="deleteSession(session.session_id)"
          />
        </div>
      </div>
    </aside>

    <main class="chat-main" v-loading="loading" element-loading-text="正在思考中...">
      <div class="chat-header">
        <h2>对话机器人</h2>
        <div class="header-actions">
          <el-switch v-model="useWeb" active-text="联网搜索" inactive-text="本地检索" />
        </div>
      </div>

      <div ref="messagesContainer" class="messages-container">
        <div
          v-for="(message, index) in messages"
          :key="index"
          class="message-item"
          :class="{ user: message.role === 'user' }"
        >
          <div class="message-avatar">
            <Component :is="message.role === 'user' ? icons.User : icons.Bot" />
          </div>
          <div class="message-content">
            <div class="message-header">
              <span class="message-role">{{ message.role === 'user' ? '我' : '助手' }}</span>
              <span class="message-time">{{ message.created_at }}</span>
            </div>
            <div class="message-body">
              <MarkdownRenderer v-if="message.role === 'assistant'" :content="message.content" />
              <span v-else>{{ message.content }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="chat-input">
        <el-input
          v-model="inputMessage"
          placeholder="请输入问题..."
          size="large"
          @keyup.enter="sendMessage"
        />
        <el-button
          type="primary"
          size="large"
          icon="Send"
          :loading="loading"
          @click="sendMessage"
        />
      </div>
    </main>

    <aside class="chat-settings">
      <div class="settings-section">
        <h4>检索设置</h4>
        <el-form :model="settings">
          <el-form-item label="Top K">
            <el-input-number v-model="settings.top_k" :min="1" :max="20" />
          </el-form-item>
          <el-form-item label="相似度阈值">
            <el-slider
              v-model="settings.similarity_threshold"
              :min="0"
              :max="1"
              :step="0.1"
            />
          </el-form-item>
        </el-form>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick, onMounted, onUnmounted } from 'vue'
import { MessageSquare, User, Bot } from '@element-plus/icons-vue'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import request from '@/utils/request'

const icons = { MessageSquare, User, Bot }

const currentSessionId = ref('default')
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const useWeb = ref(false)
const messagesContainer = ref(null)
const sessions = ref([])

const settings = reactive({
  top_k: 5,
  similarity_threshold: 0.5,
})

const createNewSession = () => {
  const newId = Date.now().toString()
  currentSessionId.value = newId
  messages.value = []
}

const switchSession = (sessionId) => {
  currentSessionId.value = sessionId
  loadHistory(sessionId)
}

const deleteSession = async (sessionId) => {
  try {
    await request.delete(`/chat/history/${sessionId}`)
    loadSessions()
    if (currentSessionId.value === sessionId) {
      createNewSession()
    }
  } catch (e) {
    console.error('删除会话失败', e)
  }
}

const loadSessions = async () => {
  try {
    const res = await request.get('/chat/sessions')
    // 后端直接返回数组 [{conversation_id, last_message, last_time, user_id}]
    sessions.value = (Array.isArray(res) ? res : []).map(s => ({
      ...s,
      session_id: s.conversation_id,
      last_message_at: s.last_time,
    }))
  } catch (e) {
    console.error('加载会话列表失败', e)
  }
}

const loadHistory = async (sessionId) => {
  try {
    const res = await request.get(`/chat/history/${sessionId}`)
    // 后端返回 {conversation_id, history: [...]}
    messages.value = Array.isArray(res?.history) ? res.history : []
    scrollToBottom()
  } catch (e) {
    console.error('加载对话历史失败', e)
  }
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || loading.value) return

  const message = inputMessage.value.trim()
  inputMessage.value = ''

  messages.value.push({
    role: 'user',
    content: message,
    created_at: new Date().toLocaleTimeString(),
  })

  loading.value = true
  scrollToBottom()

  try {
    // 后端期望的请求体格式: {message, conversation_id}
    const res = await request.post('/chat/message', {
      message: message,
      conversation_id: currentSessionId.value,
    })

    // 后端直接返回 {answer, sources}
    messages.value.push({
      role: 'assistant',
      content: res.answer || '未获取到回答',
      created_at: new Date().toLocaleTimeString(),
    })
  } catch (e) {
    messages.value.push({
      role: 'assistant',
      content: '网络错误，请重试',
      created_at: new Date().toLocaleTimeString(),
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

onMounted(() => {
  loadSessions()
  loadHistory(currentSessionId.value)
})

onUnmounted(() => {
  // 清理 WebSocket 连接等资源
})
</script>

<style scoped>
.chat-container {
  display: flex;
  height: calc(100vh - 60px);
}

.chat-sidebar {
  width: 240px;
  background: #fff;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.session-item:hover {
  background: #f3f4f6;
}

.session-item.active {
  background: #dbeafe;
}

.session-icon {
  font-size: 20px;
  color: #6b7280;
}

.session-info {
  flex: 1;
  overflow: hidden;
}

.session-name {
  font-size: 14px;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-time {
  font-size: 12px;
  color: #9ca3af;
}

.delete-btn {
  opacity: 0;
}

.session-item:hover .delete-btn {
  opacity: 1;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  position: relative;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
}

.chat-header h2 {
  margin: 0;
  font-size: 18px;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-item.user .message-content {
  align-items: flex-end;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 20px;
  color: #6b7280;
}

.message-content {
  max-width: 70%;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.message-role {
  font-size: 14px;
  font-weight: 600;
  color: #4b5563;
}

.message-time {
  font-size: 12px;
  color: #9ca3af;
}

.message-body {
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
}

.message-item:not(.user) .message-body {
  background: #fff;
  border: 1px solid #e5e7eb;
}

.message-item.user .message-body {
  background: #3b82f6;
  color: #fff;
}

.chat-input {
  display: flex;
  gap: 12px;
  padding: 16px 24px;
  background: #fff;
  border-top: 1px solid #e5e7eb;
}

.chat-input .el-input {
  flex: 1;
}

.chat-settings {
  width: 240px;
  background: #fff;
  border-left: 1px solid #e5e7eb;
  padding: 16px;
}

.settings-section {
  margin-bottom: 24px;
}

.settings-section h4 {
  margin: 0 0 16px 0;
  font-size: 14px;
}
</style>
