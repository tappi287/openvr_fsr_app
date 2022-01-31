<template>
  <div>
    <!-- Filter -->
    <b-input-group size="sm" class="mt-2">
      <b-input-group-prepend>
        <!-- Add User App -->
        <b-button @click="showAddAppModal=!showAddAppModal" variant="primary"
                  :disabled="backgroundBusy || steamlibBusy"
                  v-b-popover.hover.top="$t('lib.addAppHint')">
          <b-iconstack>
            <b-icon stacked icon="app-indicator"></b-icon>
            <b-icon stacked icon="plus"></b-icon>
          </b-iconstack>
        </b-button>
        <!-- Add User Dir -->
        <b-button @click="$eventHub.$emit('toggle-dir-manager', false, true)" variant="primary"
                  :disabled="backgroundBusy || steamlibBusy"
                  v-b-popover.hover.top="$t('lib.addAppDirHint')">
          <b-icon icon="folder-plus"></b-icon>
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
          <span class="ml-2" v-if="backgroundBusy">{{ steamLibBusyMessage }}</span>
          <b-icon icon="filter" aria-hidden="true"></b-icon>
        </b-input-group-text>
      </b-input-group-prepend>

      <b-form-input v-model="textFilter" type="search" debounce="1000" :placeholder="$t('search')" spellcheck="false"
                    :class="textFilter !== '' && textFilter !== null ? 'filter-warn no-border' : 'no-border'">
      </b-form-input>

      <b-input-group-append>
        <b-button-group size="sm">
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
             :sort-by.sync="sortBy" :sort-desc.sync="sortDesc"
             table-variant="dark" small borderless show-empty sort-icon-left
             primary-key="id" class="server-list" thead-class="bg-dark text-white">
      <!-- DYNAMIC HEADER FIELD NAMES -->
      <template #head(id)>{{ $t('lib.appId') }}</template>
      <template #head(name)>{{ $t('lib.name') }}</template>
      <template #head(sizeGb)>{{ $t('lib.sizeGb') }}</template>
      <template #head(openVr)>{{ $t('openVr') }}</template>

      <!-- Name Column -->
      <template v-slot:cell(name)="row">
        <b-link @click="row.toggleDetails()"
                :class="getRowLinkClass(row.item)">
          <b-icon :icon="row.detailsShowing ? 'caret-down-fill': 'caret-right-fill'" variant="secondary">
          </b-icon>
          <span class="ml-1">{{ row.item.name }}</span>
        </b-link>
      </template>

      <!-- Mod Column -->
      <template v-slot:cell(mod)="row">
        <span :class="getRowModInfo(row.item).version ? '' : 'text-warning'"
              v-if="getRowModInfo(row.item).text !== ''">
          {{ getRowModInfo(row.item).text }}
          <template v-if="getRowModInfo(row.item).version">
            <b-icon icon="info-circle-fill" class="text-success" v-b-popover.top.hover="$t('main.versionMatch')" />
          </template>
          <template v-else>
            <b-icon icon="info-circle-fill" v-b-popover.top.hover="$t('main.versionMismatch')" />
          </template>
        </span>
      </template>

      <!-- OpenVR Column -->
      <template v-slot:cell(openVr)="row">
        <b-icon :icon="row.item.openVr ? 'check2-square' : 'square'"></b-icon>
      </template>

      <!-- Size Column -->
      <template v-slot:cell(sizeGb)="row">
        <span v-if="row.item.sizeGb !== '0.0 GB' && row.item.sizeGb !== '0' && row.item.sizeGb !== 0">
          {{ row.item.sizeGb }}
        </span>
      </template>

      <!-- Row Details -->
      <template #row-details="row">
        <EntryDetails :entry="steamApps[row.item.appid]"
                      :current-fsr-version="currentFsrVersion"
                      :current-fov-version="currentFovVersion"
                      :current-vrp-version="currentVrpVersion"
                      :steam-lib-busy="tableBusy"
                      @entry-updated="saveSteamApps"
                      @load-steam-lib="loadSteamLib"
        />
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
import EntryDetails from "@/components/EntryDetails";


