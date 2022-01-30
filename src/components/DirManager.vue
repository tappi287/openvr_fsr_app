<template>
  <div>
    <!-- Mod source directories -->
    <b-card class="mb-4" header="Default" v-if="showModDir">
      <template #header>
        <h5><b-icon class="mr-2" icon="file-earmark-easel-fill" />{{ $t('main.folderPop') }}</h5>
      </template>

      <div class="mb-3 d-flex flex-row justify-content-between">
        <div class="d-inline-flex">{{ $t('main.folderPopSelect') }}</div>

        <b-dropdown :text="modNames[selectedModType]" size="sm" class="d-inline-flex">
          <b-dropdown-item v-for="modType in modTypes" :key="modType" @click="selectedModType = modType">
            {{ modNames[modType] }}
          </b-dropdown-item>
        </b-dropdown>
      </div>

      <div class="p-0">
        <p v-html="$t('main.folderPopText')" />
        <p><span v-html="$t('main.folderPopCurrent')" /><i> {{ modDataDirs[selectedModType] }}</i></p>
        <b-form-input size="sm" v-model="modDirInput" class="mt-2"
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
    <b-card class="mb-4" header="Default" v-if="showCustomDir">
      <template #header>
        <h5><b-icon class="mr-2" icon="folder-fill" />{{ $t('main.dirModLibs') }}</h5>
      </template>
      <template v-if="customDirs.length !== 0">
        <div v-for="d in customDirs" :key="d.id" class="mb-3 d-flex flex-row justify-content-between">
          <div class="d-inline-flex">{{ d.id }}: {{ d.path }}</div>
          <div class="d-inline-flex">
            <b-button size="sm" :id="'remove'+d.id" variant="danger">
              <b-icon icon="eject-fill"></b-icon>
            </b-button>
          </div>

          <!-- Confirm Dir Remove Popover-->
          <b-popover :target="'remove'+d.id">
            <div>{{ $t('main.dirRem')}}</div>
            <div>
              <b-button @click="removeCustomDir(d.id)" size="sm" variant="danger" class="mr-2">
                {{ $t('main.dirRemConfirm')}}
              </b-button>
              <b-button @click="$root.$emit('bv::hide::popover', 'remove'+d.id)"
                        size="sm" variant="secondary">
                {{ $t('main.folderPopClose') }}
              </b-button>
            </div>
          </b-popover>
        </div>
      </template>
      <template v-else>
        <div v-html="$t('main.dirModNoLib')"></div>
      </template>

      <!-- Add Custom Dir -->
      <hr>
      <h5 v-html="$t('lib.addDirTitle')"></h5>
      <div class="mb-2" v-html="$t('lib.addDirText')" />

      <div class="mb-3 d-flex flex-row align-items-center justify-content-between">
        <div class="d-inline-flex mr-2">
          <b-form @submit.prevent @reset.prevent>
            <b-form-group id="input-group-2" :label="$t('lib.addAppPath')" label-for="input-1"
                          :description="$t('lib.addDirPathHint')">
              <b-form-input id="input-2" v-model="addDir" required :placeholder="$t('lib.addAppPathPlace')" />
            </b-form-group>
          </b-form>
        </div>
        <div class="d-inline-flex ml-2">
          <b-button variant="primary" @click="addCustomDir">
            <b-icon icon="folder-plus"></b-icon>
            <span class="ml-2" v-html="$t('lib.addDirSubmit')"></span>
          </b-button>
        </div>
      </div>
    </b-card>
  </div>
</template>

<script>
import {getEelJsonObject} from "@/main";

export default {
  name: "DirManager",
  data: function () {
    return {
      modDirInput: '',
      modDataDirs: {0: null, 1: null, 2: null},
      userAppDirs: {},
      addDir: '',
      selectedModType: 2,
      modTypes: [0, 1, 2],
      modNames: {0: 'Open VR FSR', 1: 'Open VR Foveated', 2: 'VR Performance Toolkit'},
    }
  },
  props: {
    showModDir: Boolean, showCustomDir: Boolean
  },
  methods: {
    getCustomDirs: async function () {
      const r = await window.eel.get_custom_dirs()()
      if (r !== undefined) { this.userAppDirs = r }
    },
    removeCustomDir: async function(dir_id) {
      this.$eventHub.$emit('set-busy', true)
      this.$eventHub.$emit('toggle-dir-manager')

      const r = await getEelJsonObject(window.eel.remove_custom_dir(dir_id)())
      if (!r.result) {
        // Error
        this.$eventHub.$emit('make-toast',
            'Could not remove Custom Library: ' + r.msg, 'danger', 'Remove Custom Folder Entry', true, -1)
      } else {
        // Success
        this.$eventHub.$emit('reload-steam-lib')
      }
      this.$eventHub.$emit('set-busy', false)
    },
    addCustomDir: async function() {
      if (this.addDir === '') { return }
      this.$eventHub.$emit('set-busy', true)
      this.$eventHub.$emit('toggle-dir-manager')
      this.$eventHub.$emit('update-progress', '')

      const r = await getEelJsonObject(window.eel.add_custom_dir(this.addDir)())
      if (!r.result) {
        // Error
        this.$eventHub.$emit('make-toast',
            'Error adding custom folder entry: ' + r.msg, 'danger', 'Add Folder Entry', true, -1)
      } else {
        // Success
        this.$eventHub.$emit('reload-steam-lib')
        this.$eventHub.$emit('sort-steam-lib', 'id', false)
      }

      this.addDir = ''
      this.$eventHub.$emit('set-busy', false)
    },
    getModDir: async function (modType = 0) {
      const r = await window.eel.get_mod_dir(modType)()
      if (r !== undefined) { this.modDataDirs[modType] = r }
    },
    resetModDir: async function(modType = 0) {
      modType = Number(modType)
      this.modDirInput = ''
      await this.setModDir(modType)
    },
    setModDir: async function (modType) {
      const r = await getEelJsonObject(window.eel.set_mod_dir(this.modDirInput, modType)())

      if (r !== undefined && r.result) {
        await this.getModDir(modType)
        this.$eventHub.$emit('make-toast','Updated ' + this.modNames[modType] + ' directory to: ' + this.modDataDirs[modType],
            'success', this.modNames[modType])
      } else {
        this.$eventHub.$emit('make-toast','Could not update Mod source directory. Provided path does not exists, ' +
            'is not accessible or does not contain the PlugIn Dll and cfg file.',
            'danger', this.modNames[modType])
        await this.getModDir(modType)
      }
    },
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
  async beforeMount() {
    await this.getCustomDirs()
  },
  async created() {
    for (const modType in this.modTypes) {
      await this.getModDir(Number(modType))
    }
  }
}
</script>

<style scoped>

</style>