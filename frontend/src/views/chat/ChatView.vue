<template>
  <div class="chat-container">
    <!-- 侧边栏 -->
    <aside class="chat-sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <div class="sidebar-title" v-show="!sidebarCollapsed">
          <el-icon :size="18" color="var(--primary)"><ChatLineRound /></el-icon>
          <span>对话历史</span>
        </div>
        <button class="sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed">
          <el-icon :size="16"><Menu /></el-icon>
        </button>
      </div>
      <div class="sidebar-actions" v-show="!sidebarCollapsed">
        <button class="new-chat-btn" @click="createNewSession">
          <el-icon :size="16"><Plus /></el-icon>
          <span>新对话</span>
        </button>
      </div>
      <div class="session-list" v-show="!sidebarCollapsed">
        <div
          v-for="session in sessions"
          :key="session.session_id"
          class="session-item"
          :class="{ active: currentSessionId === session.session_id }"
          @click="switchSession(session.session_id)"
        >
          <el-icon :size="16" class="session-icon"><ChatLineRound /></el-icon>
          <div class="session-info">
            <div class="session-name">{{ session.last_message || '新对话' }}</div>
            <div class="session-time">{{ session.last_message_at }}</div>
          </div>
          <button
            class="delete-btn"
            @click.stop="deleteSession(session.session_id)"
          >
            <el-icon :size="14"><Delete /></el-icon>
          </button>
        </div>
        <div v-if="sessions.length === 0" class="session-empty">
          <el-icon :size="24" class="empty-icon"><ChatLineRound /></el-icon>
          <p>暂无对话记录</p>
        </div>
      </div>
    </aside>

    <!-- 主聊天区域 -->
    <main class="chat-main">
      <div class="chat-header">
        <div class="header-left">
          <button class="mobile-menu-btn" @click="sidebarCollapsed = !sidebarCollapsed">
            <el-icon :size="18"><Menu /></el-icon>
          </button>
          <h2>
            <el-icon :size="18" color="var(--primary)"><Promotion /></el-icon>
            AI 助手
          </h2>
        </div>
        <div class="header-actions">
          <div class="mode-switch" @click="useWeb = !useWeb">
            <div class="mode-indicator" :class="{ active: useWeb }"></div>
            <el-icon :size="14" :color="useWeb ? 'var(--primary)' : 'var(--gray-400)'">
              <Connection />
            </el-icon>
            <span class="mode-text" :class="{ active: useWeb }">
              {{ useWeb ? '联网搜索' : '本地检索' }}
            </span>
          </div>
          <button class="settings-toggle" @click="settingsOpen = !settingsOpen">
            <el-icon :size="16"><Setting /></el-icon>
          </button>
        </div>
      </div>

      <!-- 消息区域 -->
      <div ref="messagesContainer" class="messages-container">
        <!-- 空状态 -->
        <div v-if="messages.length === 0 && !loading" class="empty-state">
          <div class="empty-avatar">
            <el-icon :size="24"><MagicStick /></el-icon>
          </div>
          <h3>你好，有什么可以帮助你的？</h3>
          <p class="empty-subtitle">我是企业知识助手，可以帮你检索知识库、解答问题</p>
          <div class="example-questions">
            <div
              v-for="(q, idx) in exampleQuestions"
              :key="idx"
              class="example-card"
              @click="inputMessage = q; sendMessage()"
            >
              <div class="example-icon">
                <el-icon :size="14"><Sunny /></el-icon>
              </div>
              <span>{{ q }}</span>
            </div>
          </div>
        </div>

        <!-- 消息列表 -->
        <div
          v-for="(message, index) in messages"
          :key="index"
          class="message-item"
          :class="{
            user: message.role === 'user',
            assistant: message.role === 'assistant',
            'message-enter': true
          }"
          :style="{ '--delay': index * 0.05 }"
        >
          <div class="message-avatar" :class="message.role">
            <el-icon :size="16">
              <User v-if="message.role === 'user'" />
              <Promotion v-else />
            </el-icon>
          </div>
          <div class="message-content">
            <div class="message-header">
              <span class="message-role">{{ message.role === 'user' ? '你' : 'AI 助手' }}</span>
              <span class="message-time">{{ message.created_at }}</span>
            </div>
            <div class="message-body">
              <MarkdownRenderer v-if="message.role === 'assistant'" :content="message.content" />
              <span v-else>{{ message.content }}</span>
            </div>
          </div>
        </div>

        <!-- 打字指示器 -->
        <div v-if="loading" class="message-item assistant typing-indicator-wrapper">
          <div class="message-avatar assistant">
            <el-icon :size="16"><Promotion /></el-icon>
          </div>
          <div class="message-content">
            <div class="message-header">
              <span class="message-role">AI 助手</span>
              <span class="message-time">思考中...</span>
            </div>
            <div class="message-body typing-indicator">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="chat-input-wrapper">
        <div class="chat-input">
          <input
            v-model="inputMessage"
            placeholder="输入你的问题..."
            class="input-field"
            @keyup.enter="sendMessage"
            :disabled="loading"
          />
          <button
            class="send-btn"
            :class="{ active: inputMessage.trim() && !loading }"
            :disabled="!inputMessage.trim() || loading"
            @click="sendMessage"
          >
            <el-icon :size="18"><Promotion /></el-icon>
          </button>
        </div>
        <div class="input-hint">按 Enter 发送消息</div>
      </div>
    </main>

    <!-- 设置抽屉 -->
    <Transition name="drawer">
      <aside v-if="settingsOpen" class="chat-settings-drawer">
        <div class="drawer-header">
          <h4>
            <el-icon :size="16" color="var(--primary)"><Setting /></el-icon>
            检索设置
          </h4>
          <button class="drawer-close" @click="settingsOpen = false">
            <el-icon :size="16"><Close /></el-icon>
          </button>
        </div>
        <div class="drawer-body">
          <div class="setting-group">
            <label class="setting-label">
              <span>Top K</span>
              <span class="setting-value">{{ settings.top_k }}</span>
            </label>
            <el-slider
              v-model="settings.top_k"
              :min="1"
              :max="20"
              :show-tooltip="false"
            />
          </div>
          <div class="setting-group">
            <label class="setting-label">
              <span>相似度阈值</span>
              <span class="setting-value">{{ settings.similarity_threshold.toFixed(1) }}</span>
            </label>
            <el-slider
              v-model="settings.similarity_threshold"
              :min="0"
              :max="1"
              :step="0.1"
              :show-tooltip="false"
            />
          </div>
        </div>
      </aside>
    </Transition>

    <!-- 遮罩 -->
    <Transition name="fade">
      <div v-if="settingsOpen" class="drawer-overlay" @click="settingsOpen = false"></div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick, onMounted, onUnmounted } from 'vue'
