<template>
<div>
  <b-card :title="entry.name"
          bg-variant="dark" text-variant="white" class="text-left m-1">
    <b-card-sub-title>
      {{ entry.appid }} | {{ entry.path }}
    </b-card-sub-title>
    <b-card-text>
      <!-- Install Path Selection -->
      <div class="mt-4 mb-4">
        <h6>
          {{ $t('lib.installLoc') }}
          <b-icon icon="info-square-fill"
                  v-b-popover.top.hover="$t('lib.installHint')"
          />
        </h6>
        <b-form-checkbox-group stacked switches
                               :disabled="entry.fsrInstalled"
                               :options="entry.openVrDllPaths"
                               v-model="entry.openVrDllPathsSelected"
                               @change="saveEntry"
        />
      </div>

      <!-- FSR PlugIn Install / Uninstall Button -->
      <b-button :variant="entry.fsrInstalled ? 'success' : 'primary'"
                :disabled="entry.openVrDllPathsSelected.length === 0 || entry.fovInstalled"
                @click="installMod(0)" class="mr-2">
        <b-icon class="mr-1" :icon="entry.fsrInstalled ? 'square-fill' : 'square'" />
        FSR {{ entry.fsrInstalled ? $t('lib.uninstallPlugin') : $t('lib.installPlugin')}}
      </b-button>

      <!-- Version Report -->
      <span v-if="entry.fsrInstalled"
            :class="entry.fsrVersion !== currentFsrVersion ? 'text-warning' : ''">
        OpenVR FSR: {{ entry.fsrVersion }}
        <template v-if="entry.fsrVersion !== currentFsrVersion">
          <b-icon icon="info-circle-fill" v-b-popover.top.hover="$t('main.versionMismatch')" />
        </template>
        <template v-else>
          <b-icon icon="info-circle-fill" class="text-success" v-b-popover.top.hover="$t('main.versionMatch')" />
        </template>
      </span>

      <!-- Foveated PlugIn Install / Uninstall Button -->
      <b-button :variant="entry.fovInstalled ? 'success' : 'primary'"
                :disabled="entry.openVrDllPathsSelected.length === 0 || entry.fsrInstalled"
                @click="installMod(1)" class="mr-2 ml-2">
        <b-icon class="mr-1" :icon="entry.fovInstalled ? 'square-fill' : 'square'" />
        Foveated {{ entry.fovInstalled ? $t('lib.uninstallPlugin') : $t('lib.installPlugin')}}
      </b-button>

      <!-- Version Report -->
      <span v-if="entry.fovInstalled"
            :class="entry.fovVersion !== currentFovVersion ? 'text-warning' : ''">
        OpenVR Foveated: {{ entry.fovVersion }}
        <template v-if="entry.fovVersion !== currentFovVersion">
          <b-icon icon="info-circle-fill" v-b-popover.top.hover="$t('main.versionMismatch')" />
        </template>
        <template v-else>
          <b-icon icon="info-circle-fill" class="text-success" v-b-popover.top.hover="$t('main.versionMatch')" />
        </template>
      </span>
    </b-card-text>

    <!-- FSR Settings -->
    <template v-if="entry.fsrInstalled">
      <h6 class="mt-4">{{ $t('lib.settingsTitle') }}</h6>
      <!-- Categories -->
      <div class="mt-1" v-for="category in settingsCategories(0)" :key="category">
        <template v-if="category !== null"><h6 class="mt-1">{{ category }}</h6></template>
        <!-- Settings -->
        <Setting v-for="s in orderedSettings(0, category)" :key="s.key" :setting="s" :app-id="entry.id"
                 :disabled="!entry.fsrInstalled" @setting-changed="updateModSetting(0)"
                 class="mr-3 mb-3" />
      </div>
    </template>

    <!-- Foveated Settings -->
    <template v-if="entry.fovInstalled">
      <h6 class="mt-4">{{ $t('lib.settingsTitle') }}</h6>
      <!-- Categories -->
      <div class="mt-1" v-for="category in settingsCategories(1)" :key="category">
        <template v-if="category !== null"><h6 class="mt-4">{{ category }}</h6></template>
        <!-- Settings -->
        <Setting v-for="s in orderedSettings(1, category)" :key="s.key" :setting="s" :app-id="entry.id"
                 :disabled="!entry.fovInstalled" @setting-changed="updateModSetting(1)"
                 class="mr-3 mb-3" />
      </div>
    </template>

    <!-- Actions -->
    <div style="position: absolute; top: 1.25rem; right: 1.25rem;">
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
                v-if="entry.userApp !== undefined || entry.userApp === true"
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
    }
  },
  props: {
    entry: Object, currentFsrVersion: String, currentFovVersion: String, steamLibBusy: Boolean
  },
  methods: {
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
    updateEntry: function (manifest) {
      this.entry.settings = manifest.settings
      this.entry.fsrInstalled = manifest.fsrInstalled
      this.entry.fsrVersion = manifest.fsrVersion
      this.entry.fov_settings = manifest.fov_settings
      this.entry.fovInstalled = manifest.fovInstalled
      this.entry.fovVersion = manifest.fovVersion
    },
    installMod: async function (modType) {
      if (this.steamLibBusy) { return }
      this.$eventHub.$emit('set-busy', true)
      let r = {}
      r = await getEelJsonObject(window.eel.toggle_mod_install(this.entry, modType)())

      if (!r.result) {
        // Report Error
        this.$eventHub.$emit('make-toast', r.msg, 'danger', 'PlugIn Installation', true, -1)
      } else {
        // Update settings
        this.updateEntry(r.manifest)

        // Update install state
        if (this.entry.fsrInstalled || this.entry.fovInstalled) {
          this.$eventHub.$emit('make-toast', 'Installed PlugIn to ' + this.entry.name, 'success',
              'PlugIn Installed')
        } else {
          this.$eventHub.$emit('make-toast', 'Uninstalled PlugIn from ' + this.entry.name, 'success',
          'PlugIn Uninstalled')
        }

        // Update disk cache
        this.$emit('entry-updated', this.entry)
      }
      this.$eventHub.$emit('set-busy', false)
    },
    saveEntry: function() {
      if (this.steamLibBusy) { return }
      // Update disk cache
      this.$emit('entry-updated')
    },
    updateModSetting: async function(modType = 0) {
      await this.updateMod(modType)
      // Update disk cache
      this.$emit('entry-updated')
    },
    updateMod: async function (modType = 0) {
      if (this.steamLibBusy) { return }
      this.$eventHub.$emit('set-busy', true)

      const r = await getEelJsonObject(window.eel.update_mod(this.entry, modType)())

      if (!r.result) {
        this.$eventHub.$emit('make-toast', r.msg, 'danger', 'PlugIn Installation', true, -1)
      } else {
        // Update Entry
        this.updateEntry(r.manifest)
      }

      this.$eventHub.$emit('set-busy', false)
    },
    _getSettingsByType(modType = 0) {
      let settings = {}
      if (modType === 0) {
        settings = this.entry.settings
      } else if (modType === 1) {
        settings = this.entry.fov_settings
      }
      return settings
    },
    settingsCategories(modType = 0) {
      let settings = this._getSettingsByType(modType)
      let categorys = new Set()

      for (const key in settings) {
        const setting = settings[key]
        if (setting.category !== undefined) { categorys.add(setting.category) }
      }
      if (categorys.size > 0) { return categorys.values() }
      return [null]
    },
    orderedSettings(modType = 0, category = null) {
      let settings = this._getSettingsByType(modType)
      if (category === null) { return settings }

      let orderedSettings = {}
      for (const key in settings) {
        let setting = settings[key]
        if (setting.category === category) { orderedSettings[key] = setting }
      }
      return orderedSettings
    }
  },
  async mounted() {
    await this.updateMod()
  }
}
</script>

<style scoped>

</style>