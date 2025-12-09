<template>
  <div class="position-tab">
    <el-card shadow="never" class="section-card">
      <div class="section-header">
        <h3>持仓管理</h3>
        <div class="header-actions">
          <el-tag :type="connectionStatus ? 'success' : 'danger'" size="small">
            {{ connectionStatus ? 'QMT已连接' : 'QMT未连接' }}
          </el-tag>
          <el-button size="small" icon="el-icon-refresh" :loading="loading" @click="loadPositions">
            刷新持仓
          </el-button>
        </div>
      </div>

      <!-- 账户概览 -->
      <el-row :gutter="16" class="account-summary">
        <el-col :xs="12" :sm="6">
          <el-card shadow="never" class="summary-card">
            <p class="label">总资产</p>
            <p class="value">{{ formatCurrency(accountInfo.total_value) }}</p>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="6">
          <el-card shadow="never" class="summary-card">
            <p class="label">可用资金</p>
            <p class="value">{{ formatCurrency(accountInfo.available_cash) }}</p>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="6">
          <el-card shadow="never" class="summary-card">
            <p class="label">持仓数量</p>
            <p class="value">{{ accountInfo.positions_count || 0 }}</p>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="6">
          <el-card shadow="never" class="summary-card">
            <p class="label">总盈亏</p>
            <p class="value" :class="profitClass(accountInfo.total_profit_loss)">
              {{ formatProfit(accountInfo.total_profit_loss) }}
            </p>
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
          <el-col :span="3">
            <div class="skeleton-item" style="height: 20px;"></div>
          </el-col>
          <el-col :span="3">
            <div class="skeleton-item" style="height: 20px;"></div>
          </el-col>
          <el-col :span="4">
            <div class="skeleton-item" style="height: 20px;"></div>
          </el-col>
          <el-col :span="4">
            <div class="skeleton-item" style="height: 20px;"></div>
          </el-col>
          <el-col :span="1">
            <div class="skeleton-item" style="height: 20px;"></div>
          </el-col>
        </el-row>
      </div>
      <div v-else-if="!connectionStatus" class="empty-state">
        <i class="el-icon-warning-outline empty-icon"></i>
        <p class="empty-text">QMT未连接</p>
        <p class="form-tip">请在环境配置中启用 MiniQMT 并连接交易账户</p>
      </div>
      <div v-else-if="positionList.length === 0" class="empty-state">
        <i class="el-icon-coin empty-icon"></i>
        <p class="empty-text">暂无持仓数据</p>
      </div>
      <el-table
        v-else
        :data="positionList"
        border
        stripe
        style="width: 100%; margin-top: 16px"
      >
        <el-table-column prop="stock_code" label="股票代码" min-width="100" align="center" />
        <el-table-column prop="stock_name" label="股票名称" min-width="100" />
        <el-table-column prop="quantity" label="持仓数量" min-width="100" align="right">
          <template slot-scope="scope">
            {{ scope.row.quantity || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="cost_price" label="成本价" min-width="100" align="right">
          <template slot-scope="scope">
            {{ formatPrice(scope.row.cost_price) }}
          </template>
        </el-table-column>
        <el-table-column prop="current_price" label="现价" min-width="100" align="right">
          <template slot-scope="scope">
            {{ formatPrice(scope.row.current_price) }}
          </template>
        </el-table-column>
        <el-table-column prop="market_value" label="市值" min-width="110" align="right">
          <template slot-scope="scope">
            {{ formatCurrency(scope.row.market_value) }}
          </template>
        </el-table-column>
        <el-table-column prop="profit_loss" label="浮动盈亏" min-width="110" align="right">
          <template slot-scope="scope">
            <span :class="profitClass(scope.row.profit_loss)">
              {{ formatProfit(scope.row.profit_loss) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="profit_loss_pct" label="盈亏比例" min-width="100" align="right">
          <template slot-scope="scope">
            <span :class="profitClass(scope.row.profit_loss_pct)">
              {{ formatPercent(scope.row.profit_loss_pct) }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { getPositions } from '@/api/gs-strategy'

export default {
  name: 'PositionTab',
  data() {
    return {
      loading: false,
      connectionStatus: false,
      positionList: [],
      accountInfo: {
        total_value: 0,
        available_cash: 0,
        positions_count: 0,
        total_profit_loss: 0
      }
    }
  },
  created() {
    this.loadPositions()
  },
  methods: {
    async loadPositions() {
      this.loading = true
      try {
        const res = await getPositions()
        const data = res.data || res || {}
        // 从 account_info 嵌套对象中获取数据
        const accountInfo = data.account_info || {}
        this.connectionStatus = accountInfo.connected !== false
        this.positionList = data.positions || []
        this.accountInfo = {
          total_value: accountInfo.total_value || 0,
          available_cash: accountInfo.available_cash || 0,
          market_value: accountInfo.market_value || 0,
          frozen_cash: accountInfo.frozen_cash || 0,
          positions_count: accountInfo.positions_count || this.positionList.length,
          total_profit_loss: accountInfo.total_profit_loss || 0
        }
      } catch (error) {
        console.error('加载持仓失败', error)
        this.connectionStatus = false
        this.positionList = []
        this.accountInfo = {
          total_value: 0,
          available_cash: 0,
          market_value: 0,
          frozen_cash: 0,
          positions_count: 0,
          total_profit_loss: 0
        }
      } finally {
        this.loading = false
      }
    },
    formatCurrency(value) {
      if (value === null || value === undefined || value === '') return '--'
      const num = Number(value)
      if (Number.isNaN(num)) return value
      return `¥${num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
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
      const sign = num >= 0 ? '+' : ''
      return `${sign}${num.toFixed(2)}%`
    },
    profitClass(value) {
      if (value === null || value === undefined) return ''
      const num = Number(value)
      if (Number.isNaN(num)) return ''
      // 中国股市：红涨绿跌
      return num >= 0 ? 'text-profit' : 'text-loss'
    },
    // 供父组件调用的刷新方法
    refresh() {
      return this.loadPositions()
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

.account-summary {
  margin-top: 16px;
}

.summary-card {
  text-align: center;
  border-radius: 8px;
}

.summary-card .label {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.summary-card .value {
  margin: 8px 0 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

/* 中国股市：红涨绿跌 */
.text-profit {
  color: #e74c3c;
  font-weight: 500;
}

.text-loss {
  color: #27ae60;
  font-weight: 500;
}

.form-tip {
  color: #909399;
  font-size: 12px;
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

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  color: #909399;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  color: #c0c4cc;
}

.empty-text {
  margin: 0;
  font-size: 14px;
}
</style>
