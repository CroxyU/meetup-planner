<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const emit = defineEmits(['done'])
const colors = ref([])
const selected = ref(null)
const saving = ref(false)

onMounted(async () => {
  const data = await api.getPalette()
  colors.value = data.colors
})

async function save() {
  if (!selected.value) return
  saving.value = true
  try {
    await api.setColor(selected.value)
    emit('done')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="color-picker">
    <h2>Выберите ваш цвет</h2>
    <p class="hint">Он будет отображаться на общем календаре группы</p>
    <div class="palette">
      <button
        v-for="c in colors"
        :key="c"
        class="swatch"
        :class="{ active: selected === c }"
        :style="{ background: c }"
        @click="selected = c"
      />
    </div>
    <button class="btn-primary" :disabled="!selected || saving" @click="save">
      Продолжить
    </button>
  </div>
</template>

<style scoped>
.color-picker {
  padding: 24px 16px;
  text-align: center;
}
.hint {
  color: var(--tg-hint);
  font-size: 14px;
  margin-bottom: 24px;
}
.palette {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}
.swatch {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  margin: 0 auto;
  border: 3px solid transparent;
  transition: transform 0.15s, border-color 0.15s;
}
.swatch.active {
  border-color: var(--tg-text);
  transform: scale(1.1);
}
</style>
