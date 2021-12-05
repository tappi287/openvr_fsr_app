<template>
  <div id="main" class="text-left">
    <b-navbar type="dark" class="pl-0 pr-0">
      <b-navbar-brand href="#" class="mr-2">
        <b-img width="32px" key="1" src="@/assets/app_logo_inkscape.svg"></b-img>
      </b-navbar-brand>
      <h4 class="mt-2">OpenVR FSR App v{{ version }}</h4>

      <b-navbar-nav class="ml-auto">
        <!-- Folder -->
        <!-- FSR Folder Select -->
        <b-button variant="secondary" size="sm" id="fsr-folder">
          <b-icon icon="folder-fill"></b-icon>
        </b-button>

        <!-- Folder Select Message Hover -->
        <b-popover target="fsr-folder" triggers="hover">
          <template v-if="openFsrDir !== null">
            <span v-html="$t('main.folderSelect', { folder: openFsrDir })" />
          </template>
          <template v-else>
            <span v-html="$t('main.folderSelectError')" />
          </template>
        </b-popover>

        <!-- Folder Select Popover -->
        <b-popover target="fsr-folder" triggers="click">
          <h5>{{ $t('main.folderPop') }}</h5>
          <p v-html="$t('main.folderPopText')" />
          <b-form-input size="sm" v-model="fsrDirInput"
                        :placeholder="$t('main.folderPopHint')">
          </b-form-input>
          <div class="text-right mt-1">
            <b-button @click="setFsrDir" size="sm" variant="primary"
                      aria-label="Save">
              {{ $t('main.folderPopUpdate') }}
            </b-button>
            <b-button @click="resetFsrDir" size="sm" variant="warning"
                      class="ml-2">
              {{ $t('main.folderPopReset') }}
            </b-button>
            <b-button @click="$root.$emit('bv::hide::popover', 'fsr-folder')"
                      size="sm" aria-label="Close" class="ml-2">
              {{ $t('main.folderPopClose') }}
            </b-button>
          </div>
        </b-popover>

        <!-- Info Toggle -->
        <b-button size="sm" variant="secondary" v-b-toggle.info-collapse class="ml-2">
          <b-icon icon="info-square-fill" />
        </b-button>

        <!-- Languages -->
        <LanguageSwitcher class="ml-2" />
      </b-navbar-nav>
    </b-navbar>

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
      fsrDirInput: '',
      openFsrDir: null,
      version: version,
      isBusy: false,
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
    getFsrDir: async function () {
      const r = await window.eel.get_fsr_dir()()
      if (r !== undefined) { this.openFsrDir = r }
    },
    resetFsrDir: async function() {
      this.fsrDirInput = ''
      await this.setFsrDir()
    },
    setFsrDir: async function () {
      const r = await getEelJsonObject(window.eel.set_fsr_dir(this.fsrDirInput)())

      if (r !== undefined && r.result) {
        await this.getFsrDir()
        this.makeToast('Updated OpenVR FSR directory to: ' + this.openFsrDir, 'success')
      } else {
        this.makeToast('Could not update OpenVR FSR directory. Provided path does not exists, ' +
            'is not accessible or does not contain the PlugIn Dll and cfg file.', 'danger')
        await this.getFsrDir()
      }
      this.$root.$emit('bv::hide::popover', 'fsr-folder')
    },
    setError: async function (error) { this.$emit('error', error) },
  },
  computed: {
  },
  async created() {
    this.$eventHub.$on('make-toast', this.makeToast)
    this.$eventHub.$on('set-busy', this.setBusy)
    await this.getFsrDir()
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