import {
  ChatLineRound, User, Promotion, Plus, Delete, Setting,
  Menu, Close, Connection, MagicStick, Sunny
} from '@element-plus/icons-vue'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import request from '@/utils/request'

const currentSessionId = ref('default')
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const useWeb = ref(false)
const messagesContainer = ref(null)
const sessions = ref([])
const sidebarCollapsed = ref(false)
const settingsOpen = ref(false)

const settings = reactive({
  top_k: 5,
  similarity_threshold: 0.5,
})

const exampleQuestions = [
  '公司的报销流程是怎样的？',
  '如何申请年假和调休？',
  '最新的产品发布计划是什么？',
]

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
    const res = await request.post('/chat/message', {
      message: message,
      conversation_id: currentSessionId.value,
      use_web: useWeb.value,
    })

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
  height: 100%;
  background: var(--gray-50);
  position: relative;
  overflow: hidden;
}

/* ========== 侧边栏 ========== */
.chat-sidebar {
  width: 280px;
  background: #fff;
  border-right: 1px solid var(--gray-200);
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s;
  flex-shrink: 0;
  z-index: 10;
}

.chat-sidebar.collapsed {
  width: 56px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid var(--gray-100);
  min-height: 60px;
}

.sidebar-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 15px;
  font-weight: 600;
  color: var(--gray-800);
}

.sidebar-toggle {
  width: 32px;
  height: 32px;
  border: none;
  background: var(--gray-50);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--gray-500);
  transition: var(--transition);
}

.sidebar-toggle:hover {
  background: var(--gray-100);
  color: var(--gray-700);
}

.sidebar-actions {
  padding: 12px 16px;
}

.new-chat-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  border: 1px dashed var(--gray-300);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--gray-600);
  font-size: 14px;
  cursor: pointer;
  transition: var(--transition);
}

.new-chat-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
  background: var(--primary-bg);
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-list::-webkit-scrollbar {
  width: 4px;
}

.session-list::-webkit-scrollbar-thumb {
  background: var(--gray-200);
  border-radius: 2px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: var(--transition);
  margin-bottom: 2px;
  position: relative;
}

