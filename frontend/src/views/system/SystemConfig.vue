<template>
  <div class="system-config fade-in">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <div class="header-icon">
          <el-icon :size="20"><Setting /></el-icon>
        </div>
        <div>
          <h2>系统配置</h2>
          <p class="header-subtitle">管理系统参数、性能阈值与运行策略</p>
        </div>
      </div>
      <el-button
        type="primary"
        icon="Save"
        @click="saveConfig"
        :loading="saving"
        class="save-btn"
      >
        {{ saving ? '保存中...' : '保存配置' }}
      </el-button>
    </div>

    <!-- 配置卡片区域 -->
    <el-row :gutter="24" class="config-grid">
      <!-- 主题配置 -->
      <el-col :span="24">
        <div class="config-card theme-card">
          <div class="card-header">
            <div class="card-icon theme">
              <el-icon :size="20"><Brush /></el-icon>
            </div>
            <div class="card-title">
              <h3>主题外观</h3>
              <p>自定义界面主题色，打造个性化工作空间</p>
            </div>
          </div>
          <div class="theme-selector">
            <div
              v-for="(theme, key) in themeStore.presetThemes"
              :key="key"
              class="theme-option"
              :class="{ active: themeStore.currentTheme === key }"
              @click="themeStore.setTheme(key)"
            >
              <div class="theme-preview">
                <div class="theme-color" :style="{ background: theme.primary }"></div>
                <div class="theme-color light" :style="{ background: theme.primaryLight }"></div>
                <div class="theme-color bg" :style="{ background: theme.primaryBg }"></div>
              </div>
              <div class="theme-info">
                <span class="theme-name">{{ theme.name }}</span>
                <span class="theme-hex">{{ theme.primary }}</span>
              </div>
              <div class="theme-check" v-if="themeStore.currentTheme === key">
                <el-icon><Check /></el-icon>
              </div>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 文档解析配置 -->
      <el-col :span="12">
        <div class="config-card slide-in-left">
          <div class="card-header">
            <div class="card-icon doc">
              <el-icon :size="20"><Document /></el-icon>
            </div>
            <div class="card-title">
              <h3>文档解析配置</h3>
              <p>控制文档上传与切片参数</p>
            </div>
          </div>
          <el-form :model="config.document" label-position="top" class="config-form">
            <el-form-item label="上传大小限制 (MB)">
              <div class="input-with-unit">
                <el-input-number v-model="config.document.max_upload_size" :min="1" :max="500" controls-position="right" />
                <span class="unit">MB</span>
              </div>
            </el-form-item>
            <el-form-item label="文本切片大小">
              <div class="input-with-unit">
                <el-input-number v-model="config.document.chunk_size" :min="100" :max="2000" controls-position="right" />
                <span class="unit">字符</span>
              </div>
            </el-form-item>
            <el-form-item label="切片重叠大小">
              <div class="input-with-unit">
                <el-input-number v-model="config.document.chunk_overlap" :min="0" :max="500" controls-position="right" />
                <span class="unit">字符</span>
              </div>
            </el-form-item>
          </el-form>
        </div>
      </el-col>

      <!-- 对话配置 -->
      <el-col :span="12">
        <div class="config-card slide-in-right">
          <div class="card-header">
            <div class="card-icon chat">
              <el-icon :size="20"><ChatDotRound /></el-icon>
            </div>
            <div class="card-title">
              <h3>对话配置</h3>
              <p>设置对话上下文与回答限制</p>
            </div>
          </div>
          <el-form :model="config.chat" label-position="top" class="config-form">
            <el-form-item label="最大上下文轮数">
              <div class="input-with-unit">
                <el-input-number v-model="config.chat.max_context_rounds" :min="1" :max="50" controls-position="right" />
                <span class="unit">轮</span>
              </div>
            </el-form-item>
            <el-form-item label="最大回答长度">
              <div class="input-with-unit">
                <el-input-number v-model="config.chat.max_answer_length" :min="100" :max="5000" controls-position="right" />
                <span class="unit">字符</span>
              </div>
            </el-form-item>
            <el-form-item label="回答超时">
              <div class="input-with-unit">
                <el-input-number v-model="config.chat.timeout" :min="10" :max="120" controls-position="right" />
                <span class="unit">秒</span>
              </div>
            </el-form-item>
          </el-form>
        </div>
      </el-col>

      <!-- 检索配置 -->
      <el-col :span="12">
        <div class="config-card slide-in-left">
          <div class="card-header">
            <div class="card-icon search">
              <el-icon :size="20"><Search /></el-icon>
            </div>
            <div class="card-title">
              <h3>检索配置</h3>
              <p>优化知识检索精度与性能</p>
            </div>
          </div>
          <el-form :model="config.retrieval" label-position="top" class="config-form">
            <el-form-item label="默认 Top K">
              <div class="input-with-unit">
                <el-input-number v-model="config.retrieval.top_k" :min="1" :max="20" controls-position="right" />
                <span class="unit">条</span>
              </div>
            </el-form-item>
            <el-form-item label="相似度阈值">
              <div class="slider-with-value">
                <el-slider v-model="config.retrieval.similarity_threshold" :min="0" :max="1" :step="0.1" />
                <span class="slider-value">{{ config.retrieval.similarity_threshold.toFixed(1) }}</span>
              </div>
            </el-form-item>
            <el-form-item label="检索超时">
              <div class="input-with-unit">
                <el-input-number v-model="config.retrieval.timeout" :min="5" :max="120" controls-position="right" />
                <span class="unit">秒</span>
              </div>
            </el-form-item>
          </el-form>
        </div>
      </el-col>

      <!-- LLM配置 -->
      <el-col :span="12">
        <div class="config-card slide-in-right">
          <div class="card-header">
            <div class="card-icon llm">
              <el-icon :size="20"><Cpu /></el-icon>
            </div>
            <div class="card-title">
              <h3>LLM 配置</h3>
              <p>调整大语言模型生成参数</p>
            </div>
          </div>
          <el-form :model="config.llm" label-position="top" class="config-form">
            <el-form-item label="模型温度">
              <div class="slider-with-value">
                <el-slider v-model="config.llm.temperature" :min="0" :max="1" :step="0.1" />
                <span class="slider-value">{{ config.llm.temperature.toFixed(1) }}</span>
              </div>
            </el-form-item>
            <el-form-item label="最大 Token 数">
              <div class="input-with-unit">
                <el-input-number v-model="config.llm.max_tokens" :min="512" :max="8192" controls-position="right" />
                <span class="unit">tokens</span>
              </div>
            </el-form-item>
          </el-form>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { reactive, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import { useThemeStore } from '@/stores/theme'

const themeStore = useThemeStore()

const config = reactive({
  document: {
    max_upload_size: 50,
    chunk_size: 500,
    chunk_overlap: 50,
  },
  retrieval: {
    top_k: 5,
    similarity_threshold: 0.5,
    timeout: 30,
  },
  chat: {
    max_context_rounds: 10,
    max_answer_length: 2000,
    timeout: 60,
  },
  llm: {
    temperature: 0.7,
    max_tokens: 2048,
  },
})

const saving = ref(false)

const loadConfig = async () => {
  try {
    const data = await request.get('/system/config/')
    if (data) {
      Object.assign(config, data)
    }
  } catch (error) {
    // 配置加载失败时使用默认值
  }
}

const saveConfig = async () => {
  saving.value = true
  try {
    await request.post('/system/config/', config)
    ElMessage.success('配置保存成功')
  } catch (error) {
    ElMessage.error('配置保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.system-config {
  padding: 24px;
  animation: fadeIn 0.35s ease-out;
}

/* 页面头部 */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 28px;
  animation: slideDown 0.4s ease-out;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--primary), var(--primary-light));
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 4px 12px rgba(79, 110, 247, 0.3);
}

