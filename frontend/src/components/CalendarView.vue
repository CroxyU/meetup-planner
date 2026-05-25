<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { api } from '../api'
import DayDetailSheet from './DayDetailSheet.vue'

const props = defineProps({
  groupId: Number,
  userColor: String,
})
const emit = defineEmits(['propose-days'])

const year = ref(new Date().getFullYear())
const month = ref(new Date().getMonth() + 1)
const loading = ref(false)
const days = ref([])
const onlyMe = ref(false)

// Режимы: null | 'brush-free' | 'brush-busy' | 'pick-dates'
const brushMode = ref(null)
const pickDates = ref([])

const dayDetail = ref(null)
const showDetail = ref(false)

const monthLabel = computed(() => {
  const d = new Date(year.value, month.value - 1, 1)
  return d.toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' })
})

const weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

// Свайп
let touchStartX = 0

async function loadCalendar() {
  if (!props.groupId) return
  loading.value = true
  try {
    const data = await api.getCalendar(props.groupId, year.value, month.value, onlyMe.value)
    days.value = data.days
  } finally {
    loading.value = false
  }
}

function goMonth(delta) {
  let m = month.value + delta
  let y = year.value
  if (m > 12) { m = 1; y++ }
  if (m < 1) { m = 12; y-- }
  month.value = m
  year.value = y
}

function goToday() {
  const t = new Date()
  year.value = t.getFullYear()
  month.value = t.getMonth() + 1
}

/** Трёхпозиционный тогл: null → free → busy → null */
function nextStatus(current) {
  if (current === 'free') return 'busy'
  if (current === 'busy') return null
  return 'free'
}

async function toggleDay(dayStr, currentStatus) {
  const next = nextStatus(currentStatus)
  await api.setAvailability(props.groupId, [dayStr], next)
  await loadCalendar()
}

async function applyBrush(dayStr) {
  const status = brushMode.value === 'brush-busy' ? 'busy' : 'free'
  await api.setAvailability(props.groupId, [dayStr], status)
  await loadCalendar()
}

function onDayTap(cell) {
  if (!cell.is_current_month) return
  const dayStr = cell.day

  if (brushMode.value === 'brush-free' || brushMode.value === 'brush-busy') {
    applyBrush(dayStr)
    return
  }

  if (brushMode.value === 'pick-dates') {
    const i = pickDates.value.indexOf(dayStr)
    if (i >= 0) pickDates.value.splice(i, 1)
    else pickDates.value.push(dayStr)
    return
  }

  toggleDay(dayStr, cell.my_status)
}

async function openDetail(cell) {
  dayDetail.value = await api.getDay(props.groupId, cell.day)
  showDetail.value = true
}

let longPressTimer = null
let detailOpened = false
function onTouchStart(cell, e) {
  detailOpened = false
  touchStartX = e.touches?.[0]?.clientX ?? 0
  longPressTimer = setTimeout(async () => {
    detailOpened = true
    await openDetail(cell)
  }, 500)
}
function onTouchEnd(cell, e) {
  clearTimeout(longPressTimer)
  const dx = (e.changedTouches?.[0]?.clientX ?? 0) - touchStartX
  if (Math.abs(dx) > 60) {
    goMonth(dx < 0 ? 1 : -1)
    return
  }
  if (!detailOpened) onDayTap(cell)
}

function setBrush(mode) {
  brushMode.value = brushMode.value === mode ? null : mode
  if (mode !== 'pick-dates') pickDates.value = []
}

function submitPickDates() {
  if (pickDates.value.length) emit('propose-days', [...pickDates.value])
  brushMode.value = null
  pickDates.value = []
}

watch([() => props.groupId, year, month, onlyMe], loadCalendar, { immediate: true })
onMounted(loadCalendar)

defineExpose({ loadCalendar, goToday })
</script>

