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
        <b-button variant="secondary" size="sm" class="mr-2" @click="toggleDirManager"
                  v-b-popover.hover.top="$t('main.folderSelectClick')">
          <b-icon class="text-dark" icon="folder-fill"></b-icon>
        </b-button>

        <!-- Info Toggle -->
        <b-button size="sm" variant="secondary" class="mr-2" v-b-toggle.info-collapse>
          <b-icon icon="info-square-fill" />
        </b-button>

        <!-- Languages -->
        <LanguageSwitcher />
      </b-navbar-nav>
    </b-navbar>

    <!-- Dir Manager Modal -->
    <b-modal size="lg" v-model="showDirManager" hide-header>
      <DirManager :show-mod-dir="showDirManagerMod"
                  :show-custom-dir="showDirManagerCustom">
      </DirManager>

      <!-- Modal Footer -->
      <template #modal-footer>
        <b-button variant="secondary" size="sm" @click="showDirManager=false">
          {{ $t('main.folderPopClose') }}
        </b-button>
      </template>
    </b-modal>

    <!-- Info -->
    <b-collapse id="info-collapse">
      <b-card class="setting-card mt-3" bg-variant="dark" text-variant="white" footer-class="pt-0">
        <p>
          {{ $t('main.infoDesc1') }}
          <b-link href="https://github.com/fholger/openvr_fsr"
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
      <template #overlay>
        <div class="text-center">
          <b-spinner></b-spinner>
          <template v-if="progressMessage !== ''">
            <div></div>
            <span class="mt-4">{{ progressMessage }}</span>
          </template>
        </div>
      </template>
    </b-overlay>
  </div>
</template>

<script>

import SteamLibTable from "@/components/SteamLibTable";
import Footer from "@/components/Footer";
import {version} from '../../package.json';
import LanguageSwitcher from "@/components/LanguageSwitcher";
import DirManager from "@/components/DirManager";

export default {
  name: 'Main',
  data: function () {
    return {
      showDirManager: false, showDirManagerMod: true, showDirManagerCustom: true,
      version: version,
      isBusy: false, progressMessage: '',
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
    setProgressMessage: function (message) {
      // Set progress message
      this.progressMessage = message

      // Clear after timeout
      setTimeout(() => {
        this.setProgressMessage('')
      }, 15000)
    },
    toggleDirManager: function (showMod = true, showCustom = true) {
      this.showDirManagerMod = showMod; this.showDirManagerCustom = showCustom
      this.showDirManager = !this.showDirManager
    },
    setBusy: function (busy) { this.isBusy = busy},
    setError: async function (error) { this.$emit('error', error) },
  },
  computed: {
  },
  async created() {
    this.$eventHub.$on('make-toast', this.makeToast)
    this.$eventHub.$on('set-busy', this.setBusy)
    this.$eventHub.$on('toggle-dir-manager', this.toggleDirManager)
    this.$eventHub.$on('update-progress', this.setProgressMessage)
  },
  beforeDestroy() {
    this.$eventHub.$off('make-toast')
    this.$eventHub.$off('set-busy')
    this.$eventHub.$off('toggle-dir-manager')
    this.$eventHub.$off('update-progress')
  },
  components: {
    DirManager,
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
