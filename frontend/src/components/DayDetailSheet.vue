<script setup>
import { computed } from 'vue'

const props = defineProps({
  detail: Object,
  userColor: String,
})
const emit = defineEmits(['close', 'propose'])

const dateLabel = computed(() => {
  if (!props.detail) return ''
  const d = new Date(props.detail.day + 'T12:00:00')
  return d.toLocaleDateString('ru-RU', { weekday: 'long', day: 'numeric', month: 'long' })
})
</script>

<template>
  <div class="sheet-overlay" @click="emit('close')" />
  <div class="sheet" @click.stop>
    <div class="sheet-head">
      <h3>{{ dateLabel }}</h3>
      <button @click="emit('close')">✕</button>
    </div>
    <p v-if="detail?.all_free" class="all-free-badge">✓ Все свободны!</p>

    <section>
      <h4>Свободны</h4>
      <div v-if="!detail?.free?.length" class="empty">—</div>
      <div v-for="m in detail?.free" :key="m.user_id" class="chip">
        <span class="color-dot" :style="{ background: m.color || '#999' }" />
        {{ m.first_name }}
      </div>
    </section>
    <section>
      <h4>Заняты</h4>
      <div v-if="!detail?.busy?.length" class="empty">—</div>
      <div v-for="m in detail?.busy" :key="m.user_id" class="chip">
        <span class="color-dot" style="background:#9e9e9e" />
        {{ m.first_name }}
      </div>
    </section>
    <section>
      <h4>Не отметились</h4>
      <div v-if="!detail?.unmarked?.length" class="empty">—</div>
      <div v-for="m in detail?.unmarked" :key="m.user_id" class="chip">
        <span class="color-dot" :style="{ background: m.color || '#ccc' }" />
        {{ m.first_name }}
      </div>
    </section>

    <button class="btn-primary" style="margin-top:16px" @click="emit('propose')">
      Предложить встречу
    </button>
  </div>
</template>

<style scoped>
.sheet-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
section { margin-top: 16px; }
h4 { margin: 0 0 8px; font-size: 13px; color: var(--tg-hint); }
.chip { margin: 4px 4px 4px 0; }
.empty { color: var(--tg-hint); font-size: 13px; }
.all-free-badge {
  background: var(--accent-gold);
  padding: 8px 12px;
  border-radius: var(--radius);
  text-align: center;
  font-weight: 600;
}
</style>
