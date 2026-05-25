<script setup>
import { onMounted, ref, watch } from 'vue'
import { api } from '../api'

const props = defineProps({ groupId: Number })
const proposals = ref([])
const loading = ref(false)

async function load() {
  if (!props.groupId) return
  loading.value = true
  try {
    proposals.value = await api.listProposals(props.groupId)
  } finally {
    loading.value = false
  }
}

async function vote(id, status) {
  await api.voteProposal(id, status)
  await load()
}

watch(() => props.groupId, load, { immediate: true })
onMounted(load)
defineExpose({ load })
</script>

<template>
  <div class="proposals">
    <h2>Предложения</h2>
    <div v-if="loading" class="skeleton" style="height:80px;margin:12px" />
    <p v-else-if="!proposals.length" class="empty">Пока нет предложений встреч</p>
    <article v-for="p in proposals" :key="p.id" class="card">
      <h3>{{ p.title }}</h3>
      <p class="meta">{{ p.proposer_name }} · {{ p.days.join(', ') }}</p>
      <p v-if="p.description" class="desc">{{ p.description }}</p>
      <div class="votes">
        <div v-for="v in p.votes" :key="v.user_id" class="chip">
          <span class="color-dot" :style="{ background: v.color || '#ccc' }" />
          {{ v.first_name }}:
          <span v-if="v.status === 'free'">✅</span>
          <span v-else-if="v.status === 'busy'">❌</span>
          <span v-else>—</span>
        </div>
      </div>
      <div class="actions">
        <button class="btn-secondary" @click="vote(p.id, 'free')">Свободен</button>
        <button class="btn-secondary" @click="vote(p.id, 'busy')">Занят</button>
      </div>
    </article>
  </div>
</template>

<style scoped>
.proposals { padding: 16px; }
.empty { color: var(--tg-hint); text-align: center; margin-top: 40px; }
.card {
  background: var(--tg-secondary-bg);
  border-radius: var(--radius);
  padding: 14px;
  margin-bottom: 12px;
}
.meta { font-size: 13px; color: var(--tg-hint); }
.actions { display: flex; gap: 8px; margin-top: 12px; }
.actions button { flex: 1; }
</style>
