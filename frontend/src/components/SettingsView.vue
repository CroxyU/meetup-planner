<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const props = defineProps({ user: Object })
const emit = defineEmits(['color-changed'])
const colors = ref([])
const selected = ref(props.user?.color)

onMounted(async () => {
  const data = await api.getPalette()
  colors.value = data.colors
})

async function saveColor(c) {
  selected.value = c
  await api.setColor(c)
  emit('color-changed')
}
</script>

<template>
  <div class="settings">
    <h2>Настройки</h2>
    <p>Привет, <b>{{ user?.first_name }}</b></p>
    <h3>Ваш цвет</h3>
    <div class="palette">
      <button
        v-for="c in colors"
        :key="c"
        class="swatch"
        :class="{ active: selected === c }"
        :style="{ background: c }"
        @click="saveColor(c)"
      />
    </div>
  </div>
</template>

<style scoped>
.settings { padding: 16px; }
.palette {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-top: 12px;
}
.swatch {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  margin: 0 auto;
  border: 2px solid transparent;
}
.swatch.active { border-color: var(--tg-text); }
</style>
