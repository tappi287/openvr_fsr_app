<template>
  <div>
    <b-dropdown right variant="secondary" :text="$i18n.locale">
      <b-dropdown-item v-for="(lang, i) in languages"
                       :key="`lang-${i}`"
                       @click="selectLanguage(lang)">
        {{ lang }}
      </b-dropdown-item>
    </b-dropdown>
  </div>
</template>

<script>
import {languages} from "@/main";

export default {
  name: 'LanguageSwitcher',
  data() {
    return { languages: languages }
  },
  methods: {
    selectLanguage: function (lang) {
      this.$i18n.locale = lang
    },
    autoSelectLanguage: function () {
      const userLang = navigator.languages ? navigator.languages[0] : (navigator.language || navigator.userLanguage)
      this.languages.forEach(lang => {
        if (userLang.substr(0,2) === lang) {
          this.selectLanguage(lang)
        }
      })
    }
  },
  mounted() {
    this.autoSelectLanguage()
  }
}
</script>

<style>

</style>