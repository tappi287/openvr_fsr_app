<template>
  <div>
    <!-- Filter -->
    <b-input-group size="md" class="mt-2">
      <b-input-group-prepend>
        <b-input-group-text><b-icon icon="filter" aria-hidden="true"></b-icon></b-input-group-text>
      </b-input-group-prepend>

      <b-form-input v-model="textFilter" type="search" debounce="1000" placeholder="Search..." spellcheck="false"
                    :class="textFilter !== '' && textFilter !== null ? 'filter-warn no-border' : 'no-border'">
      </b-form-input>

      <b-input-group-append>
        <b-button-group>
          <b-button @click="filterVr = !filterVr" :variant="filterVr ? 'dark' : ''">
            <b-icon :icon="filterVr ? 'plug-fill' : 'plug'" :variant="filterVr ? 'success' : 'white'" />
            <span class="ml-2">OpenVR</span>
          </b-button>
          <b-button @click="filterInstalled = !filterInstalled" :variant="filterInstalled ? 'dark' : ''">
            <b-icon :icon="filterInstalled ? 'square-fill' : 'square'"
                    :variant="filterInstalled ? 'success' : 'white'" />
            <span class="ml-2">Installed</span>
          </b-button>
          <b-button @click="textFilter=''; filterVr=false;filterInstalled=false;" variant="secondary">
              <b-icon class="mr-2 ml-1" icon="backspace-fill" aria-hidden="true"></b-icon>Reset
          </b-button>
        </b-button-group>
      </b-input-group-append>
    </b-input-group>

    <!-- Steam Library Table -->
    <b-table :items="computedList" :fields="fields" :busy="steamlibBusy"
             table-variant="dark" small borderless show-empty
             primary-key="id" class="server-list" thead-class="bg-dark text-white">
      <!-- Name Column -->
      <template v-slot:cell(name)="row">
        <b-link @click="row.toggleDetails()" :class="row.item.fsrInstalled ? 'text-success' : 'text-light'">
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
        <b-card :title="row.item.name" :sub-title="row.item.appid"
                bg-variant="dark" text-variant="white" class="text-left m-1">

          <b-card-text>
            {{ row.item.path }}<br />
            <p v-for="p in row.item.openVrDllPaths" :key="p" class="m-0">
              {{ p }}
            </p>
          </b-card-text>
          <b-button :variant="row.item.fsrInstalled ? 'success' : 'primary'"
                    @click="installFsr(row.item)">
            {{ row.item.fsrInstalled ? 'Uninstall PlugIn' : 'Install PlugIn'}}
          </b-button>
          <div class="mt-2">
            <Setting v-for="s in row.item.settings" :key="s.key" :setting="s" :app-id="row.item.id"
                     :disabled="!row.item.fsrInstalled" @setting-changed="updateFsr(row.item)"
                     class="mr-3 mb-3" />
          </div>

          <!-- Actions -->
          <div style="position: absolute; top: 1.25rem; right: 1.25rem;">
            <template v-if="row.item.fsr_compatible !== undefined && row.item.fsr_compatible === false">
              <div class="btn btn-sm btn-warning mr-2" :id="row.item.id + '-warn'">
                OpenVR FSR Incompatible
              </div>
              <b-popover :target="row.item.id + '-warn'" triggers="hover">
                <template #title>{{ row.item.name }} Compatibility Report</template>
                This app was reported to be not compatible with the way the OpenVr Fsr PlugIn injects itself into
                the render pipeline.<br/><br/>
                In case you run into issues, the log file (openvr_mod.log) may provide clues to what's going on.
                Report errors and consult this page for troubleshooting:<br/><br/>
                <b-link href="https://github.com/fholger/openvr_fsr/issues" target="_blank">
                  https://github.com/fholger/openvr_fsr/issues
                </b-link>
              </b-popover>
            </template>
            <b-button @click="launchApp(row.item)"
                      variant="primary" size="sm">
              <b-icon variant="light" icon="play"></b-icon>
              <span class="ml-1 mr-1">Launch Steam App</span>
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
              Steam library is being scanned ...
            </p>
          </template>
          <template v-else>
            <p>Steam library could not be found.</p>
          </template>
        </div>
      </template>
    </b-table>
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
      steamApps: {}, steamlibBusy: false,
      fields: [
        { key: 'id', label: 'App Id', sortable: true, class: 'text-left' },
        { key: 'name', label: 'Name', sortable: true, class: 'text-left' },
        { key: 'sizeGb', label: 'Size', sortable: true, class: 'text-right' },
        { key: 'openVr', label: 'Open VR', sortable: true, class: 'text-right' },
      ],
    }
  },
  methods: {
    getSteamLib: async function() {
      // this.$eventHub.$emit('set-busy', true)
      this.steamlibBusy = true
      const r = await getEelJsonObject(window.eel.get_steam_lib()())
      if (!r.result) {
        this.$eventHub.$emit('make-toast',
            'Could not load Steam Library!', 'danger', 'Steam Library', true, -1)
      } else {
        this.steamApps = r.data
      }
      // this.$eventHub.$emit('set-busy', false)
      this.steamlibBusy = false
    },
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
    updateFsr: async function (manifest) {
      this.$eventHub.$emit('set-busy', true)
      const r = await getEelJsonObject(window.eel.update_fsr(manifest)())
      if (!r.result) {
        this.$eventHub.$emit('make-toast', r.msg, 'danger', 'PlugIn Installation', true, -1)
      } else {
        this.$eventHub.$emit('make-toast', 'Updated Fsr Cfg for ' + manifest.name, 'success',
            false, 1200)
      }
      this.$eventHub.$emit('set-busy', false)
    },
    installFsr: async function (manifest) {
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
        manifest.fsrInstalled = !manifest.fsrInstalled
        if (manifest.fsrInstalled) {
          this.$eventHub.$emit('make-toast', 'Installed PlugIn to ' + manifest.name, 'success',
              'PlugIn Installed')
        } else {
          this.$eventHub.$emit('make-toast', 'Uninstalled PlugIn from ' + manifest.name, 'success',
          'PlugIn Uninstalled')
        }
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
    await this.getSteamLib()
  }
}
</script>

<style scoped>

</style>