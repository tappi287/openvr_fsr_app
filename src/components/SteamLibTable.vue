<template>
  <div>
    <!-- Filter -->
    <b-input-group size="md" class="mt-2">
      <b-input-group-prepend>
        <!-- Add User App -->
        <b-button @click="showAddAppModal=!showAddAppModal" variant="primary"
                  :disabled="backgroundBusy || steamlibBusy"
                  v-b-popover.hover.top="$t('lib.addAppHint')">
          <b-icon icon="plus-square"></b-icon>
        </b-button>
        <!-- Manual Update -->
        <b-button @click="scanSteamLib" v-if="!libUpdateRequired"
                  v-b-popover.hover.top="$t('lib.updateManualHint')">
          <b-icon icon="arrow-clockwise"></b-icon>
        </b-button>
        <!-- Update Prompt -->
        <b-button @click="applyScannedLib" variant="success" v-if="libUpdateRequired"
                  v-b-popover.hover.top="$t('lib.updateHint')">
          <b-icon icon="arrow-clockwise" animation="spin"></b-icon>
          <span class="ml-2">{{ $t('lib.update') }}</span>
        </b-button>
        <!-- Filter Icon -->
        <b-input-group-text>
          <!-- Background Busy Indicator -->
          <b-spinner class="ml-2" small v-if="backgroundBusy"></b-spinner>
          <span class="ml-2" v-if="backgroundBusy">{{ $t('lib.bgSearch') }}</span>
          <b-icon icon="filter" aria-hidden="true"></b-icon>
        </b-input-group-text>
      </b-input-group-prepend>

      <b-form-input v-model="textFilter" type="search" debounce="1000" :placeholder="$t('search')" spellcheck="false"
                    :class="textFilter !== '' && textFilter !== null ? 'filter-warn no-border' : 'no-border'">
      </b-form-input>

      <b-input-group-append>
        <b-button-group>
          <b-button @click="filterVr = !filterVr" :variant="filterVr ? 'dark' : ''">
            <b-icon :icon="filterVr ? 'plug-fill' : 'plug'" :variant="filterVr ? 'success' : 'white'" />
            <span class="ml-2">{{ $t('openVr') }}</span>
          </b-button>
          <b-button @click="filterInstalled = !filterInstalled" :variant="filterInstalled ? 'dark' : ''">
            <b-icon :icon="filterInstalled ? 'square-fill' : 'square'"
                    :variant="filterInstalled ? 'success' : 'white'" />
            <span class="ml-2">{{ $t('lib.installed') }}</span>
          </b-button>
          <b-button @click="textFilter=''; filterVr=false;filterInstalled=false;" variant="secondary">
              <b-icon class="mr-2 ml-1" icon="backspace-fill" aria-hidden="true"></b-icon> {{ $t('lib.reset') }}
          </b-button>
        </b-button-group>
      </b-input-group-append>
    </b-input-group>

    <!-- Steam Library Table -->
    <b-table :items="computedList" :fields="fields" :busy="steamlibBusy"
             table-variant="dark" small borderless show-empty
             primary-key="id" class="server-list" thead-class="bg-dark text-white">
      <!-- DYNAMIC HEADER FIELD NAMES -->
      <template #head(id)>{{ $t('lib.appId') }}</template>
      <template #head(name)>{{ $t('lib.name') }}</template>
      <template #head(sizeGb)>{{ $t('lib.sizeGb') }}</template>
      <template #head(openVr)>{{ $t('openVr') }}</template>

      <!-- Name Column -->
      <template v-slot:cell(name)="row">
        <b-link @click="row.toggleDetails();updateFsr(row.item, row.detailsShowing)"
                :class="getRowLinkClass(row.item)">
          <b-icon :icon="row.detailsShowing ? 'caret-down-fill': 'caret-right-fill'" variant="secondary">
          </b-icon>
          <span class="ml-1">{{ row.item.name }}</span>
        </b-link>
      </template>

      <template v-slot:cell(openVr)="row">
        <b-icon :icon="row.item.openVr ? 'check2-square' : 'square'"></b-icon>
      </template>

      <!-- Row Details -->
      <template #row-details="row">
        <b-card :title="row.item.name"
                bg-variant="dark" text-variant="white" class="text-left m-1">
          <b-card-sub-title>
            {{ row.item.appid }} | {{ row.item.path }}
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
                                     :disabled="row.item.fsrInstalled"
                                     :options="row.item.openVrDllPaths"
                                     v-model="row.item.openVrDllPathsSelected"
              />
            </div>

            <!-- PlugIn Install / Uninstall Button -->
            <b-button :variant="row.item.fsrInstalled ? 'success' : 'primary'"
                      :disabled="row.item.openVrDllPathsSelected.length === 0"
                      @click="installFsr(row.item)" class="mr-2">
              <b-icon class="mr-1" :icon="row.item.fsrInstalled ? 'square-fill' : 'square'" />
              {{ row.item.fsrInstalled ? $t('lib.uninstallPlugin') : $t('lib.installPlugin')}}
            </b-button>

            <!-- Version Report -->
            <span v-if="row.item.fsrInstalled"
                  :class="row.item.fsrVersion !== currentFsrVersion ? 'text-warning' : ''">
              OpenVR FSR: {{ row.item.fsrVersion }}
              <template v-if="row.item.fsrVersion !== currentFsrVersion">
                <b-icon icon="info-circle-fill" v-b-popover.top.hover="$t('main.versionMismatch')" />
              </template>
              <template v-else>
                <b-icon icon="info-circle-fill" class="text-success" v-b-popover.top.hover="$t('main.versionMatch')" />
              </template>
            </span>
          </b-card-text>

          <!-- FSR Settings -->
          <template v-if="row.item.fsrInstalled">
            <h6 class="mt-4">{{ $t('lib.settingsTitle') }}</h6>
            <div class="mt-1">
              <Setting v-for="s in row.item.settings" :key="s.key" :setting="s" :app-id="row.item.id"
                       :disabled="!row.item.fsrInstalled" @setting-changed="updateFsr(row.item)"
                       class="mr-3 mb-3" />
            </div>
          </template>

          <!-- Actions -->
          <div style="position: absolute; top: 1.25rem; right: 1.25rem;">
            <template v-if="row.item.fsr_compatible !== undefined && row.item.fsr_compatible === false">
              <div class="btn btn-sm btn-warning mr-2" :id="row.item.id + '-warn'">
                OpenVR FSR {{ $t('lib.incomp') }}
              </div>
              <b-popover :target="row.item.id + '-warn'" triggers="hover">
                <template #title>{{ row.item.name }} {{ $t('lib.incompReport') }}</template>
                <span v-html="$t('lib.incompReportText')" />
              </b-popover>
            </template>
            <!-- Launch -->
            <b-button @click="launchApp(row.item)"
                      v-if="row.item.userApp === undefined || row.item.userApp === false"
                      variant="primary" size="sm">
              <b-icon variant="light" icon="play"></b-icon>
              <span class="ml-1 mr-1">{{ $t('lib.launch') }}</span>
            </b-button>
            <!-- Remove User App -->
            <b-button @click="removeUsrApp(row.item)"
                      v-if="row.item.userApp !== undefined || row.item.userApp === true"
                      variant="danger" size="sm">
              <b-icon variant="light" icon="x-square"></b-icon>
              <span class="ml-1 mr-1">{{ $t('lib.addAppRemove') }}</span>
            </b-button>
          </div>
        </b-card>
      </template>

      <!-- Empty table -->
      <template #empty>
        <div class="text-center p-4">
          <template v-if="steamlibBusy">
            <b-spinner></b-spinner>
            <p>
              {{ $t('lib.busy') }}
            </p>
          </template>
          <template v-else>
            <template v-if="Object.keys(steamApps).length !== 0">
              <p>{{ $t('lib.noResults') }}</p>
            </template>
            <template v-else>
              <p>{{ $t('lib.noLib') }}</p>
            </template>
          </template>
        </div>
      </template>
    </b-table>

    <!-- Add App modal -->
    <b-modal v-model="showAddAppModal" :title="$t('lib.addAppTitle')">
      <div v-html="$t('lib.addAppText')" />

      <b-form @submit.prevent @reset.prevent>
        <b-form-group id="input-group-1" :label="$t('lib.addAppName')" label-for="input-1"
                      :description="$t('lib.addAppNameHint')">
          <b-form-input id="input-1" v-model="addApp.name" required :placeholder="$t('lib.addAppNamePlace')" />
        </b-form-group>

        <b-form-group id="input-group-2" :label="$t('lib.addAppPath')" label-for="input-1"
                      :description="$t('lib.addAppPathHint')">
          <b-form-input id="input-2" v-model="addApp.path" required :placeholder="$t('lib.addAppPathPlace')" />
        </b-form-group>
      </b-form>
      <template #modal-footer>
        <b-button variant="primary" @click="addUsrApp">{{ $t('lib.addAppSubmit') }}</b-button>
        <b-button variant="secondary" @click="showAddAppModal=false" class="ml-2">{{ $t('lib.addAppReset') }}</b-button>
      </template>
    </b-modal>
  </div>
