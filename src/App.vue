<template>
  <div id="app">
    <!-- Exception component -->
    <template v-if="error !== ''">
      <b-container fluid="sm">
        <b-card class="mt-3" bg-variant="dark" text-variant="white">
          <template #header>
            <h6 class="mb-0"><span class="title">Critical Error</span></h6>
          </template>
          <b-card-text class="text-left">
            <pre class="text-white">{{ error }}</pre>
          </b-card-text>
          <b-card-text>
            If you think the error relates to missing privileges:
            try to re-run this application with administrative privileges:
            <b-button class="mt-2 mb-2" @click="reRunAsAdmin" size="sm">UAC Re-Run-as-Admin</b-button>
          </b-card-text>

          <template #footer>
            <span class="small">
              Something went wrong.
            </span>
          </template>
        </b-card>
        <div class="mt-3">
          <b-button @click="requestClose" size="sm">Exit</b-button>
        </div>
      </b-container>
    </template>

    <!-- Main component -->
    <Main v-on:error="setError" ref="main"></Main>

    <!-- Footer -->
    <div class="mt-3 main-footer small font-weight-lighter">
      <Updater></Updater>
    </div>
  </div>
</template>

<script>
import Main from "./components/Main.vue";
import Updater from "./components/Updater";
import {createPopperLite as createPopper, flip, preventOverflow} from "@popperjs/core";

// --- </ Prepare receiving App Exceptions
window.eel.expose(appExceptionFunc, 'app_exception')
async function appExceptionFunc (event) {
  const excEvent = new CustomEvent('app-exception-event', {detail: event})
  window.dispatchEvent(excEvent)
}
// --- />
// --- </ Prepare receiving Progress Updates
window.eel.expose(updateProgressFunc, 'update_progress')
async function updateProgressFunc (event) {
  const progressEvent = new CustomEvent('update-progress-event', {detail: event})
  window.dispatchEvent(progressEvent)
}
// --- />

export default {
  name: 'App',
  data: function () {
    return {
      error: '',
    }
  },
  methods: {
    setException: function (event) {
      this.setError(event.detail)
      this.$refs.main.setBusy(false)
    },
    setError: function (error) {
      console.error(error)
      this.error = error
    },
    requestClose: async function () {
      await window.eel.close_request()
    },
    reRunAsAdmin: async function () {
      await window.eel.re_run_admin()
    },
    resetAdmin: async function () {
      await window.eel.reset_admin()
    },
    emitProgressEvent: function (event) {
      this.$eventHub.$emit('update-progress', event.detail)
    },
  },
  components: {
    Updater,
    Main
  },
  watch: {
  },
  mounted() {
  },
  created() {
    window.addEventListener('beforeunload', this.requestClose)
    window.addEventListener('app-exception-event', this.setException)
    window.addEventListener('update-progress-event', this.emitProgressEvent)
  },
  computed: {
  },
  destroyed() {
    window.removeEventListener('app-exception-event', this.setException)
    window.removeEventListener('update-progress-event', this.emitProgressEvent)
  }
}

function neverCalled() {
  createPopper()
  preventOverflow()
  flip()
}

let pass = true
if (!pass) {
  neverCalled()
}
</script>

<style src="./assets/main.css">

</style>
