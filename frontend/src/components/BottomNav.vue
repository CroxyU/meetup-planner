<script setup>
defineProps({
  tab: { type: String, required: true },
})
const emit = defineEmits(['change'])
const items = [
  { id: 'calendar', icon: '📅', label: 'Календарь' },
  { id: 'proposals', icon: '💡', label: 'Предложения' },
  { id: 'members', icon: '👥', label: 'Участники' },
  { id: 'settings', icon: '⚙️', label: 'Настройки' },
]
</script>

<template>
  <nav class="bottom-nav">
    <button
      v-for="item in items"
      :key="item.id"
      class="nav-item"
      :class="{ active: tab === item.id }"
      @click="emit('change', item.id)"
    >
      <span class="icon">{{ item.icon }}</span>
      <span>{{ item.label }}</span>
    </button>
  </nav>
</template>