.session-item:hover {
  background: var(--gray-50);
}

.session-item.active {
  background: var(--primary-bg);
}

.session-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 3px;
  background: var(--primary);
  border-radius: 0 3px 3px 0;
}

.session-icon {
  color: var(--gray-400);
  flex-shrink: 0;
}

.session-item.active .session-icon {
  color: var(--primary);
}

.session-info {
  flex: 1;
  overflow: hidden;
}

.session-name {
  font-size: 13px;
  color: var(--gray-700);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
}

.session-time {
  font-size: 11px;
  color: var(--gray-400);
  margin-top: 2px;
}

.delete-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--gray-400);
  opacity: 0;
  transition: var(--transition);
  flex-shrink: 0;
}

.session-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background: #fef2f2;
  color: var(--danger);
}

.session-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: var(--gray-400);
}

.empty-icon {
  margin-bottom: 8px;
  opacity: 0.5;
}

.session-empty p {
  font-size: 13px;
  margin: 0;
}

/* ========== 主聊天区域 ========== */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 100%;
  background: var(--gray-50);
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--gray-100);
  z-index: 5;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.mobile-menu-btn {
  display: none;
  width: 36px;
  height: 36px;
  border: none;
  background: var(--gray-50);
  border-radius: var(--radius-sm);
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--gray-500);
}

.chat-header h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--gray-800);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.mode-switch {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: 20px;
  background: var(--gray-100);
  cursor: pointer;
  transition: var(--transition);
  user-select: none;
}

.mode-switch:hover {
  background: var(--gray-200);
}

.mode-indicator {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--gray-400);
  transition: var(--transition);
}

.mode-indicator.active {
  background: var(--primary);
  box-shadow: 0 0 8px var(--primary);
}

.mode-text {
  font-size: 13px;
  color: var(--gray-500);
  transition: var(--transition);
}

.mode-text.active {
  color: var(--primary);
  font-weight: 500;
}

.settings-toggle {
  width: 36px;
  height: 36px;
  border: none;
  background: var(--gray-50);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--gray-500);
  transition: var(--transition);
}

.settings-toggle:hover {
  background: var(--gray-100);
  color: var(--gray-700);
}

/* ========== 消息区域 ========== */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  scroll-behavior: smooth;
}

.messages-container::-webkit-scrollbar {
  width: 6px;
}

.messages-container::-webkit-scrollbar-thumb {
  background: var(--gray-200);
  border-radius: 3px;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 40px 20px;
  animation: fadeIn 0.6s ease;
}

.empty-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary), var(--primary-light));
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  margin-bottom: 20px;
  box-shadow: 0 8px 24px rgba(79, 110, 247, 0.3);
}

.empty-state h3 {
  font-size: 22px;
  font-weight: 700;
  color: var(--gray-800);
  margin: 0 0 8px 0;
}

.empty-subtitle {
  font-size: 14px;
  color: var(--gray-500);
  margin: 0 0 32px 0;
}

.example-questions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
  max-width: 680px;
  width: 100%;
}

.example-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  background: #fff;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: var(--transition);
  font-size: 13px;
  color: var(--gray-600);
}

.example-card:hover {
  border-color: var(--primary-light);
  background: var(--primary-bg);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.example-icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--primary-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
  flex-shrink: 0;
}

/* 消息项 */
.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  animation: messageIn 0.4s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}

@keyframes messageIn {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-item.user .message-content {
  align-items: flex-end;
}

/* 头像 */
.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #fff;
}

.message-avatar.user {
  background: linear-gradient(135deg, var(--primary), var(--primary-light));
  box-shadow: 0 2px 8px rgba(79, 110, 247, 0.25);
}

.message-avatar.assistant {
  background: linear-gradient(135deg, #8b5cf6, #a78bfa);
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.25);
}

/* 消息内容 */
.message-content {
  max-width: 70%;
  display: flex;
  flex-direction: column;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.message-item.user .message-header {
  flex-direction: row-reverse;
}

.message-role {
  font-size: 13px;
  font-weight: 600;
  color: var(--gray-700);
}

.message-time {
  font-size: 11px;
  color: var(--gray-400);
}

.message-body {
  padding: 12px 16px;
  border-radius: 16px;
  line-height: 1.6;
  font-size: 14px;
  word-break: break-word;
}

.message-item.assistant .message-body {
  background: #fff;
  color: var(--gray-800);
  border: 1px solid var(--gray-100);
  box-shadow: var(--shadow-sm);
  border-top-left-radius: 4px;
}

.message-item.user .message-body {
  background: linear-gradient(135deg, var(--primary), var(--primary-light));
  color: #fff;
  border-top-right-radius: 4px;
  box-shadow: 0 2px 12px rgba(79, 110, 247, 0.2);
}

/* 打字指示器 */
.typing-indicator-wrapper {
  animation: none;
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 16px 20px !important;
}

.typing-indicator .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--gray-400);
  animation: typingBounce 1.4s infinite ease-in-out;
}

