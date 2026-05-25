<script setup>
import { ref } from 'vue'

const props = defineProps({
  groups: Array,
  currentId: Number,
})
const emit = defineEmits(['select', 'create'])

const showCreate = ref(false)
const name = ref('')
const desc = ref('')

async function submitCreate() {
  if (!name.value.trim()) return
  emit('create', { name: name.value.trim(), description: desc.value || null })
  showCreate.value = false
  name.value = ''
  desc.value = ''
}
</script>

<template>
  <div class="group-selector">
    <select :value="currentId" @change="emit('select', Number($event.target.value))">
      <option v-for="g in groups" :key="g.id" :value="g.id">{{ g.name }}</option>
    </select>
    <button class="btn-icon" @click="showCreate = true">+</button>
  </div>

  <div v-if="showCreate" class="sheet-overlay" @click="showCreate = false" />
  <div v-if="showCreate" class="sheet">
    <h3>Новая группа</h3>
    <input v-model="name" class="input" placeholder="Название" />
    <input v-model="desc" class="input" placeholder="Описание (необязательно)" />
    <button class="btn-primary" @click="submitCreate">Создать</button>
  </div>
</template>

<style scoped>
.group-selector {
  display: flex;
  gap: 8px;
  align-items: center;
}
select {
  flex: 1;
  padding: 10px;
  border-radius: var(--radius);
  background: var(--tg-bg);
  color: var(--tg-text);
  border: 1px solid rgba(128,128,128,0.25);
}
.btn-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius);
  background: var(--tg-button);
  color: var(--tg-button-text);
  font-size: 22px;
}
</style>
