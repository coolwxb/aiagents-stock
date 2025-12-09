<template>
  <div class="history-tab">
    <el-card shadow="never" class="section-card">
      <div class="section-header">
        <h3>历史统计</h3>
        <div class="header-actions">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            size="small"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="yyyy-MM-dd"
            @change="handleDateChange"
          />
          <el-button size="small" icon="el-icon-refresh" :loading="loading" @click="loadData">
            刷新
          </el-button>
        </div>
      </div>

      <!-- 统计概览 -->
      <el-row :gutter="16" class="stats-summary">
        <el-col :xs="12" :sm="6">
          <el-card shadow="never" class="stats-card">
            <p class="label">总交易数</p>
            <p class="value">{{ statistics.total_trades || 0 }}</p>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="6">
          <el-card shadow="never" class="stats-card">
            <p class="label">盈利交易</p>
            <p class="value text-success">{{ statistics.winning_trades || 0 }}</p>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="6">
          <el-card shadow="never" class="stats-card">
            <p class="label">亏损交易</p>
            <p class="value text-danger">{{ statistics.losing_trades || 0 }}</p>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="6">
          <el-card shadow="never" class="stats-card">
            <p class="label">胜率</p>
            <p class="value" :class="winRateClass">{{ formatPercent(statistics.win_rate) }}</p>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="16" class="stats-summary" style="margin-top: 16px">
        <el-col :xs="24" :sm="8">
          <el-card shadow="never" class="stats-card">
            <p class="label">总盈亏</p>
            <p class="value" :class="profitClass(statistics.total_profit_loss)">
              {{ formatProfit(statistics.total_profit_loss) }}
            </p>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="8">
          <el-card shadow="never" class="stats-card">
            <p class="label">平均盈利</p>
            <p class="value text-success">{{ formatProfit(statistics.avg_profit) }}</p>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="8">
          <el-card shadow="never" class="stats-card">
            <p class="label">平均亏损</p>
            <p class="value text-danger">{{ formatProfit(statistics.avg_loss) }}</p>
          </el-card>
        </el-col>
      </el-row>

      <div v-if="loading" class="loading-container">
        <el-row :gutter="20" v-for="i in 4" :key="i" style="margin-bottom: 16px;">
          <el-col :span="3">
            <div class="skeleton-item" style="height: 20px;"></div>
          </el-col>
          <el-col :span="3">
            <div class="skeleton-item" style="height: 20px;"></div>
          </el-col>
          <el-col :span="3">
            <div class="skeleton-item" style="height: 20px;"></div>
          </el-col>
          <el-col :span="4">
            <div class="skeleton-item" style="height: 20px;"></div>
          </el-col>
          <el-col :span="3">
            <div class="skeleton-item" style="height: 20px;"></div>
          </el-col>
          <el-col :span="4">
            <div class="skeleton-item" style="height: 20px;"></div>
          </el-col>
          <el-col :span="3">
            <div class="skeleton-item" style="height: 20px;"></div>
          </el-col>
          <el-col :span="1">
            <div class="skeleton-item" style="height: 20px;"></div>
          </el-col>
        </el-row>
      </div>
      <div v-else-if="historyList.length === 0" class="empty-state">
        <i class="el-icon-document"></i>
        <p>暂无交易历史</p>
      </div>
      <el-table
        v-else
        :data="historyList"
        border
        stripe
        style="width: 100%; margin-top: 16px"
      >
        <el-table-column prop="stock_code" label="股票代码" min-width="100" align="center" />
        <el-table-column prop="stock_name" label="股票名称" min-width="100" />
        <el-table-column prop="buy_price" label="买入价" min-width="100" align="right">
          <template slot-scope="scope">
            {{ formatPrice(scope.row.buy_price) }}
          </template>
        </el-table-column>
        <el-table-column prop="buy_time" label="买入时间" min-width="160">
          <template slot-scope="scope">
            {{ formatTime(scope.row.buy_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="sell_price" label="卖出价" min-width="100" align="right">
          <template slot-scope="scope">
            {{ formatPrice(scope.row.sell_price) }}
          </template>
        </el-table-column>
        <el-table-column prop="sell_time" label="卖出时间" min-width="160">
          <template slot-scope="scope">
            {{ formatTime(scope.row.sell_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="profit_loss" label="盈亏金额" min-width="110" align="right">
          <template slot-scope="scope">
            <span :class="profitClass(scope.row.profit_loss)">
              {{ formatProfit(scope.row.profit_loss) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="profit_loss_pct" label="盈亏比例" min-width="100" align="right">
          <template slot-scope="scope">
            <span :class="profitClass(scope.row.profit_loss_pct)">
              {{ formatProfitPercent(scope.row.profit_loss_pct) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" min-width="80" align="center">
          <template slot-scope="scope">
            <el-tag :type="scope.row.status === 'closed' ? 'success' : 'warning'" size="small">
              {{ scope.row.status === 'closed' ? '已平仓' : '持仓中' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { getTradeHistory, getStatistics } from '@/api/gs-strategy'

export default {
  name: 'HistoryTab',
  data() {
    return {
      loading: false,
      dateRange: null,
      historyList: [],
      statistics: {
        total_trades: 0,
        winning_trades: 0,
        losing_trades: 0,
        win_rate: 0,
        total_profit_loss: 0,
        avg_profit: 0,
        avg_loss: 0
      }
    }
  },
  computed: {
    winRateClass() {
      const rate = this.statistics.win_rate || 0
      if (rate >= 50) return 'text-success'
      if (rate >= 30) return 'text-warning'
      return 'text-danger'
    }
  },
  created() {
    this.loadData()
  },
  methods: {
    async loadData() {
      this.loading = true
      try {
        await Promise.all([this.loadHistory(), this.loadStatistics()])
      } finally {
        this.loading = false
      }
    },
    async loadHistory() {
      try {
        const params = {}
        if (this.dateRange && this.dateRange.length === 2) {
          params.start_date = this.dateRange[0]
          params.end_date = this.dateRange[1]
        }
        const res = await getTradeHistory(params)
        this.historyList = res.data || res || []
      } catch (error) {
        console.error('加载交易历史失败', error)
        this.historyList = []
      }
    },
    async loadStatistics() {
      try {
        const res = await getStatistics()
        const data = res.data || res || {}
        this.statistics = {
          total_trades: data.total_trades || 0,
          winning_trades: data.winning_trades || 0,
          losing_trades: data.losing_trades || 0,
          win_rate: data.win_rate || 0,
          total_profit_loss: data.total_profit_loss || 0,
          avg_profit: data.avg_profit || 0,
          avg_loss: data.avg_loss || 0
        }
      } catch (error) {
        console.error('加载统计数据失败', error)
        this.statistics = {
          total_trades: 0,
          winning_trades: 0,
          losing_trades: 0,
          win_rate: 0,
          total_profit_loss: 0,
          avg_profit: 0,
          avg_loss: 0
        }
      }
    },
    handleDateChange() {
      this.loadHistory()
    },
    formatTime(value) {
      if (!value) return '--'
      return String(value).replace('T', ' ').substring(0, 19)
    },
    formatPrice(value) {
      if (value === null || value === undefined || value === '') return '--'
      const num = Number(value)
      if (Number.isNaN(num)) return value
      return num.toFixed(2)
    },
    formatProfit(value) {
      if (value === null || value === undefined || value === '') return '--'
      const num = Number(value)
      if (Number.isNaN(num)) return value
      const sign = num >= 0 ? '+' : ''
      return `${sign}¥${num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    },
    formatPercent(value) {
      if (value === null || value === undefined || value === '') return '--'
      const num = Number(value)
      if (Number.isNaN(num)) return value
      return `${num.toFixed(2)}%`
    },
    formatProfitPercent(value) {
      if (value === null || value === undefined || value === '') return '--'
      const num = Number(value)
      if (Number.isNaN(num)) return value
      const sign = num >= 0 ? '+' : ''
      return `${sign}${num.toFixed(2)}%`
    },
    profitClass(value) {
      if (value === null || value === undefined) return ''
      const num = Number(value)
      if (Number.isNaN(num)) return ''
      return num >= 0 ? 'text-success' : 'text-danger'
    },
    // 供父组件调用的刷新方法
    refresh() {
      return this.loadData()
    }
  }
}
</script>

<style scoped>
.section-card {
  border-radius: 12px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.section-header h3 {
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.stats-summary {
  margin-top: 16px;
}

.stats-card {
  text-align: center;
  border-radius: 8px;
}

.stats-card .label {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.stats-card .value {
  margin: 8px 0 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.text-success {
  color: #67c23a;
}

.text-warning {
  color: #e6a23c;
}

.text-danger {
  color: #f56c6c;
}

.loading-container {
  margin-top: 16px;
}

.skeleton-item {
  background: linear-gradient(90deg, #f2f2f2 25%, #e6e6e6 50%, #f2f2f2 75%);
  background-size: 200% 100%;
  border-radius: 4px;
  animation: skeleton-loading 1.5s infinite;
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
