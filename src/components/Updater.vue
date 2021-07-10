<template>
  <div id="updater" v-if="updatedVersion !== ''" class="mt-2">
    <template v-if="error === ''">
      <span class="mr-2">Update available!</span>
      <template v-if="!updateReady">
        <a :href="downloadUrl" target="_blank">
          <b-button size="sm" variant="primary" :disabled="downloadInProgress">
            <b-spinner small type="grow" v-if="downloadInProgress"></b-spinner>
            Download Version {{ updatedVersion }}
          </b-button>
        </a>
      </template>
      <template v-else>
        <b-button size="sm" variant="success" @click="runUpdate">
          Run update installer {{ updatedVersion }}
        </b-button>
      </template>
    </template>
    <template v-else>
      Updater failed: <pre>{{ error }}</pre>
    </template>
  </div>
</template>

<script>
import {getRequest} from '@/main'
import {version} from '../../package.json';

const GIT_RELEASE_URL = 'https://api.github.com/repos/tappi287/rf2_video_settings/releases/latest'

export default {
  name: 'Updater',
  data: function () {
    return {
      updatedVersion: '',
      downloadInProgress: false,
      updateReady: false,
      error: '',
      downloadUrl: '',
    }
  },
  methods: {
    checkUpdate: async function () {
      console.log('Checking for App updates...')
      // Get version and download url
      const request = await getRequest(GIT_RELEASE_URL)
      if (request.result === false) { this.error = 'Error: ' + request.data.result }

      // Get version and url from GitHub api data
      let newVersion = ''
      try {
        newVersion = request.data.tag_name
        this.downloadUrl = request.data.assets[0].browser_download_url
      } catch (error) {
        console.log(error)
        this.error = error
        return
      }

      if (version >= newVersion) { this.updatedVersion = ''; return }
      console.log('Found updated Version', newVersion)
      this.updatedVersion = newVersion
    },
    downloadUpdate: function () { window.open(this.downloadUrl) },
    runUpdate: function () { },
    /*
    checkUpdate: async function () {
      const r = await getEelJsonObject(window.eel.check_for_updates()())
      if (r === undefined || r === null ) { return }
      if (r.result) {
        this.updatedVersion = r.version
      }
    },
    downloadUpdate: async function () {
      this.downloadInProgress = true
      const r = await getEelJsonObject(window.eel.download_update()())
      this.downloadInProgress = false
      if (r === undefined || r === null ) { return }
      if (r.result) {
        // Offer update run
        this.updateReady = true
      }
    },
    runUpdate: async function () {
      const r = await getEelJsonObject(window.eel.run_update()())
      if (r === undefined || r === null ) { return }
      if (!r.result) {
        this.error = 'Could not execute installer. Navigate to your Downloads directory and try to run it yourself.'
      }
    },
    */
  },
  props: {
    // None yet
  },
  mounted() {
    setTimeout(() => {
      this.checkUpdate()
    }, 2500)
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
