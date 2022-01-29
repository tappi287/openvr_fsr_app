<template>
  <div id="main" class="text-left">
    <b-navbar type="dark" class="pl-0 pr-0 mt-0 mb-2">
      <b-navbar-brand class="mr-2" tag="div">
        <b-img width="32px" key="1" src="@/assets/app_logo_inkscape.svg"></b-img>
      </b-navbar-brand>
      <b-navbar-brand class="mr-2" tag="div">
        <span class="app-title">{{ appName }} v{{ version }}</span>
      </b-navbar-brand>

      <b-navbar-nav class="ml-auto" small>
        <!-- Folder Management -->
        <b-button variant="secondary" size="sm" class="mr-2" @click="toggleDirModal"
                  v-b-popover.hover.top="$t('main.folderSelectClick')">
          <b-icon class="text-primary" icon="folder-fill"></b-icon>
        </b-button>

        <!-- Folder Select Popover -->
        <b-popover target="mod-folder" triggers="click">

        </b-popover>

        <!-- Info Toggle -->
        <b-button size="sm" variant="secondary" class="mr-2" v-b-toggle.info-collapse>
          <b-icon icon="info-square-fill" />
        </b-button>

        <!-- Languages -->
        <LanguageSwitcher />
      </b-navbar-nav>
    </b-navbar>

    <!-- Dirs modal -->
    <b-modal v-model="showDirModal" :title="$t('main.dirModTitle')">
      <!-- Mod source directories -->
      <b-card class="mb-4" header="Default">
        <template #header><h5 v-html="$t('main.folderPop')"></h5></template>

        <div class="mb-3 d-flex flex-row justify-content-between">
          <div class="d-inline-flex p-2">{{ $t('main.folderPopSelect') }}</div>

          <b-dropdown :text="modNames[selectedModType]" size="sm" class="d-inline-flex">
            <b-dropdown-item v-for="modType in modTypes" :key="modType" @click="selectedModType = modType">
              {{ modNames[modType] }}
            </b-dropdown-item>
          </b-dropdown>
        </div>

        <div class="p-2">
          <p v-html="$t('main.folderPopText')" />
          <p><span v-html="$t('main.folderPopCurrent')" /><i>{{ modDataDirs[selectedModType] }}</i></p>
          <b-form-input size="sm" v-model="modDirInput"
                        :placeholder="$t('main.folderPopHint')">
          </b-form-input>
        </div>

        <template #footer>
          <!-- Buttons -->
          <div class="text-right mt-1">
            <b-button @click="setModDir(selectedModType)" size="sm" variant="primary"
                      aria-label="Save">
              {{ $t('main.folderPopUpdate') }}
            </b-button>
            <b-button @click="resetModDir(selectedModType)" size="sm" variant="warning"
                      class="ml-2">
              {{ $t('main.folderPopReset') }}
            </b-button>
          </div>
        </template>
      </b-card>

      <!-- Custom Library directories -->
      <b-card header="Default">
        <template #header><h5 v-html="$t('main.dirModLibs')"></h5></template>
        <template v-if="customDirs.length !== 0">
          <div v-for="d in customDirs" :key="d.id">
            {{ d.path }}
          </div>
        </template>
        <template v-else>
          <div>None</div>
        </template>
      </b-card>

      <!-- Modal Footer -->
      <template #modal-footer>
        <b-button variant="secondary" size="sm" @click="showDirModal=false">
          {{ $t('main.folderPopClose') }}
        </b-button>
      </template>
    </b-modal>

    <!-- Info -->
    <b-collapse id="info-collapse">
      <b-card class="setting-card mt-3" bg-variant="dark" text-variant="white" footer-class="pt-0">
        <p>
          {{ $t('main.infoDesc1') }}
          <b-link href="https://github.com/fholger/openvr_fsr#modified-openvr-dll-with-amd-fidelityfx-superresolution-upscaler"
                  target="_blank">
            {{ $t('main.infoDesc2') }}
          </b-link>
          {{ $t('main.infoDesc3') }}
        </p>
        <p>
          <span v-html="$t('main.infoDesc4')"></span> <b-icon icon="emoji-sunglasses-fill" />.
        </p>
        <h5 class="mt-4 text-primary">{{ $t('main.install') }}</h5>
        <p v-html="$t('main.installText')" />

        <h5 class="mt-4 text-primary">{{ $t('main.installLoc') }}</h5>
        <p v-html="$t('main.installLocText')" />

        <h3 class="mt-5 text-primary">{{ $t('main.plugIn') }}</h3>
        <h5 class="text-info">{{ $t('main.renderScale') }}</h5>
        <p v-html="$t('main.renderScaleText')">
          <!-- will be overwritten by translation -->
        </p>
        <h5 class="mt-4 text-info">{{ $t('main.sharp') }}</h5><p>{{ $t('main.sharpText') }}</p>
        <h5 class="mt-4 text-info">{{ $t('main.radius') }}</h5>
        <p v-html="$t('main.radiusText')">
        </p>
        <h5 class="mt-4 text-info">{{ $t('main.mip') }}</h5>
        <p v-html="$t('main.mipText')"/>
        <h5 class="mt-4 text-info">{{ $t('main.debug') }}</h5>
        <p v-html="$t('main.debugText')" />
      </b-card>
    </b-collapse>

    <!-- Steam Library -->
    <SteamLibTable class="mt-1"></SteamLibTable>

    <!-- Footer -->
    <Footer class="mt-4"></Footer>

    <!-- Busy Overlay -->
    <b-overlay no-wrap fixed :show="isBusy" blur="1px" variant="dark" rounded>
      <b-spinner></b-spinner>
    </b-overlay>
  </div>
