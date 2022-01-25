<template>
  <div class="setting" v-if="!settingHidden">
    <b-input-group size="sm" class="setting-field">
      <b-input-group-prepend>
        <b-input-group-text class="info-field fixed-width-name" :id="nameId">
          <div class="mr-2">{{ setting.name }}</div>
          <b-icon v-if="settingDesc !== ''" icon="info-square" class="mr-1"
                  v-b-popover.hover.topright="settingDesc">
          </b-icon>
        </b-input-group-text>
      </b-input-group-prepend>

      <b-input-group-append>

        <!-- Dropdown Menu -->
        <template v-if="inputType === 'value'">
          <b-dropdown :text="currentSettingName" :variant="variant" :id="elemId"
                      class="setting-item fixed-width-setting no-border" :disabled="disabled">
            <b-dropdown-item v-for="s in setting.settings" :key="s.value"
                             @click="selectSetting(s)">
              {{ s.name }}
              <b-icon v-if="s.desc !== undefined" icon="info-square"
                      class="ml-2" v-b-popover.hover.topright="s.desc">
              </b-icon>
              <b-icon v-if="showPerformance && s.perf !== undefined" icon="bar-chart"
                      class="ml-2 text-muted"
                      v-b-popover.hover.topright="s.perf.replace('G', 'GPU').replace('C', 'CPU')">
              </b-icon>
            </b-dropdown-item>
          </b-dropdown>
        </template>

        <!-- Spinner Menu -->
        <template v-if="inputType === 'range'">
          <div :id="elemId" class="fixed-width-setting position-relative">
            <b-form-spinbutton v-model="rangeValue" :min="rangeMin" :max="rangeMax" :step="rangeStep" inline
                               :class="'spinner-setting no-border btn-' + variant"
                               :disabled="disabled"
                               @change="spinnerSettingUpdated" :formatter-fn="spinnerDisplay">
            </b-form-spinbutton>
          </div>

          <!-- Manual Spinner Input -->
          <b-popover ref="spinnerPopover" :target="elemId" :triggers="'manual'">
            <template #title>Manual Input</template>
            <template #default>
              <div role="group">
                <label :for="'input-' + elemId">
                  Manually enter a value between {{ rangeMin }} and {{ rangeMax }}:
                </label>
                <b-form-input :id="'input-' + elemId" size="sm" debounce="100" :disabled="disabled"
                              v-model="spinnerInputValue" type="number"
                              :max="rangeMax" :min="rangeMin" :step="rangeStep"
                              :state="spinnerInputState" number />
                <b-form-invalid-feedback :id="'input-' + elemId + '-feedback'">
                  Enter a value within the described range and use a dot . as decimal separator.
                </b-form-invalid-feedback>
              </div>
              <div class="text-right mt-2">
                <b-button @click="confirmSpinnerPopover" :disabled="disabled"
                          size="sm" variant="success" aria-label="Confirm">
                  Confirm
                </b-button>
                <b-button @click="closeSpinnerPopover" size="sm" aria-label="Close" class="ml-1">
                  Abort
                </b-button>
              </div>
            </template>
          </b-popover>
        </template>

        <!-- Keyboard Key -->
        <template v-if="inputType === 'key'">
          <div class="btn btn-secondary setting-item fixed-width-setting" :id="elemId">
            <b-link @click="startListening" class="text-white ml-2">
              <b-icon shift-v="-1" icon="keyboard" class="text-white" />
              <span class="ml-2">{{ settingKeyName }}</span>
            </b-link>
          </div>
        </template>

        <!-- Keyboard Key Combo -->
        <template v-if="inputType === 'keyCombo'">
          <div class="btn btn-secondary setting-item fixed-width-setting" :id="elemId">
            <b-link @click="startListening" class="text-white ml-2">
              <b-icon shift-v="-1" icon="keyboard" class="text-white" />
              <span class="ml-2">{{ settingKeyComboName }}</span>
            </b-link>
          </div>
        </template>

      </b-input-group-append>
    </b-input-group>

    <!-- Keyboard Assign Modal -->
    <b-modal v-model="listening" centered hide-header-close no-close-on-backdrop no-close-on-esc :id="modalId">
      <template #modal-title>
        <b-icon icon="keyboard" variant="primary"></b-icon>
        <span class="ml-2">{{ setting.name }}</span>
      </template>
      <div class="d-block">
        <p style="font-size: small;" v-if="settingDesc !== ''">{{ settingDesc }}</p>
        <div :class="eventCaptured ? '' : 'old-setting'">
          <h5>Hotkey Mapping</h5>
          <p style="font-size: small;">{{ $t('setting.keyboardAssign') }}</p>
          <p>
            <template v-if="inputType === 'keyCombo'">
              <span>Modifier</span>
              <b-dropdown :text="modifierKey.toUpperCase()" size="sm" class="ml-2">
                <b-dropdown-item v-for="mKey in modifierKeys" :key="mKey"
                                 @click="updateModifierKey(mKey)">
                  {{ mKey.toUpperCase() }}
                </b-dropdown-item>
              </b-dropdown>
            </template>
            <span class="ml-2">Key</span>
            <span class="ml-2">{{ capturedValueName }}</span>
          </p>
        </div>
      </div>

      <template #modal-footer>
        <div class="d-block text-right">
          <b-button v-if="eventCaptured" @click="confirmAssign" variant="success">Confirm</b-button>
          <b-button class="ml-2" v-if="eventCaptured" @click="startListening" variant="primary">Retry</b-button>
          <b-button class="ml-2" variant="secondary" @click="abortListening">Abort</b-button>
        </div>
      </template>
    </b-modal>
  </div>
