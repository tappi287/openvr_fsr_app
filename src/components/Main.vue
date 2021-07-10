<template>
  <div id="main" class="text-left">
    <div>
      <b-img width="32px" key="1" src="@/assets/app_logo_inkscape.svg" class="float-left"></b-img>
      <h4 class="display-inline pl-5 mt-3">OpenVR FSR App</h4>
    </div>

    <!-- Info -->
    <b-button size="sm" variant="secondary" v-b-toggle.info-collapse
              style="position: absolute; top: 0.75rem; right: 0.75rem;">
      <b-icon icon="info-square-fill" />
    </b-button>
    <b-collapse id="info-collapse">
      <b-card class="setting-card mt-3" bg-variant="dark" text-variant="white" footer-class="pt-0">
        <p>Browse through your Steam library, let this app install the
          <b-link href="https://github.com/fholger/openvr_fsr#modified-openvr-dll-with-amd-fidelityfx-superresolution-upscaler"
                  target="_blank">
            Modified OpenVR DLL with AMD FidelityFX SuperResolution Upscaler
          </b-link>
        and adjust the plugin settings per app.</p>
        <p>
          <b>Note:</b> This app has absolutely no knowledge which Steam apps work with the FSR PlugIn.
          But this app might be the quickest way to find out <b-icon icon="emoji-sunglasses-fill" />
        </p>
        <h5>Installation</h5>
        <p>
          Hit the <i>install plugin</i> button in the menu for your Steam app of choice.
          That will enable AMD FidelityFX Super Resolution.
        </p>
        <h5>Render Scale</h5>
        <p>
          Per-dimension render scale. If smaller than 1 / 100%, will lower the game's render resolution
          accordingly and afterwards upscale to the "native" resolution set in SteamVR.<br />
          If greater than 1 / 100%, the game will render at its "native" resolution, and afterwards the
          image is upscaled to a higher resolution as per the given value.<br />
          If equals 1 / 100%, effectively disables upsampling, but you'll still get the sharpening stage.<br /><br />
          AMD presets:<br />
          Ultra Quality => 0.77<br />
          Quality       => 0.67<br />
          Balanced      => 0.59<br />
          Performance   => 0.50<br />
        </p>
      </b-card>
    </b-collapse>

    <!-- Folder -->
    <div class="text-center mt-3">
      <!-- FSR Folder Select -->
      <b-button variant="secondary" size="sm" id="fsr-folder" v-b-popover.hover.auto="'Customize PlugIn source path.'">
        <b-icon icon="folder-fill"></b-icon>
      </b-button>

      <span class="ml-2">
        <template v-if="openFsrDir !== null">
          OpenVR FSR found at <i>{{ openFsrDir }}</i>
        </template>
        <template v-else>
          <b>OpenVR FSR PlugIn not found!</b> Download
          <b-link href="https://github.com/fholger/openvr_fsr/releases/latest" target="_blank">OpenVR FSR</b-link>
          extract it to a folder and provide the path to that folder here.
        </template>
      </span>

      <!-- Folder Select Popover -->
      <b-popover target="fsr-folder" triggers="click">
        <h5>OpenVR FSR PlugIn Folder</h5>
        <p>Paste a path in the Format <i>C:\Dir\MyDir</i> where you want to copy the PlugIn dll from.</p>
        <b-form-input size="sm" v-model="fsrDirInput"
                      placeholder="Paste a folder location">
        </b-form-input>
        <div class="text-right mt-1">
          <b-button @click="setFsrDir" size="sm" variant="primary"
                    aria-label="Save">
            Update
          </b-button>
          <b-button @click="$root.$emit('bv::hide::popover', 'fsr-folder')"
                    size="sm" aria-label="Close" class="ml-2">
            Close
          </b-button>
        </div>
      </b-popover>
    </div>

    <SteamLibTable class="mt-3"></SteamLibTable>

    <!-- Busy Overlay -->
    <b-overlay no-wrap fixed :show="isBusy" blur="1px" variant="dark" rounded>
      <b-spinner></b-spinner>
    </b-overlay>
  </div>
</template>

<script>

import SteamLibTable from "@/components/SteamLibTable";
import {getEelJsonObject} from "@/main";

export default {
  name: 'Main',
  data: function () {
    return {
      fsrDirInput: '',
      openFsrDir: null,
      renderScaleSetting: {
        'key': 'renderScale', 'value': 0.75, 'name': 'Render Scale',
        'desc': 'Per-dimension render scale. If <1, will lower the game\'s render resolution ' +
          'accordingly and afterwards upscale to the "native" resolution set in SteamVR. ' +
          'If >1, the game will render at its "native" resolution, and afterwards the ' +
          'image is upscaled to a higher resolution as per the given value. ' +
          'If =1, effectively disables upsampling, but you\'ll still get the sharpening stage. ' +
          'AMD presets: ' +
          'Ultra Quality => 0.77 ' +
          'Quality       => 0.67 ' +
          'Balanced      => 0.59 ' +
          'Performance   => 0.50',
        'settings': [{'settingType': 'range', 'min': 0.10, 'max': 3.0, 'step': 0.01, 'display': 'floatpercent'}]
      },
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
