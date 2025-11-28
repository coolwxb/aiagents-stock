const state = {
  analysisList: [],
  currentAnalysis: null
}

const mutations = {
  SET_ANALYSIS_LIST: (state, list) => {
    state.analysisList = list
  },
  SET_CURRENT_ANALYSIS: (state, analysis) => {
    state.currentAnalysis = analysis
  }
}

const actions = {
  setAnalysisList({ commit }, list) {
    commit('SET_ANALYSIS_LIST', list)
  },
  setCurrentAnalysis({ commit }, analysis) {
    commit('SET_CURRENT_ANALYSIS', analysis)
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  actions
}