</template>

<script>

import {minutesToDaytime, setFixedWidth, keyCodes} from "@/main";

export default {
  name: 'Setting',
  data: function () {
    return {
      currentSettingValue: {},
      elemId: 'setting' + this._uid, // _uid is a unique identifier for each vue component
      nameId: 'name' + this._uid,
      settingDesc: '',
      inputType: 'value',
      rangeMin: 0,
      rangeMax: 1,
      rangeStep: 1,
      rangeDisp: undefined,
      rangeValue: 0,
      spinnerTimeout: null,
      showSpinnerInputPopover: false,
      spinnerInputValue: 0,
      spinnerDebounceRate: 2000,
      listening: false,
      eventCaptured: false,
      capturedEvent: null,
      modifierKeys: ['ctrl', 'alt', 'shift', 'Single Key'],
      modifierKeyEmpty: 'Single Key',
      modifierKey: 'ctrl',
      modalId: 'assign' + this._uid,
    }
  },
  props: {
    appId: String, setting: Object, variant: String, disabled: Boolean, fixedWidth: Boolean, groupId: String
  },
  methods: {
    selectSetting: function (s) {
      this.currentSettingValue = s.value
      console.log('Emitting setting update', this.setting.key, s.value)
      this.setting.value = s.value
      this.$emit('setting-changed', this.setting, s.value)
    },
    spinnerSettingUpdated: function () {
      clearTimeout(this.spinnerTimeout)
      this.spinnerTimeout = setTimeout(this.spinnerDebouncedUpdate, this.spinnerDebounceRate)
      this.currentSettingValue = this.rangeValue
    },
    spinnerDebouncedUpdate: function () {
      this.spinnerTimeout = null
      this.setting.value = this.rangeValue
      this.$emit('setting-changed', this.setting, this.rangeValue)
    },
    spinnerDisplay: function (value) {
      if (this.rangeDisp === 'floatpercent') { return String(Math.round(value * 100)) + '%' }
      if (this.rangeDisp === 'time') { return minutesToDaytime(value) }
      if (this.rangeDisp === 'position') { if (value === 0) { return 'Random' } }
      return value
    },
    iterateSettings: function (func) {
      for (let i=0; i <= this.setting.settings.length; i++) {
        let setting = this.setting.settings[i]
        if (setting === undefined) { continue }
        func(this, setting)
      }
    },
    setupSpinnerDblClick: function () {
      // Double clicking the output/value will open a manual input Popover
      let output = document.getElementById(this.elemId).querySelector('output')
      output.addEventListener('dblclick', this.handleSpinnerDblClick, false)
    },
    handleSpinnerDblClick: function () {
      this.spinnerInputValue = this.rangeValue
      this.$refs.spinnerPopover.$emit('open')
    },
    confirmSpinnerPopover: function () {
      this.closeSpinnerPopover()
      if (this.checkSpinnerInputValue(this.spinnerInputValue)) {
        this.rangeValue = this.spinnerInputValue
        this.spinnerSettingUpdated()
        console.log('Confirmed spinner manual input value', this.spinnerInputValue)
      }
    },
    closeSpinnerPopover: function () { this.$refs.spinnerPopover.$emit('close') },
    checkSpinnerInputValue: function (value) {
      if (Number.isFinite(value)) {
        if (value >= this.rangeMin && value <= this.rangeMax) {
          return true
        }
      }
      return false
    },
    handleKeyDownEvent: async function (event) {
      event.preventDefault()
      if (this.listening && !this.eventCaptured) {
        this.eventCaptured = true
        console.log(event)
        if (this.inputType === 'key') {
          this.capturedEvent = {name: 'Keyboard', value: event.keyCode}
        } else if (this.inputType === 'keyCombo') {
          this.capturedEvent = {name: 'Keyboard', value: [this.modifierKey, event.key]}
        }
      }
    },
    listenToKeyboard: function (remove = false) {
      // Add or Remove Keydown event listener
      const m = document.getElementById(this.modalId)
      if (m !== null && !remove) {
        console.log('Listening for keyboard events')
        m.addEventListener('keydown', this.handleKeyDownEvent)
      } else if (m !== null && remove) {
        console.log('Removing Keyboard listener')
        m.removeEventListener('keydown', this.handleKeyDownEvent)
      }
    },
    startListening: function () {
      this.eventCaptured = false; this.capturedEvent = null; this.listening = true
      if (Array.isArray(this.setting.value)) { this.modifierKey = this.setting.value[0] }
      this.$nextTick(() => { this.listenToKeyboard(false) })
    },
    abortListening: function () {
      this.listenToKeyboard(true); this.listening = false; this.eventCaptured = false
    },
    updateModifierKey: function (mKey) {
      this.modifierKey = mKey
      if (this.capturedEvent !== null) {
        const key = this.capturedEvent.value[1]
        this.capturedEvent.value = [this.modifierKey, key]
      }
    },
    confirmAssign: async function () {
      if (Array.isArray(this.capturedEvent.value) && this.modifierKey === this.modifierKeyEmpty) {
        // Remove Modifier Key
        this.capturedEvent.value = this.capturedEvent.value[1]
      }
      this.selectSetting(this.capturedEvent)
      this.abortListening()
    },
    keyCodeValueToDisplayString: function(value) {
      if (value !== undefined && value !== '' && value !== null) {
        const code = Number(value)
        if (code in keyCodes) { return keyCodes[code].toUpperCase() }
        return 'Key Code ' + code
      }
      return 'Not Set'
    },
    updateFixedWidth: async function () {
      if (this.fixedWidth) { setFixedWidth(this.groupId, this.nameId, this.elemId) }
    },
  },
  created: function () {
    // Set description
    this.settingDesc = this.setting.desc || ''

    // Check Setting Type
    if (this.setting.settings !== undefined && this.setting.settings.length) {
      if (this.setting.settings[0].settingType !== undefined) {
        if (this.setting.settings[0].settingType === 'range') {
          this.inputType = 'range'
          this.rangeMin = this.setting.settings[0].min
          this.rangeMax = this.setting.settings[0].max
          this.rangeStep = this.setting.settings[0].step
          this.rangeDisp = this.setting.settings[0].display
          this.rangeValue = this.setting.value
          this.spinnerInputValue = this.setting.value
          this.settingDesc = this.setting.desc || this.setting.settings[0].desc || ''
          this.$nextTick(() => { this.setupSpinnerDblClick() })
        } else if (this.setting.settings[0].settingType === 'key') {
          this.inputType = 'key'
        } else if (this.setting.settings[0].settingType === 'keyCombo') {
          this.inputType = 'keyCombo'
          if (!Array.isArray(this.setting.value)) { this.modifierKey = this.modifierKeyEmpty }
        }
      }
    }
  },
  mounted () {
    if (this.variant === undefined) { this.variant = 'secondary'}
    this.currentSettingValue = this.setting.value
    this.$emit('setting-ready', this)
  },
  updated() {
    // Access after rendering finished
    this.$nextTick(() => { this.updateFixedWidth() })
  },
  computed: {
    currentSettingName: function () {
      let name = 'No Settings!'
      if (this.setting === undefined) { return 'Not set!' }

      this.iterateSettings(function (instance, setting) {
        if (instance.currentSettingValue === setting.value) {
          name = setting.name
        }
      })
      return name
    },
    settingHidden: function () {
      if (this.setting === undefined) { return true }
      return this.setting['hidden'] || false
    },
    spinnerInputState: function () {
      return this.checkSpinnerInputValue(this.spinnerInputValue)
    },
    settingKeyName() {
      if (this.setting === undefined) { return 'Undefined' }
      if (this.inputType === 'key') {
        return this.keyCodeValueToDisplayString(this.setting.value)
      } else if (this.inputType === 'keyCombo') {
        if (!Array.isArray(this.setting.value)) {
          return String(this.setting.value).toUpperCase()
        }
        return String(this.setting.value[1]).toUpperCase()
      }
      return 'Undefined'
    },
    settingKeyComboName() {
      if (this.setting === undefined) { return 'Undefined' }
      if (!Array.isArray(this.setting.value)) {
        return String(this.setting.value).toUpperCase()
      }
      return String(this.setting.value[0]).toUpperCase() + " " + String(this.setting.value[1]).toUpperCase()
    },
    capturedValueName() {
      if (!this.eventCaptured) { return this.settingKeyName }
      if (this.inputType === 'key') {
        return this.keyCodeValueToDisplayString(this.capturedEvent.value)
      } else if (this.inputType === 'keyCombo') {
        return String(this.capturedEvent.value[1]).toUpperCase()
      }
      return 'Undefined'
    },
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style>
.spinner-setting { width: 100% !important; }
.spinner-overlay {
  width: 50%;
  height: 75%;
  position: absolute;
  left: 22.5%;
  margin: .25rem;
}
</style>
