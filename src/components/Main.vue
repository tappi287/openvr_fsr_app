<template>
  <div id="main" class="text-left">
    <h4 class="mt-2">OpenVR FSR App</h4>

    <span>Browse through your Steam library, install the OpenVR FSR plugin and adjust the plugin settings.</span>
    <p>
      Note: This app has absolutely no knowledge of which Steam app works with the FSR PlugIn.
      But this app might be the quickest way to find out.
    </p>

    <div class="text-center">
      <!-- FSR Folder Select -->
      <b-button variant="secondary" id="fsr-folder">
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
        <p>Paste a path in the Format <i>C:\Dir\MyDir</i></p>
        <b-form-input size="sm" v-model="fsrDirInput"
                      placeholder="Paste a folder location">
        </b-form-input>
        <div class="text-right mt-1">
          <b-button @click="setFsrDir" size="sm" variant="primary"
                    aria-label="Save">
            Update
          </b-button>
          <b-button @click="$root.$emit('bv::hide::popover', 'fsr-folder')"
                    size="sm" aria-label="Close">
            Close
          </b-button>
        </div>
      </b-popover>
    </div>

    <SteamLibTable class="mt-2"></SteamLibTable>

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
  width: 97%;
  margin: 0 auto 0 auto;
}
</style>
