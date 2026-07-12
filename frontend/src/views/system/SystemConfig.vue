<template>
  <div class="system-config">
    <div class="page-header">
      <h2>系统配置</h2>
      <el-button type="primary" icon="Save" @click="saveConfig">保存配置</el-button>
    </div>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card title="文档解析配置">
          <el-form :model="config.document">
            <el-form-item label="上传大小限制(MB)">
              <el-input-number v-model="config.document.max_upload_size" :min="1" :max="500" />
            </el-form-item>
            <el-form-item label="文本切片大小">
              <el-input-number v-model="config.document.chunk_size" :min="100" :max="2000" />
            </el-form-item>
            <el-form-item label="切片重叠大小">
              <el-input-number v-model="config.document.chunk_overlap" :min="0" :max="500" />
            </el-form-item>
          </el-form>
        </el-card>

        <el-card title="检索配置">
          <el-form :model="config.retrieval">
            <el-form-item label="默认 Top K">
              <el-input-number v-model="config.retrieval.top_k" :min="1" :max="20" />
            </el-form-item>
            <el-form-item label="相似度阈值">
              <el-slider v-model="config.retrieval.similarity_threshold" :min="0" :max="1" :step="0.1" />
              <span class="slider-value">{{ config.retrieval.similarity_threshold }}</span>
            </el-form-item>
            <el-form-item label="检索超时(秒)">
              <el-input-number v-model="config.retrieval.timeout" :min="5" :max="120" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card title="对话配置">
          <el-form :model="config.chat">
            <el-form-item label="最大上下文轮数">
              <el-input-number v-model="config.chat.max_context_rounds" :min="1" :max="50" />
            </el-form-item>
            <el-form-item label="最大回答长度">
              <el-input-number v-model="config.chat.max_answer_length" :min="100" :max="5000" />
            </el-form-item>
            <el-form-item label="回答超时(秒)">
              <el-input-number v-model="config.chat.timeout" :min="10" :max="120" />
            </el-form-item>
          </el-form>
        </el-card>

        <el-card title="LLM配置">
          <el-form :model="config.llm">
            <el-form-item label="模型温度">
              <el-slider v-model="config.llm.temperature" :min="0" :max="1" :step="0.1" />
              <span class="slider-value">{{ config.llm.temperature }}</span>
            </el-form-item>
            <el-form-item label="最大Token数">
              <el-input-number v-model="config.llm.max_tokens" :min="512" :max="8192" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

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
  try {
    await request.post('/system/config/', config)
    ElMessage.success('配置保存成功')
  } catch (error) {
    ElMessage.error('配置保存失败')
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.system-config {
  padding: 20px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
}

.slider-value {
  margin-left: 12px;
  color: #6b7280;
}
</style>
