
<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const facilities = ref([])
const selectedFacilityId = ref(null)
const openingHour = 9
const closingHour = 19
const berlinDate = () => new Intl.DateTimeFormat('sv-SE', {
  timeZone: 'Europe/Berlin', year: 'numeric', month: '2-digit', day: '2-digit'
}).format(new Date())
const today = ref(berlinDate())
const selectedDate = ref(today.value)
const selectedSlot = ref(null)
const message = ref('')
const messageIsError = ref(false)
const bookings = ref([])
const loading = ref(true)
const saving = ref(false)
const loadFailed = ref(false)
const now = ref(Date.now())
let requestId = 0
let timer

const slots = computed(() => Array.from({ length: closingHour - openingHour }, (_, i) => ({
  start: `${String(openingHour + i).padStart(2, '0')}:00`,
  end: `${String(openingHour + i + 1).padStart(2, '0')}:00`
})))

const bookedSlots = computed(() => bookings.value
  .filter(b => b.facility_id === selectedFacilityId.value && b.date === selectedDate.value)
  .map(b => b.start))

const isBooked = slot => bookedSlots.value.includes(slot.start)

function isPast(slot) {
  // Datum und Uhrzeit des Platzes werden ausdrücklich in Europe/Berlin verglichen.
  const current = new Intl.DateTimeFormat('sv-SE', {
    timeZone: 'Europe/Berlin', year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hourCycle: 'h23'
  }).format(new Date(now.value)).replace(', ', ' ')
  return `${selectedDate.value} ${slot.start}` <= current
}

async function api(path, options = {}) {
  const response = await fetch(`${API}${path}`, options)
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(typeof body.detail === 'string' ? body.detail : 'Anfrage fehlgeschlagen.')
  }
  return response.status === 204 ? null : response.json()
}

async function loadBookings() {
  const id = ++requestId
  loading.value = true
  loadFailed.value = false
  bookings.value = []
  try {
    const [places, result] = await Promise.all([api('/facilities'), api('/bookings')])
    if (id === requestId) {
      facilities.value = places
      bookings.value = result
      if (!places.some(place => place.id === selectedFacilityId.value)) {
        selectedFacilityId.value = places[0]?.id ?? null
      }
    }
  } catch (error) {
    if (id === requestId) {
      loadFailed.value = true
      messageIsError.value = true
      message.value = `Verfügbarkeit konnte nicht geladen werden: ${error.message}`
    }
  } finally {
    if (id === requestId) loading.value = false
  }
}

function selectSlot(slot) {
  if (!selectedFacilityId.value || !selectedDate.value || loading.value || saving.value || loadFailed.value || isBooked(slot) || isPast(slot)) return
  selectedSlot.value = slot
  message.value = ''
}

async function createBooking() {
  const slot = selectedSlot.value
  if (!slot || !selectedFacilityId.value || !selectedDate.value || loading.value || saving.value || loadFailed.value || isBooked(slot) || isPast(slot)) return
  saving.value = true
  messageIsError.value = false
  message.value = ''
  try {
    await api('/bookings', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ facility_id: selectedFacilityId.value, date: selectedDate.value, start: slot.start })
    })
    message.value = 'Buchung erfolgreich erstellt.'
  } catch (error) {
    messageIsError.value = true
    message.value = error.message
  } finally {
    selectedSlot.value = null
    await loadBookings()
    saving.value = false
  }
}

watch([selectedDate, selectedFacilityId], () => {
  selectedSlot.value = null
  message.value = ''
})

onMounted(() => {
  loadBookings()
  timer = setInterval(() => {
    now.value = Date.now()
    today.value = berlinDate()
  }, 30000)
})

onUnmounted(() => { clearInterval(timer); requestId++ })
</script>

