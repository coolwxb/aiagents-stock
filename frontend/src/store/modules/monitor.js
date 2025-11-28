const state = {
  monitorTasks: [],
  currentTask: null,
  positions: []
}

const mutations = {
  SET_MONITOR_TASKS: (state, tasks) => {
    state.monitorTasks = tasks
  },
  SET_CURRENT_TASK: (state, task) => {
    state.currentTask = task
  },
  SET_POSITIONS: (state, positions) => {
    state.positions = positions
  }
}

const actions = {
  setMonitorTasks({ commit }, tasks) {
    commit('SET_MONITOR_TASKS', tasks)
  },
  setCurrentTask({ commit }, task) {
    commit('SET_CURRENT_TASK', task)
  },
  setPositions({ commit }, positions) {
    commit('SET_POSITIONS', positions)
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  actions
}