.page-header h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: var(--gray-800);
  line-height: 1.3;
}

.header-subtitle {
  margin: 2px 0 0 0;
  font-size: 13px;
  color: var(--gray-400);
}

.save-btn {
  height: 40px;
  padding: 0 28px;
  border-radius: var(--radius-sm);
  font-weight: 500;
  transition: var(--transition);
}

.save-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 110, 247, 0.35);
}

/* 配置卡片网格 */
.config-grid {
  margin-top: 8px;
}

.config-card {
  background: #fff;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg);
  padding: 24px;
  margin-bottom: 24px;
  transition: var(--transition);
  box-shadow: var(--shadow-sm);
}

.config-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
  border-color: var(--primary-light);
}

/* 卡片头部 */
.card-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--gray-100);
}

.card-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.card-icon.doc {
  background: linear-gradient(135deg, #22c55e, #4ade80);
}

.card-icon.chat {
  background: linear-gradient(135deg, #8b5cf6, #a78bfa);
}

.card-icon.search {
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
}

.card-icon.llm {
  background: linear-gradient(135deg, #ef4444, #f87171);
}

.card-title h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--gray-800);
}

.card-title p {
  margin: 2px 0 0 0;
  font-size: 12px;
  color: var(--gray-400);
}

/* 表单样式 */
.config-form :deep(.el-form-item) {
  margin-bottom: 20px;
}

.config-form :deep(.el-form-item__label) {
  font-weight: 500;
  color: var(--gray-700);
  font-size: 13px;
  margin-bottom: 8px;
}

.config-form :deep(.el-input-number) {
  width: 100%;
}

.config-form :deep(.el-input-number .el-input__wrapper) {
  border-radius: var(--radius-sm);
  box-shadow: 0 0 0 1px var(--gray-200) inset;
  transition: var(--transition);
}

.config-form :deep(.el-input-number .el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--primary-light) inset;
}

