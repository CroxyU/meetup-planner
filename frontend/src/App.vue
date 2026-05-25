<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from './api'
import { useTelegram } from './composables/useTelegram'
import BottomNav from './components/BottomNav.vue'
import CalendarView from './components/CalendarView.vue'
import ColorPicker from './components/ColorPicker.vue'
import GroupSelector from './components/GroupSelector.vue'
import MembersView from './components/MembersView.vue'
import ProposalsView from './components/ProposalsView.vue'
import SettingsView from './components/SettingsView.vue'

const { haptic } = useTelegram()

const user = ref(null)
const groups = ref([])
const currentGroupId = ref(null)
const tab = ref('calendar')
const loading = ref(true)
const error = ref(null)

const showProposalForm = ref(false)
const proposalDays = ref([])
const proposalTitle = ref('')
const proposalDesc = ref('')
const proposalPlace = ref('')

const currentGroup = computed(() => groups.value.find((g) => g.id === currentGroupId.value))

const calendarRef = ref(null)
const proposalsRef = ref(null)

async function init() {
  loading.value = true
  error.value = null
  try {
    user.value = await api.getMe()
    groups.value = await api.listGroups()

    // Deep link: ?group=ID или start_param из URL
    const params = new URLSearchParams(window.location.search)
    const joinCode = params.get('join')
    if (joinCode) {
      const g = await api.joinGroup(joinCode)
      groups.value = await api.listGroups()
      currentGroupId.value = g.id
    } else if (groups.value.length) {
      currentGroupId.value = groups.value[0].id
    }

    const groupParam = params.get('group')
    if (groupParam) currentGroupId.value = Number(groupParam)
    if (params.get('tab') === 'proposals') tab.value = 'proposals'
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function onColorDone() {
  user.value = await api.getMe()
}

async function refreshUser() {
  user.value = await api.getMe()
}

async function onCreateGroup(data) {
  const g = await api.createGroup(data)
  groups.value = await api.listGroups()
  currentGroupId.value = g.id
  haptic('medium')
}

function onProposeDays(days) {
  proposalDays.value = days
  proposalTitle.value = ''
  proposalDesc.value = ''
  proposalPlace.value = ''
  showProposalForm.value = true
}

async function submitProposal() {
  if (!proposalTitle.value.trim() || !proposalDays.value.length) return
  await api.createProposal(currentGroupId.value, {
    title: proposalTitle.value.trim(),
    description: proposalDesc.value || null,
    place: proposalPlace.value || null,
    days: proposalDays.value,
  })
  showProposalForm.value = false
  tab.value = 'proposals'
  proposalsRef.value?.load?.()
  haptic('medium')
}

onMounted(init)
</script>

<template>
  <div v-if="loading" class="app-shell center">
    <p>Загрузка…</p>
  </div>

  <div v-else-if="error" class="app-shell center">
    <p>{{ error }}</p>
    <p class="hint">Откройте приложение из Telegram-бота</p>
  </div>

  <ColorPicker v-else-if="user?.needs_color" @done="onColorDone" />

  <div v-else class="app-shell">
    <header class="app-header">
      <GroupSelector
        :groups="groups"
        :current-id="currentGroupId"
        @select="currentGroupId = $event"
        @create="onCreateGroup"
      />
      <p v-if="!groups.length" class="hint">Создайте первую группу кнопкой +</p>
    </header>

    <main class="app-content">
      <CalendarView
        v-show="tab === 'calendar' && currentGroupId"
        ref="calendarRef"
        :group-id="currentGroupId"
        :user-color="user?.color"
        @propose-days="onProposeDays"
      />
      <ProposalsView
        v-show="tab === 'proposals' && currentGroupId"
        ref="proposalsRef"
        :group-id="currentGroupId"
      />
      <MembersView
        v-show="tab === 'members' && currentGroupId"
        :group-id="currentGroupId"
        :is-owner="currentGroup?.is_owner"
      />
      <SettingsView
        v-show="tab === 'settings'"
        :user="user"
        @color-changed="refreshUser"
      />
      <div v-if="!currentGroupId && tab !== 'settings'" class="center hint-block">
        Выберите или создайте группу
      </div>
    </main>

    <BottomNav :tab="tab" @change="tab = $event" />

    <div v-if="showProposalForm" class="sheet-overlay" @click="showProposalForm = false" />
    <div v-if="showProposalForm" class="sheet" @click.stop>
      <h3>Новая встреча</h3>
      <p class="dates">{{ proposalDays.join(', ') }}</p>
      <input v-model="proposalTitle" class="input" placeholder="Название *" />
      <input v-model="proposalDesc" class="input" placeholder="Описание" />
      <input v-model="proposalPlace" class="input" placeholder="Место" />
      <button class="btn-primary" @click="submitProposal">Отправить группе</button>
    </div>
  </div>
</template>

<style scoped>
.center {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 24px;
  text-align: center;
}
.hint { color: var(--tg-hint); font-size: 14px; }
.hint-block { padding: 48px 24px; color: var(--tg-hint); }
.dates { font-size: 13px; color: var(--tg-hint); }
</style>