export default {
  name: "SteamLibTable",
  components: {EntryDetails},
  data: function () {
    return {
      textFilter: null, filterVr: false, filterInstalled: false,
      steamApps: {}, libUpdateRequired: false, reScanRequired: false,
      steamlibBusy: false, backgroundBusy: false,
      showAddAppModal: false, showAddDirModal: false,
      addApp: { name: '', path: '' },
      addDir: 'name',
      sortBy: 'name', sortDesc: false,
      fields: [
        { key: 'id', label: '', sortable: true, class: 'text-left' },
        { key: 'name', label: '', sortable: true, class: 'text-left' },
        { key: 'mod', label: 'Mod', sortable: false, class: 'text-right' },
        { key: 'sizeGb', label: '', sortable: true, class: 'text-right' },
        { key: 'openVr', label: 'Open VR', sortable: true, class: 'text-right' },
      ],
      currentFsrVersion: '', currentFovVersion: '', currentVrpVersion: '',
      progressMessage: ''
    }
  },
  methods: {
    isBusy: function () { return this.backgroundBusy || this.steamlibBusy },
    setProgressMessage: function (message) {
      // Set progress message
      this.progressMessage = message

      // Clear after timeout
      setTimeout(() => {
        this.setProgressMessage('')
      }, 10000)
    },
    updateTableSort(sortByRow = 'name', descending = false) {
      this.sortBy = sortByRow; this.sortDesc = descending
    },
    getRowLinkClass: function (manifest) {
      let textClass = 'text-light'
      if (manifest.fsrInstalled) {
        textClass = 'text-success'
        if (manifest.fsrVersion !== undefined) {
          if (manifest.fsrVersion !== this.currentFsrVersion) { textClass = 'text-warning' }
        }
      } else if (manifest.fovInstalled) {
        textClass = 'text-success'
        if (manifest.fovVersion !== undefined) {
          if (manifest.fovVersion !== this.currentFovVersion) { textClass = 'text-warning' }
        }
      } else if (manifest.vrpInstalled) {
        textClass = 'text-success'
        if (manifest.vrpVersion !== undefined) {
          if (manifest.vrpVersion !== this.currentVrpVersion) { textClass = 'text-warning' }
        }
      }
      return textClass
    },
    getRowModInfo: function (manifest) {
      if (manifest.fsrInstalled) {
        if (manifest.fsrVersion !== undefined) {
          return {text: 'FSR ' + manifest.fsrVersion, version: manifest.fsrVersion === this.currentFsrVersion}
        }
      } else if (manifest.fovInstalled) {
        if (manifest.fovVersion !== undefined) {
          return {text: 'Foveated ' + manifest.fovVersion, version: manifest.fovVersion === this.currentFovVersion}
        }
      } else if (manifest.vrpInstalled) {
        if (manifest.vrpVersion !== undefined) {
          return {text: 'VrPerfKit ' + manifest.vrpVersion, version: manifest.vrpVersion === this.currentVrpVersion}
        }
      }
      return {text: '', version: false}
    },
    saveSteamApps: async function() {
      this.$eventHub.$emit('set-busy', true)
      await window.eel.save_steam_lib(this.steamApps)()
      this.$eventHub.$emit('set-busy', false)
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
        this.reScanRequired = r.reScanRequired
      }

      // Set un-busy if actual data returned
      if (Object.keys(this.steamApps).length !== 0) { this.steamlibBusy = false }
    },
    scanSteamLib: async function() {
      if (this.backgroundBusy) { return }
      // Scan the disk in the background
      this.backgroundBusy = true
      const r = await getEelJsonObject(window.eel.scan_app_lib()())
      this.$eventHub.$emit('update-progress', '')

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
        if (this.filterInstalled && !rowItem.fsrInstalled && !rowItem.fovInstalled && !rowItem.vrpInstalled) { return }

        // Text Filter
        if (filterText === '') { filteredList.push(rowItem); return }
        if (rowItem.name.toLowerCase().includes(filterText)) { filteredList.push(rowItem) }
      })

      return filteredList
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
    }
  },
  computed: {
    tableBusy() {
      return this.isBusy()
    },
    steamLibBusyMessage() {
      if (this.progressMessage !== '') {
        return this.$t('lib.bgSearchPre') + this.progressMessage + ' ...'
      }
      return this.$t('lib.bgSearch')
    },
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
  created() {
    this.$eventHub.$on('reload-steam-lib', this.loadSteamLib)
    this.$eventHub.$on('sort-steam-lib', this.updateTableSort)
    this.$eventHub.$on('update-progress', this.setProgressMessage)
  },
  async mounted() {
    await this.loadSteamLib()
    this.currentFsrVersion = await window.eel.get_current_fsr_version()()
    this.currentFovVersion = await window.eel.get_current_foveated_version()()
    this.currentVrpVersion = await window.eel.get_current_vrperfkit_version()()
    if (Object.keys(this.steamApps).length === 0 || this.reScanRequired) {
      await this.scanSteamLib()
    }
  },
  destroyed() {
    this.$eventHub.$off('reload-steam-lib')
    this.$eventHub.$off('sort-steam-lib')
    this.$eventHub.$off('update-progress')
  }
}
</script>

<style scoped>

</style>