</template>

<script>

import SteamLibTable from "@/components/SteamLibTable";
import {getEelJsonObject} from "@/main";
import Footer from "@/components/Footer";
import {version} from '../../package.json';
import LanguageSwitcher from "@/components/LanguageSwitcher";

export default {
  name: 'Main',
  data: function () {
    return {
      modDirInput: '',
      modDataDirs: {0: null, 1: null, 2: null},
      userAppDirs: {}, showDirModal: false,
      selectedModType: 0,
      modTypes: [0, 1, 2],
      modNames: {0: 'Open VR FSR', 1: 'Open VR Foveated', 2: 'VR Performance Toolkit'},
      version: version,
      isBusy: false,
      appName: process.env.VUE_APP_FRIENDLY_NAME,
    }
  },
  methods: {
    makeToast(message, category = 'secondary', title = 'Update', append = true, delay = 8000) {
      let autoHideDisabled = false
      if (delay <= 0) { autoHideDisabled = true }

      this.$bvToast.toast(message, {
        title: title,
        autoHideDelay: delay,
        appendToast: append,
        variant: category,
        noAutoHide: autoHideDisabled,
        solid: true,
      })
    },
    setBusy: function (busy) { this.isBusy = busy},
    toggleDirModal: async function() {
      await this.getCustomDirs()
      this.showDirModal = !this.showDirModal
    },
    getCustomDirs: async function () {
      const r = await window.eel.get_custom_dirs()()
      if (r !== undefined) { this.userAppDirs = r }
    },
    getModDir: async function (modType = 0) {
      const r = await window.eel.get_mod_dir(modType)()
      if (r !== undefined) { this.modDataDirs[modType] = r }
    },
    resetModDir: async function(modType = 0) {
      modType = Number(modType)
      this.modDirInput = ''
      await this.setModDir(modType)
      this.showDirModal = false
    },
    setModDir: async function (modType) {
      const r = await getEelJsonObject(window.eel.set_mod_dir(this.modDirInput, modType)())

      if (r !== undefined && r.result) {
        await this.getModDir(modType)
        this.makeToast('Updated ' + this.modNames[modType] + ' directory to: ' + this.modDataDirs[modType],
            'success', this.modNames[modType])
      } else {
        this.makeToast('Could not update Mod source directory. Provided path does not exists, ' +
            'is not accessible or does not contain the PlugIn Dll and cfg file.',
            'danger', this.modNames[modType])
        await this.getModDir(modType)
      }
      this.showDirModal = false
    },
    setError: async function (error) { this.$emit('error', error) },
  },
  computed: {
    customDirs: function () {
      let appDirArray = []
      for (const key in this.userAppDirs) {
         appDirArray.push({'id': key, 'path': this.userAppDirs[key]})
      }
      return appDirArray
    },
  },
  async created() {
    this.$eventHub.$on('make-toast', this.makeToast)
    this.$eventHub.$on('set-busy', this.setBusy)
    for (const modType in this.modTypes) {
      await this.getModDir(Number(modType))
    }
  },
  beforeDestroy() {
    this.$eventHub.$off('make-toast')
    this.$eventHub.$off('set-busy')
  },
  components: {
    LanguageSwitcher,
    Footer,
    SteamLibTable
  },
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style>
#main {
  width: 96%;
  margin: 0 auto 0 auto;
}
</style>