<template>
  <div class="calendar-view" @touchstart.passive @touchend.passive>
    <div class="cal-toolbar">
      <button @click="goMonth(-1)">‹</button>
      <div class="month-block">
        <span class="month-label">{{ monthLabel }}</span>
        <button class="today-btn" @click="goToday">Сегодня</button>
      </div>
      <button @click="goMonth(1)">›</button>
    </div>

    <div class="view-toggle">
      <button :class="{ active: !onlyMe }" @click="onlyMe = false">Все</button>
      <button :class="{ active: onlyMe }" @click="onlyMe = true">Только я</button>
    </div>

    <div class="quick-bar">
      <button :class="{ active: brushMode === 'brush-free' }" @click="setBrush('brush-free')">🖌 Свободен</button>
      <button :class="{ active: brushMode === 'brush-busy' }" @click="setBrush('brush-busy')">🖌 Занят</button>
      <button :class="{ active: brushMode === 'pick-dates' }" @click="setBrush('pick-dates')">📌 Даты</button>
    </div>

    <div v-if="loading" class="skeleton-grid">
      <div v-for="i in 35" :key="i" class="skeleton skeleton-cell" />
    </div>

    <div v-else class="cal-grid">
      <div v-for="w in weekdays" :key="w" class="wd">{{ w }}</div>
      <div
        v-for="cell in days"
        :key="cell.day"
        class="day-cell"
        :class="{
          other: !cell.is_current_month,
          today: cell.is_today,
          allFree: cell.all_free && !onlyMe,
          free: cell.my_status === 'free',
          busy: cell.my_status === 'busy',
          picked: pickDates.includes(cell.day),
        }"
        :style="cell.my_status === 'free' && userColor ? { '--my-color': userColor } : {}"
        @touchstart="onTouchStart(cell, $event)"
        @touchend="onTouchEnd(cell, $event)"
        @contextmenu.prevent
      >
        <span class="num">{{ new Date(cell.day + 'T12:00:00').getDate() }}</span>
        <div v-if="!onlyMe && cell.members?.length" class="dots">
          <span
            v-for="m in cell.members.filter(x => x.status)"
            :key="m.user_id"
            class="dot"
            :class="{ busy: m.status === 'busy' }"
            :style="m.status === 'free' ? { background: m.color } : {}"
          />
        </div>
        <span v-if="cell.all_free && !onlyMe" class="all-icon">✓</span>
        <span v-if="cell.my_status === 'busy'" class="cross">✕</span>
      </div>
    </div>

    <button
      v-if="brushMode === 'pick-dates' && pickDates.length"
      class="btn-primary floating"
      @click="submitPickDates"
    >
      Предложить ({{ pickDates.length }})
    </button>

    <DayDetailSheet
      v-if="showDetail"
      :detail="dayDetail"
      :user-color="userColor"
      @close="showDetail = false"
      @propose="emit('propose-days', [dayDetail.day]); showDetail = false"
    />
  </div>
</template>

<style scoped>
.cal-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
}
.cal-toolbar button {
  font-size: 28px;
  padding: 4px 12px;
  color: var(--tg-link);
}
.month-block { text-align: center; }
.month-label { font-weight: 600; text-transform: capitalize; display: block; }
.today-btn {
  font-size: 12px;
  color: var(--tg-link);
  margin-top: 4px;
}
.view-toggle, .quick-bar {
  display: flex;
  gap: 8px;
  padding: 0 12px 8px;
  flex-wrap: wrap;
}
.view-toggle button, .quick-bar button {
  flex: 1;
  min-width: 0;
  padding: 8px;
  border-radius: 20px;
  background: var(--tg-secondary-bg);
  font-size: 12px;
}
.view-toggle button.active, .quick-bar button.active {
  background: var(--tg-button);
  color: var(--tg-button-text);
}
.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  padding: 0 8px 16px;
}
.wd {
  text-align: center;
  font-size: 11px;
  color: var(--tg-hint);
  padding: 4px 0;
}
.day-cell {
  position: relative;
  min-height: var(--cell-size);
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  padding-top: 6px;
  transition: background 0.15s, transform 0.1s;
}
.day-cell.other { opacity: 0.35; }
.day-cell.today {
  box-shadow: 0 0 0 2px var(--tg-link);
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 2px var(--tg-link); }
  50% { box-shadow: 0 0 0 3px var(--tg-link); }
}
.day-cell.allFree {
  background: var(--accent-gold);
  box-shadow: inset 0 0 0 2px var(--accent-all-free);
}
.day-cell.free {
  background: color-mix(in srgb, var(--my-color, #6C9BCF) 45%, transparent);
}
.day-cell.busy {
  background: rgba(158, 158, 158, 0.35);
}
.day-cell.picked {
  outline: 2px dashed var(--tg-link);
}
.num { font-size: 15px; font-weight: 500; }
.dots {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  justify-content: center;
  max-width: 36px;
  margin-top: 2px;
}
.dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
}
.dot.busy { background: #9e9e9e; }
.cross { font-size: 10px; color: #666; position: absolute; bottom: 4px; }
.all-icon { font-size: 9px; position: absolute; top: 2px; right: 4px; color: var(--accent-all-free); }
.floating {
  position: fixed;
  bottom: 72px;
  left: 16px;
  right: 16px;
  z-index: 50;
}
</style>
