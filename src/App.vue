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
  },
  computed: {
  },
  destroyed() {
    window.removeEventListener('app-exception-event', this.setException)
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

<style>
#app {
  /*font-family: Avenir, Helvetica, Arial, sans-serif;*/
  /* font-family: "Ubuntu", sans-serif;*/
  font-family: "Segoe UI", system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #efefef;
}
body {
  background: none !important;
}
html {
  /*background-image: linear-gradient(60deg, #172122 0%, #0c1013 100%);*/
  background: #16161a;
}
.no-border { border: none; }
.main-footer {
  margin-bottom: 3rem;
}
.info-field {
  background-image: linear-gradient(to left, #ddd9de 0%, #c6c7cd 100%), radial-gradient(88% 271%, rgba(255, 255, 255, 0.25) 0%, rgba(254, 254, 254, 0.25) 1%, rgba(0, 0, 0, 0.25) 100%), radial-gradient(50% 100%, rgba(255, 255, 255, 0.30) 0%, rgba(0, 0, 0, 0.30) 100%);
  background-blend-mode: normal, lighten, soft-light;
}
.info-field.diff {
  background-image: linear-gradient(120deg, #ddd9de 70%, #fa7c56 100%);
  border: none;
}
.setting { display: inline-block }
.setting-item { min-width: 7.0rem; font-weight: lighter; }
.setting-field {
  box-shadow: 0 6px 15px rgba(36, 37, 38, 0.3);
}
/* Remove plastic bootstrap style */
.setting-card .card-header, .card-body, .card-footer {
  background: none; border: none;
}
@keyframes backgroundColorPalette {
  0% {
    background: #ecaaa8;
  }
  100% {
    background: white;
  }
}
.filter-warn {
  animation-name: backgroundColorPalette;
  animation-duration: 4s;
  animation-iteration-count: infinite;
  animation-direction: alternate;
}
.server-list * td { vertical-align: baseline !important; }
.server-list { margin-bottom: 0; font-family: "Segoe UI", system-ui, sans-serif; }
</style>
