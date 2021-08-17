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
            OpenVR FSR found at <i>{{ openFsrDir }}</i>. Click to customize PlugIn source path.
          </template>
          <template v-else>
            <b>OpenVR FSR PlugIn not found!</b> Download
            <b-link href="https://github.com/fholger/openvr_fsr/releases/latest" target="_blank">OpenVR FSR</b-link>
            extract it to a folder and provide the path to that folder here.
          </template>
        </b-popover>

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

        <!-- Info Toggle -->
        <b-button size="sm" variant="secondary" v-b-toggle.info-collapse class="ml-2">
          <b-icon icon="info-square-fill" />
        </b-button>
      </b-navbar-nav>
    </b-navbar>

    <!-- Info -->
    <b-collapse id="info-collapse">
      <b-card class="setting-card mt-3" bg-variant="dark" text-variant="white" footer-class="pt-0">
        <p>Browse through your Steam library, let this app install the
          <b-link href="https://github.com/fholger/openvr_fsr#modified-openvr-dll-with-amd-fidelityfx-superresolution-upscaler"
                  target="_blank">
            Modified OpenVR DLL with AMD FidelityFX SuperResolution Upscaler
          </b-link>
        and adjust the plugin settings per app.</p>
        <p>
          <b>Note:</b> This app has absolutely no knowledge which Steam apps will work with the FSR PlugIn.
          But this app might be the quickest way to find out <b-icon icon="emoji-sunglasses-fill" />.
        </p>
        <h5 class="mt-4 text-primary">Installation</h5>
        <p>
          Hit the <i>install plugin</i> button in the menu for your Steam app of choice.
          That will enable the AMD FidelityFX Super Resolution plugin.
        </p>

        <h5 class="mt-4 text-primary">Install Location</h5>
        <p>
          Find the location of the openvr_api.dll in the game's installation folder that are listed with checkboxes
          in each entry:<br /><br />

          It might be located right next to the main executable (e.g. Skyrim, FO4).<br />
          For Unity games, look in: [GameDir]\[]Game]_Data\Plugins<br />
          For Unreal 4 games, look in: [GameDir]\Engine\Binaries\ThirdParty\OpenVR\OpenVRvX_Y_Z<br /><br />
          Take care if there are folders like [SteamVRInput] which might not be used for rendering and should
          not be replaced.<br />
          In that case simply uncheck that locations checkbox before installing the plugin.<br /><br />

          In case you run into issues, the log file (openvr_mod.log) may provide clues to what's going on.
        </p>

        <h3 class="mt-5 text-primary">Plugin Configuration</h3>
        <h5 class="text-info">Render Scale</h5>
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
        <h5 class="mt-4 text-info">Sharpness</h5><p>Tune sharpness, values range from 0 to 1</p>
        <h5 class="mt-4 text-info">Radius</h5>
        <p>
          Only apply FSR to the given radius around the center of the image.
          Anything outside this radius is upscaled by simple bilinear filtering,
          which is cheaper and thus saves a bit of performance. Due to the design
          of current HMD lenses, you can experiment with fairly small radii and may
          still not see a noticeable difference.
          Sensible values probably lie somewhere between [0.2, 1.0]. However, note
          that, since the image is not spheric, even a value of 1.0 technically still
          skips some pixels in the corner of the image, so if you want to completely
          disable this optimization, you can choose a value of 2.
        </p>
        <h5 class="mt-4 text-info">Apply MIP Bias</h5>
        <p>
          If enabled, applies a negative LOD bias to texture MIP levels
          should theoretically improve texture detail in the upscaled image
        </p>
        <h5 class="mt-4 text-info">Debug Mode</h5>
        <p>
          If enabled, will visualize the radius to which FSR is applied.
          Will also periodically log the GPU cost for applying FSR in the
          current configuration.
        </p>
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