<template>
  <main class="page">
    <section class="booking-card">
      <header class="header">
        <div class="header-top">
            <h1>Sportstätte buchen</h1>
            <p>Wähle ein Datum und ein verfügbares Zeitfenster.</p>
        </div>
        <img src="/dd.png" alt="Logo" class="header-image" />
      </header>

      <div class="field">
        <label for="facility">Sportstätte</label>
        <select id="facility" v-model="selectedFacilityId" :disabled="loading || saving || loadFailed || !facilities.length">
          <option v-for="facility in facilities" :key="facility.id" :value="facility.id">
            {{ facility.name }}
          </option>
        </select>
        <p v-if="!loading && !loadFailed && !facilities.length">Keine Sportstätten vorhanden.</p>
      </div>

      <div class="field">
        <label for="date">Datum</label>
        <input
          id="date"
          v-model="selectedDate"
          type="date"
          :min="today"
          :disabled="saving"
        />
      </div>

      <div class="slots-section">
        <h2>Verfügbare Zeitfenster</h2>
        <p v-if="loading" role="status">Verfügbarkeit wird geladen…</p>
        <button v-if="loadFailed && !loading" class="retry-button" @click="loadBookings">
          Erneut laden
        </button>

        <div class="slots-grid">
          <button
            v-for="slot in slots"
            :key="slot.start"
            class="slot"
            :class="{
              selected: selectedSlot?.start === slot.start,
              booked: isBooked(slot)
            }"
            :disabled="!selectedFacilityId || !selectedDate || loading || saving || loadFailed || isBooked(slot) || isPast(slot)"
            :aria-pressed="selectedSlot?.start === slot.start"
            @click="selectSlot(slot)"
          >
            {{ slot.start }}
          </button>
        </div>

        <div class="legend">
          <!--<span><i class="dot free"></i> Frei</span>-->
          <span><i class="dot occupied"></i> Belegt</span>
        </div>
      </div>

      <footer class="footer">
        <div class="selection">
          <small>Ausgewählte Buchung</small>
          <strong v-if="selectedSlot">
            {{ selectedSlot.start }}–{{ selectedSlot.end }} Uhr
          </strong>
          <strong v-else>Keine Uhrzeit ausgewählt</strong>
        </div>

        <button
          class="book-button"
          :disabled="!selectedFacilityId || !selectedDate || !selectedSlot || loading || saving || loadFailed"
          @click="createBooking"
        >
          {{ saving ? 'Wird gebucht…' : 'Buchen' }}
        </button>
      </footer>

      <p v-if="message" class="message" :class="{ error: messageIsError }" role="status">
        {{ message }}
      </p>
    </section>
  </main>
</template>

<style>
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: Inter, system-ui, sans-serif;
  color: #20242c;
  background: #f5f6f8;
}

.page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 24px;
}

.booking-card {
  width: 100%;
  max-width: 520px;
  padding: 28px;
  background: white;
  border: 1px solid #e6e8ec;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.04);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;           
  width: 100%;                   
  box-sizing: border-box;
  margin-bottom: 28px;
}

.header-image {
  max-width: 120px;
  height: auto;                  
}

h1 {
  margin: 0 0 8px;
  font-size: 23px;
  color: #000000;
}

.header-top p {
  margin: 0;
  color: #777f8b;
  font-size: 14px;
}

.field {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 600;
}

input, select {
  width: 100%;
  padding: 12px;
  border: 1px solid #dce0e6;
  border-radius: 8px;
  background: white;
  font: inherit;
}

input:disabled {
  background: #f7f8fa;
  color: #4a5260;
}

.slots-section {
  margin-top: 28px;
}

h2 {
  font-size: 16px;
  margin-bottom: 16px;
}

.slots-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}

.slot {
  padding: 12px 4px;
  border: 1px solid #dce0e6;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  font-size: 13px;
}

.slot:hover:not(:disabled) {
  border-color: #252b35;
}

.slot.selected {
  background: #252b35;
  color: white;
  border-color: #252b35;
}

.slot:disabled {
  background: #f1f2f4;
  color: #a2a7af;
  cursor: not-allowed;
}

.legend {
  display: flex;
  gap: 20px;
  margin-top: 18px;
  font-size: 12px;
  color: #777f8b;
}

.legend span {
  display: flex;
  align-items: center;
  gap: 6px;
}

.dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  display: inline-block;
}

.free {
  background: #399b68;
}

.occupied {
  background: #a2a7af;
}

.footer {
  border-top: 1px solid #e6e8ec;
  margin-top: 28px;
  padding-top: 22px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.selection {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.selection small {
  color: #777f8b;
}

.selection strong {
  font-size: 14px;
}

.book-button {
  border: 0;
  background: #252b35;
  color: white;
  border-radius: 8px;
  padding: 12px 20px;
  cursor: pointer;
  font-weight: 600;
}

.book-button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.message {
  margin: 20px 0 0;
  padding: 12px;
  border-radius: 8px;
  background: #edf8f0;
  color: #236d43;
  font-size: 14px;
}

.message.error {
  background: #fff0f0;
  color: #9c2525;
}

.retry-button {
  padding: 8px 12px;
  margin-bottom: 12px;
  border: 1px solid #dce0e6;
  border-radius: 8px;
  background: white;
  cursor: pointer;
}

@media (max-width: 480px) {
  .booking-card {
    padding: 18px;
  }

  .slots-grid {
    gap: 6px;
  }

  .slot {
    font-size: 12px;
  }
}
</style>

