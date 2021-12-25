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
                @click="installMod(1)" class="mr-2">
        <b-icon class="mr-1" :icon="entry.fsrInstalled ? 'square-fill' : 'square'" />
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
      <div class="mt-1">
        <Setting v-for="s in entry.settings" :key="s.key" :setting="s" :app-id="entry.id"
                 :disabled="!entry.fsrInstalled" @setting-changed="updateFsrSetting(0)"
                 class="mr-3 mb-3" />
      </div>
    </template>

    <!-- Foveated Settings -->
    <template v-if="entry.fovInstalled">
      <h6 class="mt-4">{{ $t('lib.settingsTitle') }}</h6>
      <div class="mt-1">
        <Setting v-for="s in entry.fov_settings" :key="s.key" :setting="s" :app-id="entry.id"
                 :disabled="!entry.fovInstalled" @setting-changed="updateFsrSetting(1)"
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
    entry: Object, currentFsrVersion: String, currentFovVersion: String,
  },
  methods: {
    launchApp: async function() {
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
      const r = await getEelJsonObject(window.eel.remove_custom_app(this.entry)())
      if (!r.result) {
        // Error
        this.$eventHub.$emit('make-toast',
            'Error removing app entry: ' + r.msg, 'danger', 'Remove App Entry', true, -1)
      } else {
        this.$emit('load-steam-lib')
      }
    },
    installMod: async function (modType) {
      this.$eventHub.$emit('set-busy', true)
      let r = {}
      r = await getEelJsonObject(window.eel.toggle_mod_install(this.entry, modType)())

      if (!r.result) {
        // Report Error
        this.$eventHub.$emit('make-toast', r.msg, 'danger', 'PlugIn Installation', true, -1)
      } else {
        // Update settings
        this.entry = r.manifest

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
    updateFsrSetting: async function(modType = 0) {
      await this.updateFsr(modType)
      // Update disk cache
      this.$emit('entry-updated')
    },
    updateFsr: async function (modType = 0) {
      if (!this.entry['fsrInstalled'] && modType === 0) { return }
      if (!this.entry['fovInstalled'] && modType === 1) { return }

      this.$eventHub.$emit('set-busy', true)

      const r = await getEelJsonObject(window.eel.update_mod(this.entry, modType)())

      if (!r.result) {
        this.$eventHub.$emit('make-toast', r.msg, 'danger', 'PlugIn Installation', true, -1)
      } else {
        // Update Entry
        this.entry = r.manifest
      }

      this.$eventHub.$emit('set-busy', false)
    },
  },
  async mounted() {
    await this.updateFsr()
  }
}
</script>

<style scoped>

</style>