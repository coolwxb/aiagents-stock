<template>
  <div class="history-page app-container">
    <el-card shadow="hover">
      <div slot="header" class="card-header">
        <div>
          <h2>📖 历史分析记录</h2>
          <p class="subtitle">回顾 AI 团队过往的分析结果，查找复盘材料或重新加入监测</p>
        </div>
        <div class="header-actions">
          <el-button icon="el-icon-refresh" :loading="loading" @click="loadRecords">刷新</el-button>
        </div>
      </div>

      <el-form :inline="true" size="small" class="toolbar">
        <el-form-item label="搜索">
          <el-input
            v-model="searchKeyword"
            placeholder="输入股票代码或名称"
            clearable
            @clear="handleSearch"
            @keyup.enter.native="handleSearch"
          >
            <el-button slot="append" icon="el-icon-search" @click="handleSearch" />
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button @click="resetFilter">清除筛选</el-button>
        </el-form-item>
        <el-form-item>
          <el-tag v-if="fallbackMode" type="warning">已加载示例数据，仅供前端联调演示</el-tag>
        </el-form-item>
      </el-form>

      <el-row :gutter="16" class="stat-row">
        <el-col v-for="card in statCards" :key="card.label" :xs="12" :sm="8" :md="6">
          <el-card shadow="never" class="stat-card">
            <p class="label">{{ card.label }}</p>
            <h3 class="value">{{ card.value }}</h3>
            <p class="desc">{{ card.desc }}</p>
          </el-card>
        </el-col>
      </el-row>

      <el-skeleton v-if="loading" :rows="6" animated />
      <template v-else>
        <el-empty v-if="filteredRecords.length === 0" description="暂无历史记录" />
        <div v-else class="record-list">
          <el-card
            v-for="record in filteredRecords"
            :key="record.id"
            shadow="hover"
            class="record-card"
          >
            <div class="record-header">
              <div>
                <h3 class="record-title">
                  {{ record.stock_name || '未命名' }}（{{ record.symbol }}）
                  <el-tag :type="ratingTagType(record.rating)" size="small">{{ record.rating || '未知' }}</el-tag>
                </h3>
                <p class="record-meta">
                  分析日期：{{ formatDate(record.analysis_date) }} · 数据周期：{{ record.period || '-' }}
                </p>
              </div>
              <div class="record-actions">
                <el-button size="mini" icon="el-icon-view" @click="viewDetail(record)">查看详情</el-button>
                <el-button size="mini" icon="el-icon-bell" :loading="addingMonitorId === record.id" @click="addToMonitor(record)">
                  加入监测
                </el-button>
                <el-popconfirm title="删除后无法恢复，确认删除？" @confirm="deleteRecord(record)">
                  <el-button slot="reference" size="mini" type="danger" icon="el-icon-delete">删除</el-button>
                </el-popconfirm>
              </div>
            </div>
            <div class="record-body">
              <el-row :gutter="16">
                <el-col :sm="6" :xs="12">
                  <p class="summary-label">当前价格</p>
                  <p class="summary-value">{{ getField(record.stock_info, 'current_price') }}</p>
                </el-col>
                <el-col :sm="6" :xs="12">
                  <p class="summary-label">涨跌幅</p>
                  <p class="summary-value">{{ formatPercent(getField(record.stock_info, 'change_percent', null)) }}</p>
                </el-col>
                <el-col :sm="6" :xs="12">
                  <p class="summary-label">信心度</p>
                  <el-progress :percentage="confidencePercent(getField(record.final_decision, 'confidence_level', null))" :stroke-width="10" />
                </el-col>
                <el-col :sm="6" :xs="12">
                  <p class="summary-label">目标价格</p>
                  <p class="summary-value">{{ getField(record.final_decision, 'target_price') }}</p>
                </el-col>
              </el-row>
            </div>
          </el-card>
        </div>
      </template>
    </el-card>

    <el-drawer
      title="分析详情"
      :visible.sync="detailVisible"
      size="48%"
      :destroy-on-close="true"
      @close="closeDetail"
    >
      <el-skeleton v-if="detailLoading" :rows="6" animated />
      <template v-else-if="detailData">
        <div class="detail-scroll">
          <section class="detail-section compact">
            <h3>🏷️ 基本信息</h3>
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="股票代码">{{ detailData.symbol }}</el-descriptions-item>
              <el-descriptions-item label="股票名称">{{ detailData.stock_name }}</el-descriptions-item>
              <el-descriptions-item label="分析时间">{{ formatDate(detailData.analysis_date) }}</el-descriptions-item>
              <el-descriptions-item label="数据周期">{{ detailData.period }}</el-descriptions-item>
            </el-descriptions>
          </section>

          <section class="detail-section compact">
            <h3>📋 最终决策</h3>
            <div class="decision-badge" :class="ratingAlertType(getField(detailData.final_decision, 'rating', ''))">
              <span class="badge-title">{{ getField(detailData.final_decision, 'rating', '暂无评级') }}</span>
              <span class="badge-desc">AI 团队综合结论</span>
            </div>
            <div class="metric-grid">
              <div class="metric-card">
                <p class="metric-label">信心度</p>
                <el-progress
                  :percentage="confidencePercent(getField(detailData.final_decision, 'confidence_level', null))"
                  status="success"
                  :stroke-width="12"
                />
                <p class="metric-value">{{ getField(detailData.final_decision, 'confidence_level', '--') }}/10</p>
              </div>
              <div class="metric-card">
                <p class="metric-label">进场区间</p>
                <p class="metric-value highlight">{{ getField(detailData.final_decision, 'entry_range') }}</p>
                <p class="metric-desc">建议分批建仓</p>
              </div>
              <div class="metric-card">
                <p class="metric-label">止盈目标</p>
                <p class="metric-value">{{ getField(detailData.final_decision, 'take_profit') }}</p>
                <p class="metric-desc">安全获利点</p>
              </div>
              <div class="metric-card">
                <p class="metric-label">止损位置</p>
                <p class="metric-value danger">{{ getField(detailData.final_decision, 'stop_loss') }}</p>
                <p class="metric-desc">风险控制线</p>
              </div>
            </div>
            <el-card shadow="never" class="detail-card gradient success">
              <h4>🎯 操作建议</h4>
              <p>{{ getField(detailData.final_decision, 'operation_advice', '暂无建议') }}</p>
            </el-card>
            <el-card
              v-if="getField(detailData.final_decision, 'risk_warning', null)"
              shadow="never"
              class="detail-card gradient warning"
            >
              <h4>⚠️ 风险提示</h4>
              <p>{{ getField(detailData.final_decision, 'risk_warning') }}</p>
            </el-card>
          </section>

          <section v-if="agentTabs.length" class="detail-section compact">
            <h3>🤖 AI 分析师报告</h3>
            <el-tabs>
              <el-tab-pane
                v-for="agent in agentTabs"
                :key="agent.agent_name"
                :label="agent.agent_name"
              >
                <el-descriptions :column="1" border size="small">
                  <el-descriptions-item label="职责">{{ agent.agent_role || '—' }}</el-descriptions-item>
                  <el-descriptions-item label="分析时间">{{ agent.timestamp || '—' }}</el-descriptions-item>
                </el-descriptions>
                <el-card shadow="never" class="detail-card">
                  <p>{{ agent.analysis || '暂无内容' }}</p>
                </el-card>
              </el-tab-pane>
            </el-tabs>
          </section>
        </div>
      </template>
      <el-empty v-else description="暂无详情" />
    </el-drawer>
  </div>
