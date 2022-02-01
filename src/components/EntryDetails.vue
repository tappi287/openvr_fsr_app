<template>
<div>
  <b-card bg-variant="dark" text-variant="white" class="text-left m-1">
    <b-card-sub-title>
      {{ entry.appid }} | {{ entry.path }}
    </b-card-sub-title>
    <b-card-text>
      <!-- Install Path Selection -->
      <div class="mt-4 mb-4">
        <h6 style="line-height: 1.25rem;">
          <b-checkbox switch :checked="true" class="d-inline mr-1"
                      @change="toggleModInstallPaths"
                      :disabled="entry.fsrInstalled || entry.fovInstalled || entry.vrpInstalled">
            {{ $t('lib.installLoc') }}
          </b-checkbox>
          <b-icon icon="info-square-fill" class="ml-1" style="opacity: 0.75;"
                  v-b-popover.top.hover="$t('lib.installHint')"
          />
        </h6>
        <b-form-checkbox-group stacked switches
                               :disabled="entry.fsrInstalled || entry.fovInstalled || entry.vrpInstalled"
                               :options="entry.openVrDllPaths"
                               v-model="entry.openVrDllPathsSelected"
                               @change="saveEntryDebounced"
                               class="text-primary"
        />
        <b-form-checkbox-group stacked switches
                               :disabled="entry.fsrInstalled || entry.fovInstalled || entry.vrpInstalled"
                               :options="entry.executablePaths"
                               v-model="entry.executablePathsSelected"
                               @change="saveEntryDebounced"
                               class="text-info"
        />
      </div>

      <!-- FSR PlugIn Install / Uninstall Button -->
      <b-button :variant="entry.fsrInstalled ? 'success' : 'primary'"
                :disabled="!modInstallAllowed(0)"
                @click="installMod(0)" class="mr-2" size="sm">
        <b-icon class="mr-1" :icon="entry.fsrInstalled ? 'square-fill' : 'square'" />
        FSR {{ entry.fsrInstalled ? $t('lib.uninstallPlugin') : $t('lib.installPlugin')}}
      </b-button>

      <!-- Foveated PlugIn Install / Uninstall Button -->
      <b-button :variant="entry.fovInstalled ? 'success' : 'primary'"
                :disabled="!modInstallAllowed(1)"
                @click="installMod(1)" class="mr-2 ml-2" size="sm">
        <b-icon class="mr-1" :icon="entry.fovInstalled ? 'square-fill' : 'square'" />
        Foveated {{ entry.fovInstalled ? $t('lib.uninstallPlugin') : $t('lib.installPlugin')}}
      </b-button>

      <!-- VrPerfKit PlugIn Install / Uninstall Button -->
      <b-button :variant="entry.vrpInstalled ? 'success' : 'info'"
                :disabled="!modInstallAllowed(2)"
                @click="installMod(2)" class="mr-2 ml-2" size="sm">
        <b-icon class="mr-1" :icon="entry.vrpInstalled ? 'square-fill' : 'square'" />
        VrPerfKit {{ entry.vrpInstalled ? $t('lib.uninstallPlugin') : $t('lib.installPlugin')}}
      </b-button>

      <b-button v-if="entry.fsrInstalled" variant="warning"
                @click="resetModSettings(0)"
                class="float-right warning no-border" size="sm">
        <b-icon class="mr-1" icon="arrow-counterclockwise"/>
        Reset FSR Settings
      </b-button>
      <b-button v-if="entry.fovInstalled" variant="warning"
                @click="resetModSettings(1)"
                class="float-right warning no-border" size="sm">
        <b-icon class="mr-1" icon="arrow-counterclockwise"/>
        Reset FFR Settings
      </b-button>
      <b-button v-if="entry.vrpInstalled" variant="warning"
                @click="resetModSettings(2)"
                class="float-right warning no-border" size="sm">
        <b-icon class="mr-1" icon="arrow-counterclockwise"/>
        Reset VRP Settings
      </b-button>
    </b-card-text>

    <!-- Settings Space -->
    <div class="mt-4 card bg-dark" v-if="!settingsAboutToReset">

      <!-- FSR Settings -->
      <template v-if="entry.fsrInstalled">
        <h4 v-if="settingsCategories(0)[0] === null" class="mt-4">{{ $t('lib.settingsTitle') }}</h4>
        <!-- Categories -->
        <div class="mt-1 mb-2 text-center" v-for="(category, idx) in settingsCategories(0)" :key="category"
             :id="'FSR' + idx">
          <template v-if="category !== null"><h6 class="mt-1">{{ category }}</h6></template>
          <!-- Settings -->
          <Setting v-for="s in orderedSettings(0, category)" :key="s.key" :setting="s" :app-id="entry.id"
                   :disabled="!entry.fsrInstalled" @setting-changed="updateModSetting(0)"
                   :fixed-width="true" :group-id="'FSR' + idx"
                   class="mr-3 mb-3" />
        </div>
      </template>

      <!-- Foveated Settings -->
      <template v-if="entry.fovInstalled">
        <h4 v-if="settingsCategories(1)[0] === null" class="mt-4">{{ $t('lib.settingsTitle') }}</h4>
        <!-- Categories -->
        <div class="mt-1 mb-2 text-center" v-for="(category, idx) in settingsCategories(1)" :key="category"
             :id="'FFR' + idx">
          <template v-if="category !== null"><h6 class="mt-1">{{ category }}</h6></template>
          <!-- Settings -->
          <Setting v-for="s in orderedSettings(1, category)" :key="s.key" :setting="s" :app-id="entry.id"
                   :disabled="!entry.fovInstalled" @setting-changed="updateModSetting(1)"
                   :fixed-width="true" :group-id="'FFR' + idx"
                   class="mr-3 mb-3" />
        </div>
      </template>

      <!-- VrPerfKit Settings -->
      <template v-if="entry.vrpInstalled">
        <h4 v-if="settingsCategories(2)[0] === null" class="mt-4">{{ $t('lib.settingsTitle') }}</h4>
        <!-- Categories -->
        <div class="mt-1 mb-2 text-center" v-for="(category, idx) in settingsCategories(2)" :key="category"
             :id="'VRP' + idx">
          <template v-if="category !== null"><h6 class="mt-1">{{ category }}</h6></template>
          <!-- Settings -->
          <Setting v-for="s in orderedSettings(2, category)" :key="s.key" :setting="s" :app-id="entry.id"
                   :disabled="!entry.vrpInstalled" @setting-changed="updateModSetting(2)"
                   :fixed-width="true" :group-id="'VRP' + idx"
                   class="mr-3 mb-3" />
        </div>
      </template>
    </div>

    <!-- Actions -->
    <div style="position: absolute; top: 0.5rem; right: 1.25rem;">
      <template v-if="entry.fsr_compatible !== undefined && entry.fsr_compatible === false">
        <div class="btn btn-sm btn-warning mr-2" :id="entry.id + '-warn'">
          {{ $t('lib.incomp') }}
        </div>
        <b-popover :target="entry.id + '-warn'" triggers="hover">
          <template #title>{{ entry.name }} {{ $t('lib.incompReport') }}</template>
          <span v-html="$t('lib.incompReportText')" />
        </b-popover>
      </template>
      <!-- Launch -->
      <b-button @click="launchApp"
                v-if="entry.userApp === undefined || entry.userApp === false"
                variant="primary" size="sm">
        <b-icon variant="light" icon="play"></b-icon>
        <span class="ml-1 mr-1">{{ $t('lib.launch') }}</span>
      </b-button>
      <!-- Remove User App -->
      <b-button @click="removeUsrApp"
                v-if="entry.userApp === true"
                variant="danger" size="sm">
        <b-icon variant="light" icon="x-square"></b-icon>
        <span class="ml-1 mr-1">{{ $t('lib.addAppRemove') }}</span>
      </b-button>
    </div>
  </b-card>
