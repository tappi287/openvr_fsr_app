import Vue from 'vue'
import App from './App.vue'
import { BootstrapVue, BootstrapVueIcons } from 'bootstrap-vue'
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'
import Axios from "axios"
import VueI18n from 'vue-i18n';
import messages from './lang';

Vue.use(BootstrapVue)
Vue.use(BootstrapVueIcons)
Vue.config.productionTip = false
Vue.config.devtools = true

// --- i18n support
Vue.use(VueI18n)
export const i18n = new VueI18n({
  locale: 'en',
  fallbackLocale: 'en',
  messages
})
let _l = []
for (const lang in messages) { _l.push(lang) }
export const languages = _l

Vue.prototype.$eventHub = new Vue(); // Global event bus

new Vue({
  render: h => h(App),
  i18n
}).$mount('#app')

export async function getEelJsonObject (promise) {
  const value = await promise
  return JSON.parse(value)
}

export function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms))
}

export var isValid=(function(){
  let rg1=/^[^\\/:*?"<>|]+$/; // forbidden characters \ / : * ? " < > |
  let rg2=/^\./; // cannot start with dot (.)
  let rg3=/^(nul|prn|con|lpt[0-9]|com[0-9])(\.|$)/i; // forbidden file names
  return function isValid(fname){
    return rg1.test(fname)&&!rg2.test(fname)&&!rg3.test(fname);
  }
})();

export function getMaxWidth (elements) {
  let maxWidth = 0
  for (let i in elements) {
    if (elements[i].clientWidth !== undefined) {
      maxWidth = Math.max(maxWidth, parseInt(elements[i].clientWidth))
    }
  }
  return maxWidth
}

export function clearWidthStyle (elements) {
  for (let i in elements) {
      if (elements[i].style !== undefined) { elements[i].style.width = null }
  }
}

export function setFixedWidth(groupId, nameId, elemId) {
  // Iterate all elements of this setting group_id and set width to widest element found
  const nameElem = document.querySelectorAll('#' + groupId + ' .fixed-width-name')
  const settElem = document.querySelectorAll('#' + groupId + ' .fixed-width-setting')

  let nameMaxWidth = getMaxWidth(nameElem); let settMaxWidth = getMaxWidth(settElem)

  let e = document.getElementById(nameId)
  if (e !== null) { e.style.width = String(nameMaxWidth) + 'px' }
  let s = document.getElementById(elemId)
  if (s !== null) { s.style.width = String(settMaxWidth) + 'px' }
}

// Generic axios GET request
export async function getRequest(url) {
  try {
    let requestUrl
    requestUrl = url
    const response = await Axios.get(requestUrl)
    return { result: true, data: response.data }
  } catch (error) {
    return { result: false, data: error.response.data }
  }
}

export function minutesToDaytime(num) {
  const hours = ('0' + String(Math.floor(num / 60))).slice(-2)
  const minutes = ('0' + String(num % 60)).slice(-2)
  return String(hours + ":" + minutes)
}