</template>

<script>
import {
  fetchHistoryRecords,
  getHistoryRecord,
  deleteHistoryRecord,
  addHistoryRecordToMonitor
} from '@/api/history'

const FALLBACK_DATA = [
  {
    id: 1,
    symbol: '600519',
    stock_name: '贵州茅台',
    analysis_date: '2024-11-12 10:25',
    period: '6mo',
    rating: '买入',
    final_decision: {
      confidence_level: 8.5,
      target_price: '2050',
      entry_range: '1850 - 1900',
      take_profit: '2100',
      stop_loss: '1780',
      operation_advice: '长期看好，建议在回调时分批建仓。',
      risk_warning: '高估值带来的回撤风险，留意消费景气度。'
    },
    stock_info: {
      current_price: '1923.50',
      change_percent: 1.23
    }
  },
  {
    id: 2,
    symbol: 'AAPL',
    stock_name: 'Apple Inc.',
    analysis_date: '2024-11-10 21:40',
    period: '1y',
    rating: '持有',
    final_decision: {
      confidence_level: 7,
      target_price: '220',
      entry_range: '185 - 195',
      take_profit: '230',
      stop_loss: '175',
      operation_advice: '保持核心仓位，若跌破 180 可考虑降低仓位。',
      risk_warning: '关注供应链与宏观需求波动。'
    },
    stock_info: {
      current_price: '198.20',
      change_percent: -0.42
    }
  }
]

