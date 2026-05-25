<script setup>
import { onMounted, ref, watch } from 'vue'
import { api } from '../api'

const props = defineProps({ groupId: Number, isOwner: Boolean })
const members = ref([])
const invite = ref(null)

async function load() {
  if (!props.groupId) return
  members.value = await api.getMembers(props.groupId)
  invite.value = await api.getInvite(props.groupId)
}

async function remove(memberId) {
  if (!confirm('Удалить участника?')) return
  await api.removeMember(props.groupId, memberId)
  await load()
}

function copyInvite() {
  if (!invite.value) return
  const link = `https://t.me/${window.location.hostname}?start=group_${invite.value.invite_code}`
  const text = `Присоединяйся! Код: ${invite.value.invite_code}\n/start group_${invite.value.invite_code}`
  navigator.clipboard?.writeText(text)
  window.Telegram?.WebApp?.showAlert?.('Код скопирован. Отправьте друзьям команду /start group_' + invite.value.invite_code)
}

watch(() => props.groupId, load, { immediate: true })
onMounted(load)
</script>

<template>
  <div class="members">
    <h2>Участники</h2>
    <button v-if="invite" class="btn-primary" style="margin-bottom:16px" @click="copyInvite">
      📋 Скопировать приглашение
    </button>
    <p v-if="invite" class="hint">Код: <code>{{ invite.invite_code }}</code></p>
    <div v-for="m in members" :key="m.id" class="row">
      <span class="color-dot" :style="{ background: m.color || '#ccc', width:14, height:14 }" />
      <span class="name">{{ m.first_name }}{{ m.is_owner ? ' 👑' : '' }}</span>
      <button v-if="isOwner && !m.is_owner" class="remove" @click="remove(m.id)">✕</button>
    </div>
  </div>
</template>

<style scoped>
.members { padding: 16px; }
.row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(128,128,128,0.15);
}
.name { flex: 1; }
.remove { color: #e53935; font-size: 18px; }
.hint { font-size: 13px; color: var(--tg-hint); }
code { background: var(--tg-secondary-bg); padding: 2px 6px; border-radius: 4px; }
</style>
