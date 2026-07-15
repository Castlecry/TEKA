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
            <div class="session-time">
              <el-tag
                v-if="session.module"
                size="small"
                effect="plain"
                :style="{ background: getModuleColor(session.module) + '15', color: getModuleColor(session.module), border: 0 }"
                style="margin-right: 4px; padding: 0 6px; height: 16px; line-height: 16px;"
              >
                {{ getModuleName(session.module) }}
              </el-tag>
              {{ session.last_message_at }}
            </div>
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
            <el-icon :size="18" :color="currentModuleColor"><Component :is="currentModuleIcon" /></el-icon>
            {{ currentModuleName }}
          </h2>
        </div>
        <div class="header-actions">
          <!-- 模块切换 -->
          <div class="module-selector">
            <button
              v-for="mod in modules"
              :key="mod.id"
              class="module-tab"
              :class="{ active: currentModule === mod.id }"
              :style="currentModule === mod.id ? { borderColor: mod.color, color: mod.color } : {}"
              @click="switchModule(mod.id)"
            >
              <el-icon :size="14"><Component :is="getModuleIcon(mod.icon)" /></el-icon>
              <span>{{ mod.name }}</span>
            </button>
          </div>
          <div class="chat-mode-selector">
            <button
              v-for="mode in chatModes"
              :key="mode.value"
              class="mode-btn"
              :class="{ active: chatMode === mode.value }"
              @click="chatMode = mode.value"
            >
              <el-icon :size="14">
                <component :is="mode.icon" />
              </el-icon>
              <span>{{ mode.label }}</span>
            </button>
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
              <!-- 推理过程（折叠区，参考 DeepSeek 风格） -->
              <div v-if="message.role === 'assistant' && message.reasoning" class="reasoning-block">
                <div
                  class="reasoning-header"
                  @click="message.reasoningExpanded = !message.reasoningExpanded"
                >
                  <el-icon :size="14" class="reasoning-icon">
                    <component :is="message.reasoningExpanded ? ArrowDown : ArrowRight" />
                  </el-icon>
                  <span class="reasoning-label">
                    已思考<span v-if="message.reasoningDuration > 0">（用时 {{ message.reasoningDuration }} 秒）</span>
                  </span>
                </div>
                <div v-if="message.reasoningExpanded" class="reasoning-content">
                  <RichContent :content="message.reasoning" type="markdown" />
                </div>
              </div>
              <!-- 流式输出时使用纯文本，结束后使用 markdown 渲染 -->
              <template v-if="message.role === 'assistant'">
                <div v-if="message.streaming" class="streaming-text">{{ message.content }}</div>
                <RichContent v-else :content="message.content" type="markdown" />
              </template>
              <span v-else>{{ message.content }}</span>
              <!-- 文档下载附件 -->
              <div v-if="message.attachments && message.attachments.length > 0" class="message-attachments">
                <div
                  v-for="att in message.attachments"
                  :key="att.file_id"
                  class="attachment-card"
                  :class="att.format"
                  @click="downloadAttachment(att)"
                  style="cursor: pointer;"
                >
                  <el-icon :size="20" class="attachment-icon">
                    <Document v-if="att.format === 'word'" />
                    <Reading v-else />
                  </el-icon>
                  <div class="attachment-info">
                    <div class="attachment-name">{{ att.filename }}</div>
                    <div class="attachment-meta">
                      {{ att.format === 'word' ? 'Word 文档' : 'PDF 文档' }} · {{ att.size_kb }} KB
                    </div>
                  </div>
                  <el-icon :size="16" class="attachment-download"><Download /></el-icon>
                </div>
              </div>
              <!-- 消息操作栏（仅 AI 消息） -->
              <div v-if="message.role === 'assistant' && message.content" class="message-actions">
                <button class="action-btn" :title="copiedIndex === index ? '已复制' : '复制'" @click="copyMessage(index)">
                  <el-icon :size="14"><CopyDocument v-if="copiedIndex !== index" /><Check v-else /></el-icon>
                </button>
                <button class="action-btn" title="重新生成" :disabled="loading" @click="regenerateMessage(index)">
                  <el-icon :size="14"><RefreshRight /></el-icon>
                </button>
                <button class="action-btn" :class="{ active: message.favorited }" :title="message.favorited ? '取消收藏' : '收藏此回复'" @click="toggleFavoriteMessage(index)">
                  <el-icon :size="14"><Star /></el-icon>
                </button>
                <button class="action-btn" :class="{ active: message.feedback === -1 }" title="没帮助" @click="submitFeedback(index, -1)">
                  <el-icon :size="14"><WarningFilled /></el-icon>
                </button>
              </div>
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
        <!-- 已选文件标签 -->
        <div v-if="selectedFile" class="selected-file-tag">
          <el-icon :size="14"><Document /></el-icon>
          <span>{{ selectedFile.name }}</span>
          <el-icon :size="14" class="remove-file" @click="selectedFile = null"><Close /></el-icon>
        </div>
        <!-- 工具栏：搜索模式 + 模型来源 + 知识库选择 -->
        <div class="input-toolbar">
          <div class="toolbar-left">
            <button class="toolbar-btn" :class="{ active: useWeb }" @click="useWeb = !useWeb">
              <el-icon :size="16"><Connection /></el-icon>
              <span>{{ useWeb ? '联网搜索' : '本地检索' }}</span>
              <div v-if="useWeb" class="toolbar-dot"></div>
            </button>
            <button class="toolbar-btn" :class="{ active: modelProvider === 'local' }" @click="modelProvider = modelProvider === 'api' ? 'local' : 'api'">
              <el-icon :size="16"><Cpu /></el-icon>
              <span>{{ modelProvider === 'api' ? '云端 API' : '本地模型' }}</span>
            </button>
            <!-- 自由问答模式下显示知识库选择 -->
            <el-select
              v-if="currentModule === 'general'"
              v-model="selectedKBIds"
              multiple
              placeholder="选择知识库（可选）"
              class="kb-selector"
              size="small"
              collapse-tags
              collapse-tags-tooltip
              :max-collapse-tags="2"
            >
              <el-option
                v-for="kb in availableKnowledgeBases"
                :key="kb.id"
                :label="kb.name"
                :value="kb.id"
              />
            </el-select>
          </div>
        </div>
        <div class="chat-input">
          <!-- 文件上传按钮 -->
          <label class="upload-file-btn" :class="{ disabled: loading }">
            <el-icon :size="18"><Paperclip /></el-icon>
            <input
              type="file"
              accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt,.md,.png,.jpg,.jpeg"
              hidden
              @change="onFileSelected"
              :disabled="loading"
            />
          </label>
          <input
            v-model="inputMessage"
            :placeholder="selectedFile ? '输入你的问题（可选）...' : '输入你的问题...'"
            class="input-field"
            @keyup.enter="sendMessage"
            :disabled="loading"
          />
          <button
            class="send-btn"
            :class="{ active: (inputMessage.trim() || selectedFile) && !loading }"
            :disabled="(!inputMessage.trim() && !selectedFile) || loading"
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
import { ref, reactive, nextTick, onMounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ChatLineRound, User, Promotion, Plus, Delete, Setting,
  Menu, Close, Connection, MagicStick, Sunny, Cpu, Monitor, Document, Reading, Download, Paperclip,
  CopyDocument, Check, RefreshRight, Star, WarningFilled,
  ArrowDown, ArrowRight
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import RichContent from '@/components/RichContent.vue'
import request from '@/utils/request'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const route = useRoute()
const router = useRouter()
const token = ref(localStorage.getItem('token') || '')
// 从 localStorage 恢复当前会话 ID，跨页面切换保持
// 默认为 'pending'，表示当前没有激活的真实会话（显示欢迎页）
const currentSessionId = ref(localStorage.getItem('currentSessionId') || 'pending')
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const useWeb = ref(false)
const chatMode = ref('rag')
const modelProvider = ref('api')
const messagesContainer = ref(null)
const sessions = ref([])
const sidebarCollapsed = ref(false)
const settingsOpen = ref(false)
const copiedIndex = ref(-1)
const selectedKBIds = ref([])
const availableKnowledgeBases = ref([])
let lastUserId = userStore.user?.id || null

// 模块相关
const modules = ref([])
const currentModule = ref('general')

const iconMap = { Document, Monitor, OfficeBuilding: Monitor, ChatLineRound, Sunny }

const getModuleIcon = (iconName) => iconMap[iconName] || ChatLineRound

// 模块颜色与名称映射（用于历史对话列表的小徽标）
const moduleColorMap = { policy: '#4f6ef7', tech: '#22c55e', admin: '#f59e0b', general: '#8b5cf6' }
const moduleNameMap = { policy: '规章制度', tech: '产品技术', admin: '行政服务', general: '自由问答' }
const getModuleColor = (mod) => moduleColorMap[mod] || '#8b5cf6'
const getModuleName = (mod) => moduleNameMap[mod] || '自由问答'

const currentModuleData = computed(() => {
  return modules.value.find(m => m.id === currentModule.value) || modules.value[3] || { name: '自由问答', color: '#8b5cf6', icon: 'ChatLineRound', example_questions: [] }
})

const currentModuleName = computed(() => currentModuleData.value.name || '自由问答')
const currentModuleColor = computed(() => currentModuleData.value.color || '#8b5cf6')
const exampleQuestions = computed(() => currentModuleData.value.example_questions || [])

const loadModules = async () => {
  try {
    const data = await request.get('/knowledge-bases/modules')
    modules.value = data
  } catch (error) {
    console.error('加载模块列表失败', error)
  }
}

const switchModule = (moduleId) => {
  // 切换模块：不创建新会话，仅改变 RAG 检索的知识库范围
  // 这样用户在历史对话中切换模块，可以看到其他模块的回答
  currentModule.value = moduleId
  localStorage.setItem('currentModule', moduleId)
}

// 模式配置
const chatModes = [
  { value: 'rag', label: 'RAG', icon: 'Sunny' },
  { value: 'agent', label: 'Agent', icon: 'Cpu' },
  { value: 'langgraph', label: 'LangGraph', icon: 'Monitor' }
]

const settings = reactive({
  top_k: 5,
  similarity_threshold: 0.5,
})

const createNewSession = () => {
  // 点击"新对话"：清空当前对话区，回到欢迎页
  // 不创建任何历史记录，只有用户真正发送消息后才会在后端创建
  currentSessionId.value = 'pending'
  localStorage.setItem('currentSessionId', 'pending')
  messages.value = []
  inputMessage.value = ''
  selectedFile.value = null
}

const switchSession = (sessionId) => {
  currentSessionId.value = sessionId
  localStorage.setItem('currentSessionId', sessionId)
  // 恢复该会话所属的模块
  const sess = sessions.value.find(s => s.session_id === sessionId || s.conversation_id === sessionId)
  if (sess && sess.module) {
    currentModule.value = sess.module
    localStorage.setItem('currentModule', sess.module)
  }
  loadHistory(sessionId)
  checkFavoriteStatus(sessionId)
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

// ========== 收藏功能（单条消息级别） ==========

// 检查当前对话中哪些消息已收藏
const checkFavoriteStatus = async (conversationId) => {
  if (!conversationId || conversationId === 'default') return
  try {
    // 遍历所有 AI 消息，逐条检查收藏状态
    for (let i = 0; i < messages.value.length; i++) {
      const msg = messages.value[i]
      if (msg.role === 'assistant' && msg.content) {
        const res = await request.get(`/chat/favorites/check/${conversationId}/${msg.id || i}`)
        msg.favorited = res?.favorited || false
      }
    }
  } catch (e) {
    console.error('检查收藏状态失败', e)
  }
}

// 切换单条 AI 消息的收藏状态
const toggleFavoriteMessage = async (index) => {
  const message = messages.value[index]
  if (!message || message.role !== 'assistant') return

  if (!currentSessionId.value || currentSessionId.value === 'default') {
    ElMessage.warning('请先进行对话再收藏')
    return
  }

  // 找到对应的用户问题（上一条用户消息）
  let query = ''
  for (let i = index - 1; i >= 0; i--) {
    if (messages.value[i].role === 'user') {
      query = messages.value[i].content
      break
    }
  }

  const title = query.slice(0, 50) || '未命名收藏'

  try {
    const res = await request.post('/chat/favorite', {
      conversation_id: currentSessionId.value,
      message_id: message.id || String(index),
      title,
      query,
      answer: message.content,
      module: currentModule.value || 'general',
    })
    message.favorited = res?.favorited || false
    ElMessage.success(res?.message || (message.favorited ? '已收藏' : '已取消收藏'))
  } catch (e) {
    console.error('收藏操作失败', e)
    ElMessage.error('操作失败')
  }
}

const selectedFile = ref(null)

const onFileSelected = (event) => {
  const file = event.target.files[0]
  if (file) {
    selectedFile.value = file
  }
}

const sendMessage = async () => {
  const hasMessage = inputMessage.value.trim()
  const hasFile = selectedFile.value

  if ((!hasMessage && !hasFile) || loading.value) return

  const message = inputMessage.value.trim() || (hasFile ? '请分析这个文件的内容' : '')
  const file = selectedFile.value
  inputMessage.value = ''
  selectedFile.value = null

  const displayContent = file ? `[文件: ${file.name}] ${message}` : message
  messages.value.push({
    id: `msg_${Date.now()}_u`,
    role: 'user',
    content: displayContent,
    created_at: new Date().toLocaleTimeString(),
  })

  loading.value = true
  scrollToBottom()

  try {
    if (file) {
      // 文件 + 问题：使用 upload-and-ask
      const formData = new FormData()
      formData.append('file', file)
      formData.append('message', message)
      // 如果当前是"pending"或"default"，生成新会话 ID
      let sendConvId = currentSessionId.value
      if (!sendConvId || sendConvId === 'pending' || sendConvId === 'default') {
        sendConvId = crypto.randomUUID ? crypto.randomUUID() : Date.now().toString() + Math.random().toString(36).slice(2)
      }
      formData.append('conversation_id', sendConvId)
      // 同步当前会话 ID
      currentSessionId.value = sendConvId
      localStorage.setItem('currentSessionId', sendConvId)

      const res = await request.post('/chat/upload-and-ask', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      messages.value.push({
        id: `msg_${Date.now()}_a`,
        role: 'assistant',
        content: res.answer || '无响应',
        created_at: new Date().toLocaleTimeString(),
      })
      if (res.conversation_id) currentSessionId.value = res.conversation_id
    } else {
      // 纯文本：使用 HTTP SSE 流式
      const token = localStorage.getItem('token')
      // 如果当前是"pending"（新对话）或"default"（初始），生成新的会话 ID 发送到后端
      let sendConvId = currentSessionId.value
      if (!sendConvId || sendConvId === 'pending' || sendConvId === 'default') {
        sendConvId = crypto.randomUUID ? crypto.randomUUID() : Date.now().toString() + Math.random().toString(36).slice(2)
      }
      // SSE 直连后端（绕过 Vite 代理防止缓冲）
      const backendHost = window.location.hostname === 'localhost' ? 'http://localhost:8888' : ''
      const response = await fetch(`${backendHost}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: message,
          conversation_id: sendConvId,
          use_web: useWeb.value,
          mode: chatMode.value,
          provider: modelProvider.value,
          module: currentModule.value,
          // 自由问答模式下，如果用户选择了知识库则使用之；否则使用所有个人+通用知识库
          knowledge_base_ids: currentModule.value === 'general' && selectedKBIds.value.length > 0
            ? selectedKBIds.value
            : undefined,
        }),
      })

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: '请求失败' }))
        throw new Error(err.detail || `HTTP ${response.status}`)
      }

      // 读取 SSE 流
      if (!response.body) {
        throw new Error('浏览器不支持流式读取，请使用现代浏览器')
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let fullAnswer = ''
      let reasoningText = ''
      let reasoningStartTime = 0

      // 创建 assistant 消息占位
      const assistantMsg = reactive({
        id: `msg_${Date.now()}_a`,
        role: 'assistant',
        content: '',
        reasoning: '',
        reasoningDuration: 0,
        reasoningExpanded: false,
        streaming: true,
        created_at: new Date().toLocaleTimeString()
      })
      messages.value.push(assistantMsg)

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') continue
            try {
              const parsed = JSON.parse(data)
              if (parsed.type === 'meta' && parsed.conversation_id) {
                currentSessionId.value = parsed.conversation_id
                localStorage.setItem('currentSessionId', parsed.conversation_id)
              } else if (parsed.type === 'reasoning' && parsed.text) {
                if (reasoningStartTime === 0) reasoningStartTime = Date.now()
                reasoningText += parsed.text
                assistantMsg.reasoning = reasoningText
                assistantMsg.reasoningDuration = Math.floor((Date.now() - reasoningStartTime) / 1000)
                // 逐字渲染：yield 到浏览器重绘
                scrollToBottom()
                await new Promise(r => setTimeout(r, 0))
              } else if (parsed.type === 'content' && parsed.text) {
                fullAnswer += parsed.text
                assistantMsg.content = fullAnswer
                scrollToBottom()
                await new Promise(r => setTimeout(r, 0))
              } else if (parsed.type === 'chunk' && parsed.content) {
                fullAnswer += parsed.content
                assistantMsg.content = fullAnswer
                scrollToBottom()
                await new Promise(r => setTimeout(r, 0))
              } else if (parsed.type === 'attachments' && Array.isArray(parsed.items) && parsed.items.length > 0) {
                assistantMsg.attachments = parsed.items
              } else if (parsed.type === 'error') {
                assistantMsg.content = `错误: ${parsed.content}`
              }
            } catch (e) {}
          }
        }
      }

      if (!fullAnswer) {
        assistantMsg.content = '(空响应)'
      }
      // 流式结束，切换到 markdown 渲染
      assistantMsg.streaming = false
    }

    loadSessions()
    // 检查收藏状态
    checkFavoriteStatus(currentSessionId.value)
  } catch (e) {
    console.error('发送失败', e)
    messages.value.push({
      id: `msg_${Date.now()}_a`,
      role: 'assistant',
      content: `请求失败: ${e.message || '请检查后端服务'}`,
      created_at: new Date().toLocaleTimeString(),
    })
  } finally {
    loading.value = false
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 下载附件文档（fetch blob 触发下载，避免 <a download> 跨域失效）
const downloadAttachment = async (att) => {
  const url = att.download_url + '?token=' + (token.value || '')
  try {
    const resp = await fetch(url)
    if (!resp.ok) throw new Error('下载失败')
    const blob = await resp.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = att.filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(a.href)
  } catch (e) {
    console.error('下载失败', e)
    ElMessage?.error?.('文件下载失败')
  }
}

// 复制回答
const copyMessage = async (index) => {
  const msg = messages.value[index]
  if (!msg) return
  try {
    await navigator.clipboard.writeText(msg.content)
    copiedIndex.value = index
    setTimeout(() => { copiedIndex.value = -1 }, 1500)
  } catch (e) {
    // 降级方案
    const textarea = document.createElement('textarea')
    textarea.value = msg.content
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    copiedIndex.value = index
    setTimeout(() => { copiedIndex.value = -1 }, 1500)
  }
}

// 重新生成
const regenerateMessage = (index) => {
  if (loading.value) return
  // 找到对应的用户问题（上一条 user 消息）
  let userMsgIndex = -1
  for (let i = index - 1; i >= 0; i--) {
    if (messages.value[i].role === 'user') {
      userMsgIndex = i
      break
    }
  }
  if (userMsgIndex < 0) return

  const userMsg = messages.value[userMsgIndex].content
  // 删除从用户消息开始的后续消息
  messages.value.splice(userMsgIndex)
  // 重新发送
  inputMessage.value = userMsg.replace(/^\[文件: [^\]]+\] /, '')
  sendMessage()
}

// 消息反馈（点赞/点踩）
const submitFeedback = async (index, rating) => {
  const msg = messages.value[index]
  if (!msg || msg.role !== 'assistant') return

  // 乐观更新
  const oldRating = msg.feedback || 0
  msg.feedback = oldRating === rating ? 0 : rating

  try {
    await request.post('/chat/feedback', {
      conversation_id: currentSessionId.value,
      message_id: `msg_${index}`,
      rating: msg.feedback,
    })
  } catch (e) {
    // 失败回滚
    msg.feedback = oldRating
    console.error('反馈提交失败', e)
  }
}

const resetChatState = () => {
  currentSessionId.value = 'default'
  localStorage.setItem('currentSessionId', 'default')
  messages.value = []
  sessions.value = []
  inputMessage.value = ''
  selectedFile.value = null
  loading.value = false
  selectedKBIds.value = []
}

// 加载自由问答模式下可选的知识库（通用库 + 用户的个人库，不含其他三个模块）
const loadAvailableKnowledgeBases = async () => {
  try {
    const kbs = await request.get('/knowledge-bases/', { params: { module: 'general' } })
    // 合并 general 共享库 + 用户自己的个人知识库
    const list = []
    for (const kb of kbs) {
      if (kb.module === 'general') list.push(kb)
    }
    // 额外加载用户的个人知识库（任意模块）
    const all = await request.get('/knowledge-bases/')
    for (const kb of all) {
      if (kb.is_personal && kb.owner_id === userStore.user?.id) {
        list.push(kb)
      }
    }
    availableKnowledgeBases.value = list
  } catch (e) {
    console.error('加载可选知识库失败', e)
  }
}

onMounted(async () => {
  lastUserId = userStore.user?.id || null
  await loadModules()
  await loadSessions()
  await loadAvailableKnowledgeBases()

  // 处理从 Dashboard 跳转来的模块和问题
  if (route.query.module) {
    currentModule.value = route.query.module
    localStorage.setItem('currentModule', route.query.module)
  } else {
    // 恢复上次的模块选择
    const savedModule = localStorage.getItem('currentModule')
    if (savedModule) currentModule.value = savedModule
  }
  if (route.query.question) {
    inputMessage.value = route.query.question
  }
  // 处理从收藏页跳转来的会话
  if (route.query.session) {
    currentSessionId.value = route.query.session
    localStorage.setItem('currentSessionId', route.query.session)
    // 恢复该会话的模块
    const sess = sessions.value.find(s => s.session_id === route.query.session || s.conversation_id === route.query.session)
    if (sess && sess.module) {
      currentModule.value = sess.module
      localStorage.setItem('currentModule', sess.module)
    }
    await loadHistory(route.query.session)
    await checkFavoriteStatus(route.query.session)
  } else {
    // 恢复上次活跃会话（localStorage 中持久化的）
    const savedSessionId = localStorage.getItem('currentSessionId')
    if (savedSessionId && savedSessionId !== 'default' && savedSessionId !== 'pending') {
      // 检查该会话是否真实存在于后端会话列表中
      const exists = sessions.value.find(s => s.session_id === savedSessionId || s.conversation_id === savedSessionId)
      if (exists) {
        currentSessionId.value = savedSessionId
        // 恢复该会话所属模块
        if (exists.module) {
          currentModule.value = exists.module
          localStorage.setItem('currentModule', exists.module)
        }
        await loadHistory(savedSessionId)
        await checkFavoriteStatus(savedSessionId)
      } else {
        // 会话不存在（可能被删除或从未在后端创建），清理 localStorage
        localStorage.removeItem('currentSessionId')
        currentSessionId.value = 'pending'
      }
    } else {
      // 初始状态：显示欢迎页
      currentSessionId.value = 'pending'
    }
  }
  // 清空 query 参数
  router.replace({ query: {} })
})

watch(
  () => userStore.user?.id,
  (newId) => {
    if (newId && lastUserId && newId !== lastUserId) {
      resetChatState()
    }
    lastUserId = newId
  }
)
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

/* 模块切换 */
.module-selector {
  display: flex;
  align-items: center;
  background: var(--gray-100);
  border-radius: 20px;
  padding: 2px;
  gap: 2px;
}

.module-tab {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  border: 2px solid transparent;
  background: transparent;
  border-radius: 18px;
  font-size: 13px;
  color: var(--gray-500);
  cursor: pointer;
  transition: var(--transition);
  white-space: nowrap;
}

.module-tab:hover {
  color: var(--gray-700);
  background: rgba(255, 255, 255, 0.5);
}

.module-tab.active {
  background: #fff;
  font-weight: 500;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.module-tab .el-icon {
  flex-shrink: 0;
}

.chat-mode-selector {
  display: flex;
  align-items: center;
  background: var(--gray-100);
  border-radius: 20px;
  padding: 2px;
  gap: 2px;
}

.mode-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: none;
  background: transparent;
  border-radius: 18px;
  font-size: 13px;
  color: var(--gray-500);
  cursor: pointer;
  transition: var(--transition);
  white-space: nowrap;
}

.mode-btn:hover {
  color: var(--gray-700);
}

.mode-btn.active {
  background: #fff;
  color: var(--primary);
  font-weight: 500;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.mode-btn .el-icon {
  flex-shrink: 0;
}

/* ========== 输入区域 ========== */
.chat-input-wrapper {
  padding: 12px 24px 20px;
  background: transparent;
  flex-shrink: 0;
}

/* 输入工具栏 */
.input-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 6px;
}

.toolbar-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 1px solid transparent;
  border-radius: 20px;
  background: transparent;
  color: var(--gray-500);
  font-size: 13px;
  cursor: pointer;
  transition: var(--transition);
  position: relative;
  user-select: none;
}

.toolbar-btn:hover {
  background: rgba(79, 110, 247, 0.08);
  color: var(--primary);
}

.toolbar-btn.active {
  background: var(--primary-bg);
  border-color: var(--primary-light);
  color: var(--primary);
  font-weight: 500;
}

.toolbar-btn .toolbar-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--primary);
  box-shadow: 0 0 8px var(--primary);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
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

/* 文件上传按钮 */
.upload-file-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--gray-500);
  transition: var(--transition);
  flex-shrink: 0;
}
.upload-file-btn:hover {
  background: var(--gray-100);
  color: var(--primary);
}
.upload-file-btn.disabled {
  pointer-events: none;
  opacity: 0.4;
}

/* 已选文件标签 */
.selected-file-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  margin-bottom: 8px;
  background: var(--primary-bg);
  border: 1px solid var(--primary-light);
  border-radius: 20px;
  font-size: 13px;
  color: var(--primary);
}
.selected-file-tag .remove-file {
  cursor: pointer;
  color: var(--gray-400);
}
.selected-file-tag .remove-file:hover {
  color: var(--danger);
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

/* 附件下载卡片 */
.message-attachments {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.attachment-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #f0f7ff 0%, #e6f0ff 100%);
  border: 1px solid rgba(79, 110, 247, 0.15);
  border-radius: var(--radius-sm);
  text-decoration: none;
  color: var(--gray-700);
  transition: var(--transition);
  cursor: pointer;
}

.attachment-card:hover {
  background: linear-gradient(135deg, #e6f0ff 0%, #d6e4ff 100%);
  border-color: var(--primary);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 110, 247, 0.15);
}

.attachment-card.word {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border-color: rgba(37, 99, 235, 0.2);
}

.attachment-card.word:hover {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border-color: #2563eb;
}

.attachment-card.pdf {
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border-color: rgba(220, 38, 38, 0.2);
}

.attachment-card.pdf:hover {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  border-color: #dc2626;
}

.attachment-icon {
  flex-shrink: 0;
  color: var(--primary);
}

.attachment-card.word .attachment-icon {
  color: #2563eb;
}

.attachment-card.pdf .attachment-icon {
  color: #dc2626;
}

.attachment-info {
  flex: 1;
  min-width: 0;
}

.attachment-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-800);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}

.attachment-meta {
  font-size: 12px;
  color: var(--gray-500);
}

.attachment-download {
  color: var(--gray-400);
  flex-shrink: 0;
}

.attachment-card:hover .attachment-download {
  color: var(--primary);
}

.attachment-card.word:hover .attachment-download {
  color: #2563eb;
}

.attachment-card.pdf:hover .attachment-download {
  color: #dc2626;
}

/* 流式输出纯文本（避免 markdown 渲染阻塞） */
.streaming-text {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
  font-size: 14px;
}

/* 推理过程（思考链）折叠区 */
.reasoning-block {
  margin-bottom: 12px;
  background: #f7f8fa;
  border: 1px solid #e6e8eb;
  border-radius: 8px;
  overflow: hidden;
}
.reasoning-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  cursor: pointer;
  user-select: none;
  font-size: 13px;
  color: #606266;
  transition: background 0.15s;
}
.reasoning-header:hover {
  background: #eef0f3;
}
.reasoning-icon {
  color: #8b5cf6;
  transition: transform 0.2s;
}
.reasoning-label {
  font-weight: 500;
  color: #8b5cf6;
}
.reasoning-content {
  padding: 12px 16px;
  border-top: 1px solid #e6e8eb;
  max-height: 400px;
  overflow-y: auto;
  font-size: 13px;
  line-height: 1.6;
  color: #606266;
  background: #fafbfc;
}
.reasoning-content :deep(p) {
  margin: 4px 0;
}

/* 消息操作栏 */
.message-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--gray-100);
  opacity: 0.6;
  transition: opacity 0.2s;
}

.message-item.assistant:hover .message-actions {
  opacity: 1;
}

.action-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--gray-400);
  transition: var(--transition);
}

.action-btn:hover {
  background: var(--gray-100);
  color: var(--primary);
}

.action-btn:disabled {
  cursor: not-allowed;
  opacity: 0.4;
}

.action-btn.active {
  color: var(--primary);
  background: var(--primary-bg);
}

/* 设置按钮 */
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

/* 文件上传按钮 */
.upload-file-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--gray-500);
  transition: var(--transition);
  flex-shrink: 0;
}
.upload-file-btn:hover {
  background: var(--gray-100);
  color: var(--primary);
}
.upload-file-btn.disabled {
  pointer-events: none;
  opacity: 0.4;
}

/* 已选文件标签 */
.selected-file-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  margin-bottom: 8px;
  background: var(--primary-bg);
  border: 1px solid var(--primary-light);
  border-radius: 20px;
  font-size: 13px;
  color: var(--primary);
}
.selected-file-tag .remove-file {
  cursor: pointer;
  color: var(--gray-400);
}
.selected-file-tag .remove-file:hover {
  color: var(--danger);
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