export default {
  name: 'HistoryIndex',
  data() {
    return {
      loading: false,
      records: [],
      filteredRecords: [],
      searchKeyword: '',
      fallbackMode: false,
      detailVisible: false,
      detailLoading: false,
      detailData: null,
      addingMonitorId: null
    }
  },
  computed: {
    statCards() {
      const total = this.records.length
      const buyCount = this.records.filter(r => (r.rating || '').includes('买')).length
      const holdCount = this.records.filter(r => (r.rating || '').includes('持')).length
      const sellCount = this.records.filter(r => (r.rating || '').includes('卖')).length
      return [
        { label: '总记录', value: total, desc: '含所有分析历史' },
        { label: '买入/强烈买入', value: buyCount, desc: '看多建议' },
        { label: '持有', value: holdCount, desc: '观望策略' },
        { label: '卖出/强烈卖出', value: sellCount, desc: '风险提示' }
      ]
    },
    agentTabs() {
      if (!this.detailData || !this.detailData.agents_results) return []
      return Object.values(this.detailData.agents_results)
    }
  },
  created() {
    this.loadRecords()
  },
  methods: {
    async loadRecords() {
      this.loading = true
      this.fallbackMode = false
      try {
        const res = await fetchHistoryRecords()
        this.records = Array.isArray(res?.items) ? res.items : (res || [])
        this.filteredRecords = [...this.records]
      } catch (error) {
        console.warn('Failed to fetch history records, use fallback data', error)
        this.records = FALLBACK_DATA
        this.filteredRecords = [...this.records]
        this.fallbackMode = true
        this.$message.warning('历史记录接口暂不可用，已加载示例数据')
      } finally {
        this.loading = false
      }
    },
    handleSearch() {
      if (!this.searchKeyword) {
        this.filteredRecords = [...this.records]
        return
      }
      const keyword = this.searchKeyword.trim().toLowerCase()
      this.filteredRecords = this.records.filter(record =>
        record.symbol?.toLowerCase().includes(keyword) ||
        record.stock_name?.toLowerCase().includes(keyword)
      )
    },
    resetFilter() {
      this.searchKeyword = ''
      this.handleSearch()
    },
    async viewDetail(record) {
      this.detailVisible = true
      this.detailLoading = true
      try {
        const detail = await getHistoryRecord(record.id)
        this.detailData = detail || record
      } catch (error) {
        console.warn('Failed to load detail, fallback to basic data', error)
        this.detailData = record
        this.$message.warning('未获取到完整详情，展示简要信息')
      } finally {
        this.detailLoading = false
      }
    },
    closeDetail() {
      this.detailVisible = false
      this.detailData = null
    },
    async deleteRecord(record) {
      try {
        await deleteHistoryRecord(record.id)
        this.$message.success('记录已删除')
        this.loadRecords()
      } catch (error) {
        console.error(error)
        this.$message.error('删除失败，请稍后重试')
      }
    },
    async addToMonitor(record) {
      this.addingMonitorId = record.id
      try {
        await addHistoryRecordToMonitor(record.id, {})
        this.$message.success('已提交监测任务')
      } catch (error) {
        console.warn('Add to monitor failed', error)
        this.$message.info('监测接口暂未实现，待后端接入后可使用')
      } finally {
        this.addingMonitorId = null
      }
    },
    ratingTagType(rating) {
      if (!rating) return 'info'
      if (rating.includes('买')) return 'success'
      if (rating.includes('卖')) return 'danger'
      if (rating.includes('持')) return 'warning'
      return 'info'
    },
    ratingAlertType(rating) {
      if (!rating) return 'info'
      if (rating.includes('买')) return 'success'
      if (rating.includes('卖')) return 'error'
      if (rating.includes('持')) return 'warning'
      return 'info'
    },
    getField(obj, key, fallback = '--') {
      if (!obj || obj[key] === undefined || obj[key] === null || obj[key] === '') {
        return fallback
      }
      return obj[key]
    },
    confidencePercent(value) {
      if (!value && value !== 0) return 0
      const num = Number(value)
      if (Number.isNaN(num)) return 0
      return Math.min(100, Math.max(0, num * 10))
    },
    formatDate(value) {
      if (!value) return '--'
      return value.replace('T', ' ')
    },
    formatPercent(value) {
      if (value === null || value === undefined || value === '') return '--'
      return `${Number(value).toFixed(2)}%`
    }
  }
}
</script>