.typing-indicator .dot:nth-child(1) { animation-delay: 0s; }
.typing-indicator .dot:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator .dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes typingBounce {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-6px);
    opacity: 1;
  }
}

/* ========== 输入区域 ========== */
.chat-input-wrapper {
  padding: 16px 24px 20px;
  background: transparent;
  flex-shrink: 0;
}

.chat-input {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 6px 6px 20px;
  background: #fff;
  border: 1px solid var(--gray-200);
  border-radius: 28px;
  box-shadow: var(--shadow-md);
  transition: var(--transition);
}

.chat-input:focus-within {
  border-color: var(--primary-light);
  box-shadow: 0 4px 16px rgba(79, 110, 247, 0.12);
}

.input-field {
  flex: 1;
  border: none;
  outline: none;
  font-size: 14px;
  color: var(--gray-800);
  background: transparent;
  line-height: 1.5;
  padding: 10px 0;
}

.input-field::placeholder {
  color: var(--gray-400);
}

.input-field:disabled {
  opacity: 0.6;
}

.send-btn {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: var(--gray-100);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--gray-400);
  transition: var(--transition);
  flex-shrink: 0;
}

.send-btn.active {
  background: linear-gradient(135deg, var(--primary), var(--primary-light));
  color: #fff;
  box-shadow: 0 2px 8px rgba(79, 110, 247, 0.3);
}

.send-btn.active:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(79, 110, 247, 0.4);
}

.send-btn:disabled {
  cursor: not-allowed;
}

.input-hint {
  text-align: center;
  font-size: 11px;
  color: var(--gray-400);
  margin-top: 8px;
}

/* ========== 设置抽屉 ========== */
.chat-settings-drawer {
  position: fixed;
  right: 0;
  top: 60px;
  bottom: 0;
  width: 320px;
  background: #fff;
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.08);
  z-index: 100;
  display: flex;
  flex-direction: column;
  animation: slideInRight 0.3s cubic-bezier(0.22, 1, 0.36, 1);
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--gray-100);
}

.drawer-header h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--gray-800);
}

.drawer-header h4 svg,
.drawer-header h4 .el-icon {
  color: var(--primary);
}

.drawer-close {
  width: 32px;
  height: 32px;
  border: none;
  background: var(--gray-50);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--gray-500);
  transition: var(--transition);
}

.drawer-close:hover {
  background: var(--gray-100);
  color: var(--gray-700);
}

.drawer-body {
  padding: 24px;
  flex: 1;
  overflow-y: auto;
}

.setting-group {
  margin-bottom: 28px;
}

.setting-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 500;
  color: var(--gray-700);
  margin-bottom: 12px;
}

.setting-value {
  font-size: 13px;
  font-weight: 600;
  color: var(--primary);
  background: var(--primary-bg);
  padding: 2px 10px;
  border-radius: 12px;
}

/* 遮罩 */
.drawer-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.2);
  z-index: 99;
  animation: fadeIn 0.3s ease;
}

/* Transition */
.drawer-enter-active {
  animation: slideInRight 0.3s cubic-bezier(0.22, 1, 0.36, 1);
}

.drawer-leave-active {
  animation: slideInRight 0.3s cubic-bezier(0.22, 1, 0.36, 1) reverse;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* ========== 响应式 ========== */
@media (max-width: 768px) {
  .chat-sidebar {
    position: fixed;
    left: 0;
    top: 60px;
    bottom: 0;
    z-index: 50;
    box-shadow: 4px 0 16px rgba(0, 0, 0, 0.1);
  }

  .chat-sidebar.collapsed {
    width: 0;
    overflow: hidden;
    border: none;
  }

  .mobile-menu-btn {
    display: flex;
  }

  .message-content {
    max-width: 85%;
  }

  .example-questions {
    grid-template-columns: 1fr;
  }

  .chat-settings-drawer {
    width: 100%;
  }
}
</style>
