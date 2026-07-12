<template>
  <div v-html="renderedContent" class="markdown-content" />
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'

const props = defineProps({
  content: {
    type: String,
    required: true,
  },
})

marked.setOptions({
  breaks: true,
})

const renderer = new marked.Renderer()

renderer.code = function ({ text, lang }) {
  const language = lang && hljs.getLanguage(lang) ? lang : 'plaintext'
  const highlighted = hljs.highlight(text, { language }).value
  return `<pre><code class="hljs language-${language}">${highlighted}</code></pre>`
}

marked.use({ renderer })

const renderedContent = computed(() => {
  return marked(props.content)
})
</script>

<style scoped>
.markdown-content {
  font-size: 14px;
  line-height: 1.8;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3,
.markdown-content h4,
.markdown-content h5,
.markdown-content h6 {
  font-weight: 600;
  margin-top: 16px;
  margin-bottom: 8px;
  color: #1f2937;
}

.markdown-content h1 {
  font-size: 24px;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 8px;
}

.markdown-content h2 {
  font-size: 20px;
}

.markdown-content h3 {
  font-size: 18px;
}

.markdown-content p {
  margin-bottom: 8px;
}

.markdown-content ul,
.markdown-content ol {
  padding-left: 24px;
  margin-bottom: 8px;
}

.markdown-content li {
  margin-bottom: 4px;
}

.markdown-content blockquote {
  border-left: 4px solid #3b82f6;
  padding-left: 12px;
  margin: 8px 0;
  color: #6b7280;
  background: #f3f4f6;
  padding: 8px 12px;
  border-radius: 0 8px 8px 0;
}

.markdown-content code {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', monospace;
  font-size: 13px;
}

.markdown-content pre {
  background: #1f2937;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}

.markdown-content pre code {
  background: none;
  padding: 0;
  color: #fff;
}

.markdown-content table {
  width: 100%;
  border-collapse: collapse;
  margin: 8px 0;
}

.markdown-content th,
.markdown-content td {
  border: 1px solid #e5e7eb;
  padding: 8px 12px;
  text-align: left;
}

.markdown-content th {
  background: #f3f4f6;
  font-weight: 600;
}

.markdown-content a {
  color: #3b82f6;
  text-decoration: none;
}

.markdown-content a:hover {
  text-decoration: underline;
}

.markdown-content hr {
  border: none;
  border-top: 1px solid #e5e7eb;
  margin: 16px 0;
}

.markdown-content img {
  max-width: 100%;
  border-radius: 8px;
}
</style>
