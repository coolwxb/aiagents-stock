<template>
  <div class="gs-strategy-page app-container">
    <el-card shadow="hover" class="gs-strategy-panel">
      <div slot="header" class="card-header">
        <div>
          <h2>📊 GS策略</h2>
          <p class="subtitle">基于中枢G买卖信号的自动化交易系统，管理股票池、监控队列、持仓和历史统计</p>
        </div>
        <div class="header-actions">
          <el-button icon="el-icon-refresh" :loading="loading" @click="refreshCurrentTab">刷新数据</el-button>
        </div>
      </div>

      <el-tabs v-model="activeTab" class="gs-strategy-tabs" @tab-click="handleTabClick">
        <el-tab-pane label="📋 股票池" name="stockPool">
          <stock-pool-tab ref="stockPoolTab" @add-to-monitor="handleAddToMonitor" />
        </el-tab-pane>

        <el-tab-pane label="📈 监控管理" name="monitor">
          <monitor-tab ref="monitorTab" />
        </el-tab-pane>

        <el-tab-pane label="💼 持仓管理" name="position">
          <position-tab ref="positionTab" />
        </el-tab-pane>

        <el-tab-pane label="📜 历史统计" name="history">
          <history-tab ref="historyTab" />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script>
import StockPoolTab from './components/StockPoolTab.vue'
import MonitorTab from './components/MonitorTab.vue'
import PositionTab from './components/PositionTab.vue'
import HistoryTab from './components/HistoryTab.vue'

export default {
  name: 'GSStrategyIndex',
  components: {
    StockPoolTab,
    MonitorTab,
    PositionTab,
    HistoryTab
  },
  data() {
    return {
      activeTab: 'stockPool',
      loading: false
    }
  },
  methods: {
    handleTabClick(tab) {
      // 点击tab时自动刷新对应数据
      this.$nextTick(() => {
        const tabRef = this.$refs[tab.name + 'Tab']
        if (tabRef && typeof tabRef.refresh === 'function') {
          this.loading = true
          tabRef.refresh().finally(() => {
            this.loading = false
          })
        }
      })
    },
    refreshCurrentTab() {
      this.loading = true
      const tabRef = this.$refs[this.activeTab + 'Tab']
      if (tabRef && typeof tabRef.refresh === 'function') {
        tabRef.refresh().finally(() => {
          this.loading = false
        })
      } else {
        this.loading = false
      }
    },
    handleAddToMonitor() {
      // Switch to monitor tab and refresh list
      this.activeTab = 'monitor'
      this.$nextTick(() => {
        if (this.$refs.monitorTab && typeof this.$refs.monitorTab.refresh === 'function') {
          this.$refs.monitorTab.refresh()
        }
      })
    }
  }
}
</script>

<style scoped>
.gs-strategy-panel {
  border-radius: 14px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.card-header h2 {
  margin: 0;
}

.subtitle {
  margin: 6px 0 0;
  color: #909399;
}

.header-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.gs-strategy-tabs {
  margin-top: 16px;
}
</style>