</template>

<script>
import {getEelJsonObject} from "@/main";
import Setting from "@/components/Setting";

export default {
  name: "SteamLibTable",
  components: {Setting},
  data: function () {
    return {
      textFilter: null, filterVr: true, filterInstalled: false,
      steamApps: {}, libUpdateRequired: false,
      steamlibBusy: false, backgroundBusy: false,
      showAddAppModal: false,
      addApp: { name: '', path: '' },
      fields: [
        { key: 'id', label: '', sortable: true, class: 'text-left' },
        { key: 'name', label: '', sortable: true, class: 'text-left' },
        { key: 'sizeGb', label: '', sortable: true, class: 'text-right' },
        { key: 'openVr', label: 'Open VR', sortable: true, class: 'text-right' },
      ],
      currentFsrVersion: '',
    }
  },
  methods: {
    isBusy: function () { return this.backgroundBusy || this.steamlibBusy },
    getRowLinkClass: function (manifest) {
      let textClass = 'text-light'
      if (manifest.fsrInstalled) {
        textClass = 'text-success'
        if (manifest.fsrVersion !== undefined) {
          if (manifest.fsrVersion !== this.currentFsrVersion) { textClass = 'text-warning' }
        }
      }
      return textClass
    },
    loadSteamLib: async function() {
      if (this.isBusy()) { return }
      // Load Steam Lib from disk if available
      this.steamlibBusy = true
      const r = await getEelJsonObject(window.eel.load_steam_lib()())
      if (!r.result) {
        this.$eventHub.$emit('make-toast',
            'Could not load Steam Library!', 'danger', 'Steam Library', true, -1)
      } else {
        this.steamApps = r.data
      }
      // Set un-busy if actual data returned
      if (Object.keys(this.steamApps).length !== 0) { this.steamlibBusy = false }
    },
    scanSteamLib: async function() {
      if (this.backgroundBusy) { return }
      // Scan the disk in the background
      this.backgroundBusy = true
      const r = await getEelJsonObject(window.eel.get_steam_lib()())
      if (!r.result) {
        this.$eventHub.$emit('make-toast',
            'Could not load Steam Library!', 'danger', 'Steam Library', true, -1)
      } else {
        if (Object.keys(this.steamApps).length !== 0) {
          // Keep the scan results and prompt the user to update
          this.libUpdateRequired = true
        } else {
          // No disk cache was present or empty
          this.steamApps = r.data
        }
      }
      this.backgroundBusy = false; this.steamlibBusy = false
    },
    applyScannedLib: async function() { await this.loadSteamLib(); this.libUpdateRequired = false },
    filterEntries: function (tableData) {
      let filterText = ''
      let filteredList = []
      if (this.textFilter !== null) { filterText = this.textFilter.toLowerCase() }

      tableData.forEach(rowItem => {
        // Button Filter
        if (this.filterVr && !rowItem.openVr) { return }
        if (this.filterInstalled && !rowItem.fsrInstalled) { return }

        // Text Filter
        if (filterText === '') { filteredList.push(rowItem); return }
        if (rowItem.name.toLowerCase().includes(filterText)) { filteredList.push(rowItem) }
      })

      return filteredList
    },
    launchApp: async function(manifest) {
      this.$eventHub.$emit('set-busy', true)
      const r = await getEelJsonObject(window.eel.launch_app(manifest)())
      if (!r.result) {
        this.$eventHub.$emit('make-toast', r.msg, 'danger', 'Launch', true, -1)
      } else {
        this.$eventHub.$emit('make-toast', r.msg, 'success', false, 1200)
      }
      this.$eventHub.$emit('set-busy', false)
    },
    addUsrApp: async function() {
      if (this.isBusy()) { return }
      this.$eventHub.$emit('set-busy', true)
      this.showAddAppModal = false
      const r = await getEelJsonObject(window.eel.add_custom_app(this.addApp)())
      if (!r.result) {
        // Error
        this.$eventHub.$emit('make-toast',
            'Error adding custom app entry: ' + r.msg, 'danger', 'Add App Entry', true, -1)
      } else {
        // Success
        await this.loadSteamLib()
        this.textFilter = this.addApp.name
      }

      this.addApp = { name: '', path: '' }
      this.$eventHub.$emit('set-busy', false)
    },
    removeUsrApp: async function(app) {
      if (this.isBusy()) { return }
      const r = await getEelJsonObject(window.eel.remove_custom_app(app)())
      if (!r.result) {
        // Error
        this.$eventHub.$emit('make-toast',
            'Error removing app entry: ' + r.msg, 'danger', 'Remove App Entry', true, -1)
      } else {
        await this.loadSteamLib()
      }
    },
    updateFsr: async function (manifest, rowNotExpanded=false) {
      if (this.isBusy()) { return }
      if (rowNotExpanded) { return }
      this.$eventHub.$emit('set-busy', true)
      const r = await getEelJsonObject(window.eel.update_fsr(manifest)())
      if (!r.result) {
        this.$eventHub.$emit('make-toast', r.msg, 'danger', 'PlugIn Installation', true, -1)
      } else {
        // this.$eventHub.$emit('make-toast', 'Updated Fsr Cfg for ' + manifest.name, 'success', manifest.name,
        //  false, 1200)

        // Update Entry
        manifest.settings = r.manifest.settings
        manifest.fsrVersion = r.manifest.fsrVersion
      }

      // Update disk cache
      await window.eel.save_steam_lib(this.steamApps)()
      this.$eventHub.$emit('set-busy', false)
    },
    installFsr: async function (manifest) {
      if (this.isBusy()) { return }
      this.$eventHub.$emit('set-busy', true)
      let r = {}
      if (manifest.fsrInstalled) {
        r = await getEelJsonObject(window.eel.uninstall_fsr(manifest)())
      } else {
        r = await getEelJsonObject(window.eel.install_fsr(manifest)())
      }

      if (!r.result) {
        this.$eventHub.$emit('make-toast',
            r.msg, 'danger', 'PlugIn Installation', true, -1)
      } else {
        // Update settings
        manifest.settings = r.manifest.settings

        // Update install state
        manifest.fsrInstalled = !manifest.fsrInstalled
        if (manifest.fsrInstalled) {
          this.$eventHub.$emit('make-toast', 'Installed PlugIn to ' + manifest.name, 'success',
              'PlugIn Installed')
        } else {
          this.$eventHub.$emit('make-toast', 'Uninstalled PlugIn from ' + manifest.name, 'success',
          'PlugIn Uninstalled')
        }

        // Update FSR version
        manifest.fsrVersion = r.manifest.fsrVersion

        // Update disk cache
        await window.eel.save_steam_lib(this.steamApps)()
      }
      this.$eventHub.$emit('set-busy', false)
    },
  },
  computed: {
    computedList() {
      let steamTableData = []
      for (const appId in this.steamApps) {
        const entry = this.steamApps[appId]
        entry['id'] = appId
        steamTableData.push(entry)
      }
      return this.filterEntries(steamTableData)
    }
  },
  async mounted() {
    await this.loadSteamLib()
    this.currentFsrVersion = await window.eel.get_current_fsr_version()()
    console.log('Current FSR App compatible version:', this.currentFsrVersion)
    if (Object.keys(this.steamApps).length === 0) {
      await this.scanSteamLib()
    }
  }
}
</script>

<style scoped>

</style>