</div>
</template>

<script>
import Setting from "@/components/Setting";
import {getEelJsonObject} from "@/main";

export default {
  name: "EntryDetails",
  components: {Setting},
  data: function () {
    return {
      id: this._uid,
      settingsAboutToReset: false,
      debounceTimeout: null, debounceRate: 1500,
    }
  },
  props: {
    entry: Object, currentFsrVersion: String, currentFovVersion: String, currentVrpVersion: String,
    steamLibBusy: Boolean
  },
  methods: {
    delay: ms => new Promise(res => {
        setTimeout(res, ms)
    }),
    modInstallAllowed: function (modType) {
      const openVrPathSelected = this.entry.openVrDllPathsSelected.length !== 0
      const exePathSelected = this.entry.executablePathsSelected.length !== 0

      if (modType === 0) {
        return !this.entry.fovInstalled && !this.entry.vrpInstalled && openVrPathSelected
      } else if (modType === 1) {
        return !this.entry.fsrInstalled && !this.entry.vrpInstalled && openVrPathSelected
      } else if (modType === 2) {
        return !this.entry.fsrInstalled && !this.entry.fovInstalled && exePathSelected
      }
    },
    launchApp: async function() {
      if (this.steamLibBusy) { return }
      this.$eventHub.$emit('set-busy', true)
      const r = await getEelJsonObject(window.eel.launch_app(this.entry)())
      if (!r.result) {
        this.$eventHub.$emit('make-toast', r.msg, 'danger', 'Launch', true, -1)
      } else {
        this.$eventHub.$emit('make-toast', r.msg, 'success', false, 1200)
      }
      this.$eventHub.$emit('set-busy', false)
    },
    removeUsrApp: async function() {
      if (this.steamLibBusy) { return }
      const r = await getEelJsonObject(window.eel.remove_custom_app(this.entry)())
      if (!r.result) {
        // Error
        this.$eventHub.$emit('make-toast',
            'Error removing app entry: ' + r.msg, 'danger', 'Remove App Entry', true, -1)
      } else {
        this.$emit('load-steam-lib')
      }
    },
    updateEntry: async function (manifest) {
      this.settingsAboutToReset = true
      this.entry.settings = manifest.settings
      this.entry.fsrInstalled = manifest.fsrInstalled
      this.entry.fsrVersion = manifest.fsrVersion
      this.entry.fov_settings = manifest.fov_settings
      this.entry.fovInstalled = manifest.fovInstalled
      this.entry.fovVersion = manifest.fovVersion
      this.entry.vrp_settings = manifest.vrp_settings
      this.entry.vrpInstalled = manifest.vrpInstalled
      this.entry.vrpVersion = manifest.vrpVersion
      this.$nextTick(() => { this.settingsAboutToReset = false })
    },
    installMod: async function (modType) {
      if (this.steamLibBusy) { return }
      this.$eventHub.$emit('set-busy', true)
      let r = {}
      r = await getEelJsonObject(window.eel.toggle_mod_install(this.entry, modType)())

      if (!r.result) {
        // Report Error
        this.$eventHub.$emit('make-toast', r.msg, 'danger', 'PlugIn Installation', true, -1)
      }

      if (r.manifest !== undefined) {
        // Update settings
        await this.updateEntry(r.manifest)
        // Update disk cache
        this.$emit('entry-updated', this.entry)

        // Report install state
        if (this.entry.fsrInstalled || this.entry.fovInstalled || this.entry.vrpInstalled) {
          this.$eventHub.$emit('make-toast', 'Installed PlugIn to ' + this.entry.name, 'success',
              'PlugIn Installed')
        } else {
          this.$eventHub.$emit('make-toast', 'Uninstalled PlugIn from ' + this.entry.name, 'success',
          'PlugIn Uninstalled')
        }
      }
      this.$eventHub.$emit('set-busy', false)
    },
    saveEntryDebounced: function() {
      clearTimeout(this.debounceTimeout)
      this.debounceTimeout = setTimeout(this.saveEntry, this.debounceRate)
    },
    saveEntry: function() {
      if (this.steamLibBusy) { return }
      // Update disk cache
      this.$emit('entry-updated')
    },
    toggleModInstallPaths: function (checked) {
      if (checked) {
        this.entry.openVrDllPathsSelected = this.entry.openVrDllPaths
        this.entry.executablePathsSelected = this.entry.executablePaths
      } else {
        this.entry.openVrDllPathsSelected = []
        this.entry.executablePathsSelected = []
      }
      this.saveEntryDebounced()
    },
    updateModSetting: async function(modType = -1) {
      await this.updateMod(modType, true)
      // Update disk cache
      this.$emit('entry-updated')
    },
    updateMod: async function (modType = 0, write = false) {
      if (this.steamLibBusy) { return }
      this.$eventHub.$emit('set-busy', true)

      const r = await getEelJsonObject(window.eel.update_mod(this.entry, modType, write)())

      if (!r.result) {
        this.$eventHub.$emit('make-toast', r.msg, 'danger', 'PlugIn Installation', true, -1)
      } else {
        // Update Entry
        await this.updateEntry(r.manifest)
      }

      this.$eventHub.$emit('set-busy', false)
    },
    resetModSettings: async function (modType = -1) {
      if (this.steamLibBusy) { return }
      this.$eventHub.$emit('set-busy', true)

      const r = await getEelJsonObject(window.eel.reset_mod_settings(this.entry, modType)())

      if (!r.result) {
        this.$eventHub.$emit('make-toast', r.msg, 'danger', 'PlugIn Settings', true, -1)
      } else {
        // Update Entry
        await this.updateEntry(r.manifest)
      }
      await this.saveEntry()
      this.$eventHub.$emit('set-busy', false)
    },
    _getSettingsByType(modType = -1) {
      let settings = {}
      if (modType === 0) {
        settings = this.entry.settings
      } else if (modType === 1) {
        settings = this.entry.fov_settings
      } else if (modType === 2) {
        settings = this.entry.vrp_settings
      }
      return settings
    },
    settingsCategories(modType = -1) {
      let settings = this._getSettingsByType(modType)
      let categorys = new Set()

      for (const key in settings) {
        const setting = settings[key]
        if (setting.category !== undefined) { categorys.add(setting.category) }
      }
      if (categorys.size > 0) { return Array.from(categorys).sort() }
      return [null]
    },
    orderedSettings(modType = -1, category = null) {
      let settings = this._getSettingsByType(modType)
      if (category === null) { return settings }

      let orderedSettings = {}
      let orderedKeys = []
      for (const key in settings) { orderedKeys.push(key) }
      for (const key in orderedKeys.sort()) {
        let setting = settings[key]
        if (setting.category === category) { orderedSettings[key] = setting }
      }
      return orderedSettings
    }
  },
  async mounted() {
    for (const modType in [0, 1, 2]) {
      await this.updateMod(Number(modType))
    }
  }
}
</script>

<style scoped>

</style>