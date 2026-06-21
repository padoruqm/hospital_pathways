<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { chatWithAI, chatWithRAG } from '@/api/client'
import type { ChatMessage } from '@/types'

// 2 chế độ AI cho cùng khung chat:
//  - 'system': nhồi toàn bộ khoa vào prompt (đơn giản)
//  - 'rag'   : truy hồi vài khoa liên quan từ tài liệu rồi mới hỏi LLM (kèm nguồn)
const mode = ref<'system' | 'rag'>('rag')

// Hội thoại được giữ ngay trong component (frontend), gửi kèm mỗi lần hỏi để chatbot
// trả lời có ngữ cảnh. Đơn giản, không cần lưu server.
const messages = ref<ChatMessage[]>([
  {
    role: 'assistant',
    text: 'Chào bạn 👋 Mình là trợ lý bệnh viện. Bạn mô tả triệu chứng hoặc nhu cầu, mình sẽ gợi ý khoa khám phù hợp kèm tầng, phòng và giờ làm việc nhé.',
  },
])
const input = ref('')
const sending = ref(false)
const error = ref('')

const suggestions = ['Tôi bị đau ngực, khó thở', 'Khám thai ở đâu?', 'Con tôi bị sốt cao', 'Tôi đau đầu nhiều ngày']

const listEl = ref<HTMLElement | null>(null)
async function scrollToEnd() {
  await nextTick()
  listEl.value?.scrollTo({ top: listEl.value.scrollHeight, behavior: 'smooth' })
}

async function send(text: string) {
  const content = text.trim()
  if (!content || sending.value) return
  error.value = ''
  messages.value.push({ role: 'user', text: content })
  input.value = ''
  await scrollToEnd()

  sending.value = true
  // Lịch sử gửi lên là toàn bộ hội thoại TRƯỚC câu hỏi hiện tại.
  const history = messages.value.slice(0, -1)
  try {
    const res = mode.value === 'rag'
      ? await chatWithRAG(content, history)
      : await chatWithAI(content, history)
    messages.value.push({ role: 'assistant', text: res.reply, sources: res.sources })
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    sending.value = false
    await scrollToEnd()
  }
}
</script>

<template>
  <section class="chat">
    <header class="chat-head">
      <h1>Trợ lý AI</h1>
      <p>Hỏi đáp bằng tiếng Việt — gợi ý khoa khám từ triệu chứng của bạn.</p>
      <div class="mode" role="group" aria-label="Chế độ AI">
        <button :class="{ on: mode === 'rag' }" @click="mode = 'rag'">RAG (tra tài liệu)</button>
        <button :class="{ on: mode === 'system' }" @click="mode = 'system'">Hỏi nhanh</button>
      </div>
    </header>

    <div ref="listEl" class="messages">
      <div v-for="(m, i) in messages" :key="i" class="msg" :class="m.role">
        <div class="bubble">
          {{ m.text }}
          <div v-if="m.sources && m.sources.length" class="sources">
            📚 Nguồn: {{ m.sources.join(' · ') }}
          </div>
        </div>
      </div>
      <div v-if="sending" class="msg assistant">
        <div class="bubble typing"><span></span><span></span><span></span></div>
      </div>
      <p v-if="error" class="state error">⚠️ {{ error }}</p>
    </div>

    <div v-if="messages.length <= 1" class="suggestions">
      <button v-for="s in suggestions" :key="s" class="chip" @click="send(s)">{{ s }}</button>
    </div>

    <form class="composer" @submit.prevent="send(input)">
      <input
        v-model="input"
        type="text"
        placeholder="Nhập triệu chứng hoặc câu hỏi…"
        aria-label="Tin nhắn"
        :disabled="sending"
      />
      <button type="submit" class="send" :disabled="sending || !input.trim()">Gửi</button>
    </form>
  </section>
</template>

<style scoped>
.chat {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 150px);
}
.chat-head h1 {
  font-size: 1.3rem;
  margin: 0 0 2px;
}
.chat-head p {
  color: var(--color-muted);
  font-size: 0.9rem;
  margin: 0 0 10px;
}
.mode {
  display: inline-flex;
  gap: 4px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 999px;
  padding: 3px;
  margin-bottom: 12px;
}
.mode button {
  border: none;
  background: transparent;
  color: var(--color-muted);
  font-size: 0.82rem;
  padding: 6px 12px;
  border-radius: 999px;
}
.mode button.on {
  background: var(--color-primary);
  color: #fff;
  font-weight: 600;
}
.sources {
  margin-top: 8px;
  padding-top: 6px;
  border-top: 1px dashed var(--color-border);
  font-size: 0.78rem;
  color: var(--color-muted);
}
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 4px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.msg {
  display: flex;
}
.msg.user {
  justify-content: flex-end;
}
.bubble {
  max-width: 82%;
  padding: 10px 14px;
  border-radius: 14px;
  font-size: 0.95rem;
  line-height: 1.45;
  white-space: pre-wrap;
  word-break: break-word;
}
.msg.assistant .bubble {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-bottom-left-radius: 4px;
}
.msg.user .bubble {
  background: var(--color-primary);
  color: #fff;
  border-bottom-right-radius: 4px;
}
.typing {
  display: flex;
  gap: 4px;
}
.typing span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-muted);
  animation: blink 1.2s infinite both;
}
.typing span:nth-child(2) {
  animation-delay: 0.2s;
}
.typing span:nth-child(3) {
  animation-delay: 0.4s;
}
@keyframes blink {
  0%, 80%, 100% {
    opacity: 0.3;
  }
  40% {
    opacity: 1;
  }
}
.suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px 0;
}
.chip {
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-primary-dark);
  border-radius: 999px;
  padding: 7px 12px;
  font-size: 0.85rem;
}
.composer {
  display: flex;
  gap: 8px;
  padding-top: 10px;
  border-top: 1px solid var(--color-border);
}
.composer input {
  flex: 1;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  padding: 12px 16px;
  font-size: 1rem;
  font-family: inherit;
  outline: none;
}
.composer input:focus {
  border-color: var(--color-primary);
}
.send {
  border: none;
  background: var(--color-primary);
  color: #fff;
  border-radius: 999px;
  padding: 0 20px;
  font-weight: 600;
}
.send:disabled {
  opacity: 0.5;
}
</style>
