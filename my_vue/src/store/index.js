import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    user: JSON.parse(localStorage.getItem('user')) || null,
    token: localStorage.getItem('token') || null
  },
  getters: {
    isLoggedIn: state => !!state.token,
    currentUser: state => state.user,
    currentRole: state => state.user ? state.user.role : null,
    dealerCode: state => state.user ? state.user.dealerCode : null,
    isAdmin: state => state.user ? state.user.role === 'admin' : false,
    isDealer: state => state.user ? state.user.role === 'dealer' : false
  },
  mutations: {
    setUser(state, user) {
      state.user = user
      if (user) {
        localStorage.setItem('user', JSON.stringify(user))
      } else {
        localStorage.removeItem('user')
      }
    },
    setToken(state, token) {
      state.token = token
      if (token) {
        localStorage.setItem('token', token)
      } else {
        localStorage.removeItem('token')
      }
    },
    clearUser(state) {
      state.user = null
      state.token = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  },
  actions: {
    login({ commit }, { user, token }) {
      commit('setUser', user)
      commit('setToken', token)
    },
    logout({ commit }) {
      commit('clearUser')
    }
  },
  modules: {
  }
})