<style scoped>
.history-page .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.subtitle {
  margin: 4px 0 0;
  color: #909399;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.toolbar {
  margin: 16px 0;
}

.stat-row {
  margin-bottom: 16px;
}

.stat-card {
  text-align: center;
  border-radius: 8px;
}

.stat-card .label {
  color: #909399;
  margin: 0;
}

.stat-card .value {
  margin: 8px 0 4px;
  font-size: 24px;
  color: #303133;
}

.stat-card .desc {
  margin: 0;
  color: #c0c4cc;
  font-size: 12px;
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.record-card {
  border-radius: 10px;
}

.record-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.record-title {
  margin: 0;
}

.record-meta {
  margin: 4px 0 0;
  color: #909399;
  font-size: 13px;
}

.record-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.record-body {
  margin-top: 12px;
}

.summary-label {
  color: #909399;
  margin: 0;
  font-size: 13px;
}

.summary-value {
  margin: 4px 0 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.detail-scroll {
  max-height: calc(100vh - 140px);
  overflow-y: auto;
  padding-right: 8px;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-card {
  margin-top: 12px;
  border-radius: 8px;
}

.detail-section.compact el-descriptions {
  background: #fff;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  grid-gap: 12px;
  margin-top: 12px;
}

.detail-card.warning {
  background: #fef0f0;
  border-color: #fde2e2;
}

.detail-card.gradient {
  color: #fff;
  border: none;
}

.detail-card.gradient.success {
  background: linear-gradient(120deg, #4facfe, #00f2fe);
}

.detail-card.gradient.warning {
  background: linear-gradient(120deg, #f6d365, #fda085);
}

.decision-badge {
  display: inline-flex;
  flex-direction: column;
  padding: 12px 18px;
  border-radius: 10px;
  margin-bottom: 12px;
  color: #fff;
  font-weight: 600;
}

.decision-badge.success {
  background: linear-gradient(120deg, #2af598, #009efd);
}

.decision-badge.warning {
  background: linear-gradient(120deg, #f7971e, #ffd200);
}

.decision-badge.error {
  background: linear-gradient(120deg, #ff5f6d, #ffc371);
}

.decision-badge.info {
  background: linear-gradient(120deg, #8ec5fc, #e0c3fc);
}

.badge-title {
  font-size: 18px;
}

.badge-desc {
  font-size: 12px;
  opacity: 0.85;
}

.metric-card {
  background: #f8f9fb;
  border-radius: 10px;
  padding: 12px;
  text-align: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.metric-label {
  margin: 0;
  color: #909399;
  font-size: 13px;
}

.metric-value {
  margin: 8px 0 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.metric-value.highlight {
  color: #16a085;
}

.metric-value.danger {
  color: #e74c3c;
}

.metric-desc {
  margin: 0;
  color: #c0c4cc;
  font-size: 12px;
}

.decision-row {
  margin-top: 12px;
}
</style>