.config-form :deep(.el-input-number .el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--primary) inset;
}

/* 带单位的输入框 */
.input-with-unit {
  display: flex;
  align-items: center;
  gap: 10px;
}

.input-with-unit .el-input-number {
  flex: 1;
}

.unit {
  font-size: 13px;
  color: var(--gray-500);
  font-weight: 500;
  white-space: nowrap;
}

/* 滑块样式 */
.slider-with-value {
  display: flex;
  align-items: center;
  gap: 16px;
}

.slider-with-value .el-slider {
  flex: 1;
}

.slider-value {
  min-width: 36px;
  padding: 4px 10px;
  background: var(--primary-bg);
  color: var(--primary);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
  text-align: center;
}

.config-form :deep(.el-slider__runway) {
  height: 6px;
  border-radius: 3px;
}

.config-form :deep(.el-slider__bar) {
  height: 6px;
  border-radius: 3px;
  background: linear-gradient(90deg, var(--primary), var(--primary-light));
}

.config-form :deep(.el-slider__button) {
  width: 16px;
  height: 16px;
  border: 2px solid var(--primary);
  box-shadow: 0 2px 6px rgba(79, 110, 247, 0.3);
}

/* 动画 */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-12px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes slideInLeft {
  from { opacity: 0; transform: translateX(-20px); }
  to { opacity: 1; transform: translateX(0); }
}

@keyframes slideInRight {
  from { opacity: 0; transform: translateX(20px); }
  to { opacity: 1; transform: translateX(0); }
}

.slide-in-left {
  animation: slideInLeft 0.5s ease-out;
}

.slide-in-right {
  animation: slideInRight 0.5s ease-out;
}

/* 响应式 */
@media (max-width: 1200px) {
  .config-grid :deep(.el-col-12) {
    width: 100%;
  }
}

/* 主题卡片 */
.theme-card {
  animation: slideDown 0.4s ease-out;
}

.card-icon.theme {
  background: linear-gradient(135deg, var(--primary), var(--primary-light));
}

.theme-selector {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}

.theme-option {
  position: relative;
  padding: 16px;
  border: 2px solid var(--gray-200);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: var(--transition);
  background: #fff;
}

.theme-option:hover {
  border-color: var(--primary-light);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.theme-option.active {
  border-color: var(--primary);
  background: var(--primary-bg);
}

.theme-preview {
  display: flex;
  gap: 6px;
  margin-bottom: 12px;
}

.theme-color {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.theme-color.light {
  width: 20px;
  height: 20px;
  align-self: center;
}

.theme-color.bg {
  width: 20px;
  height: 20px;
  align-self: center;
  border: 1px solid var(--gray-200);
}

.theme-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.theme-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-800);
}

.theme-hex {
  font-size: 12px;
  color: var(--gray-500);
  font-family: var(--font-mono);
}

.theme-check {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  animation: scaleIn 0.3s ease-out;
}

@keyframes scaleIn {
  from {
    transform: scale(0);
  }
  to {
    transform: scale(1);
  }
}

@media (max-width: 768px) {
  .theme-selector {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 12px;
  }
  
  .theme-option {
    padding: 12px;
  }
}
</style>
