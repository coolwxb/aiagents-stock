<template>
  <div class="portfolio-page app-container">
    <el-card shadow="hover" class="portfolio-panel">
      <div slot="header" class="card-header">
        <div>
          <h2>📊 持仓定时分析</h2>
          <p class="subtitle">参照主界面布局，集中管理持仓、批量分析、定时任务与历史记录</p>
        </div>
        <div class="header-actions">
          <el-tag v-if="stocksFallback" type="warning" effect="plain">已加载示例持仓数据</el-tag>
          <el-button icon="el-icon-refresh" :loading="stocksLoading" @click="loadStocks">刷新</el-button>
          <el-button type="primary" icon="el-icon-plus" @click="openCreateDialog">添加持仓</el-button>
        </div>
      </div>

      <el-alert
        title="在该界面即可完成持仓管理、批量分析、定时配置与历史复盘，体验与 Streamlit 版本保持一致。"
        type="info"
        class="page-tip"
        show-icon
        :closable="false"
      />

      <el-tabs v-model="activeTab" class="portfolio-tabs" type="border-card" @tab-click="handleTabChange">
        <el-tab-pane label="📝 持仓管理" name="stocks">
          <el-row :gutter="16" class="stat-row">
            <el-col v-for="card in stockStats" :key="card.label" :xs="12" :sm="6" :md="6">
              <el-card shadow="never" class="stat-card">
                <p class="label">{{ card.label }}</p>
                <h3 class="value">{{ card.value }}</h3>
                <p class="desc">{{ card.desc }}</p>
              </el-card>
            </el-col>
          </el-row>

          <el-card shadow="never">
            <template v-if="!stocksLoading && stockList.length === 0">
              <el-empty description="暂未添加持仓股票">
                <el-button type="primary" @click="openCreateDialog">立即添加</el-button>
              </el-empty>
            </template>
            <el-table
              v-else
              v-loading="stocksLoading"
              :data="stockList"
              border
              class="portfolio-table"
              size="medium"
            >
              <el-table-column label="股票" min-width="200">
                <template slot-scope="{ row }">
                  <div class="stock-info">
                    <strong>{{ row.code }}</strong>
                    <span>{{ row.name || '未命名' }}</span>
                    <el-tag
                      v-if="row.note"
                      size="mini"
                      type="info"
                      effect="plain"
                      class="note-tag"
                    >
                      备注
                    </el-tag>
                  </div>
                  <p v-if="row.note" class="note-text">{{ row.note }}</p>
                </template>
              </el-table-column>
              <el-table-column label="成本价" width="120">
                <template slot-scope="{ row }">
                  {{ formatCurrency(row.cost_price) }}
                </template>
              </el-table-column>
              <el-table-column label="持仓数量" width="120">
                <template slot-scope="{ row }">
                  {{ formatQuantity(row.quantity) }}
                </template>
              </el-table-column>
              <el-table-column label="自动监测" width="120">
                <template slot-scope="{ row }">
                  <el-tag :type="row.auto_monitor ? 'success' : 'info'">
                    {{ row.auto_monitor ? '已启用' : '未启用' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="创建时间" width="170">
                <template slot-scope="{ row }">
                  {{ formatDate(row.created_at) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="160">
                <template slot-scope="{ row }">
                  <el-button size="mini" icon="el-icon-edit" @click="openEditDialog(row)">编辑</el-button>
                  <el-button
                    size="mini"
                    type="danger"
                    icon="el-icon-delete"
                    :loading="deleteLoadingId === row.id"
                    @click="deleteStock(row)"
                  >
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-tab-pane>

        <el-tab-pane label="🔄 批量分析" name="batch">
          <el-row :gutter="16">
            <el-col :md="10" :xs="24">
              <el-card shadow="never" class="section-card">
                <h3>分析参数</h3>
                <el-form label-width="100px" size="small" label-position="left">
                  <el-form-item label="分析模式">
                    <el-radio-group v-model="batchForm.mode">
                      <el-radio label="sequential">顺序分析（稳健）</el-radio>
                      <el-radio label="parallel">并行分析（快速）</el-radio>
                    </el-radio-group>
                  </el-form-item>
                  <el-form-item label="并行线程">
                    <el-input-number
                      v-model="batchForm.max_workers"
                      :min="2"
                      :max="10"
                      :precision="0"
                      :disabled="batchForm.mode === 'sequential'"
                    />
                  </el-form-item>
                  <el-form-item label="自动同步">
                    <el-switch
                      v-model="batchForm.auto_sync"
                      active-text="同步到监测"
                      inactive-text="仅保存记录"
                    />
                  </el-form-item>
                  <el-form-item label="完成通知">
                    <el-switch
                      v-model="batchForm.send_notification"
                      active-text="发送通知"
                      inactive-text="无需提醒"
                    />
                  </el-form-item>
                  <el-form-item>
                    <el-button
                      type="primary"
                      icon="el-icon-cpu"
                      :loading="batchLoading"
                      :disabled="stockList.length === 0"
                      @click="handleBatchAnalyze"
                    >
                      🚀 立即开始分析
                    </el-button>
                    <span v-if="stockList.length === 0" class="hint-text">请先添加持仓股票</span>
                  </el-form-item>
                </el-form>
              </el-card>
            </el-col>

            <el-col :md="14" :xs="24">
              <el-card shadow="never" class="section-card result-card">
                <div class="result-header">
                  <h3>分析概况</h3>
                  <el-tag v-if="batchFallback" type="warning" effect="plain">演示数据</el-tag>
                </div>
                <el-skeleton v-if="batchLoading" :rows="5" animated />
                <template v-else>
                  <el-empty v-if="!batchResult" description="尚未执行批量分析" />
                  <div v-else>
                    <el-row :gutter="16" class="stat-row compact">
                      <el-col v-for="summary in batchSummary" :key="summary.label" :sm="6">
                        <el-card shadow="never" class="stat-card mini">
                          <p class="label">{{ summary.label }}</p>
                          <h3 class="value">{{ summary.value }}</h3>
                          <p class="desc">{{ summary.desc }}</p>
                        </el-card>
                      </el-col>
                    </el-row>
                    <el-divider />
                    <el-collapse accordion>
                      <el-collapse-item
                        v-for="item in batchResult.results || []"
                        :key="item.code"
                        :name="item.code"
                      >
                        <template slot="title">
                          <div class="batch-item-title">
                            <span>{{ item.code }}</span>
                            <el-tag :type="ratingTagType(getDecision(item).rating)" size="mini">
                              {{ getDecision(item).rating || '未评级' }}
                            </el-tag>
                          </div>
                        </template>
                        <el-descriptions :column="2" border size="small">
                          <el-descriptions-item label="股票">
                            {{ getStockInfo(item).name || '--' }}
                          </el-descriptions-item>
                          <el-descriptions-item label="信心度">
                            {{ getDecision(item).confidence_level || '--' }}/10
                          </el-descriptions-item>
                          <el-descriptions-item label="进场区间">
                            {{ getDecision(item).entry_range || '--' }}
                          </el-descriptions-item>
                          <el-descriptions-item label="目标价格">
                            {{ getDecision(item).target_price || '--' }}
                          </el-descriptions-item>
                          <el-descriptions-item label="止盈位">
                            {{ getDecision(item).take_profit || '--' }}
                          </el-descriptions-item>
                          <el-descriptions-item label="止损位">
                            {{ getDecision(item).stop_loss || '--' }}
                          </el-descriptions-item>
                        </el-descriptions>
                        <el-card v-if="getDecision(item).operation_advice" shadow="never" class="detail-card">
                          <h4>🎯 操作建议</h4>
                          <p>{{ getDecision(item).operation_advice }}</p>
                        </el-card>
                      </el-collapse-item>
                    </el-collapse>
                  </div>
                </template>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>

        <el-tab-pane label="⏰ 定时任务" name="schedule">
          <el-row :gutter="16">
            <el-col :md="10" :xs="24">
              <el-card shadow="never" class="section-card">
                <div class="section-header">
                  <h3>每日分析时间</h3>
                  <el-tag v-if="scheduleFallback" type="warning" effect="plain">示例配置</el-tag>
                </div>
                <p class="hint-text">设置多个时间点，系统会在对应时间触发持仓分析</p>

                <div class="time-list">
                  <el-tag
                    v-for="time in scheduleForm.times"
                    :key="time"
                    closable
                    effect="plain"
                    @close="removeScheduleTime(time)"
                  >
                    {{ time }}
                  </el-tag>
                  <el-empty v-if="scheduleForm.times.length === 0" description="尚未配置时间" />
                </div>

                <div class="time-input">
                  <el-time-select
                    v-model="newScheduleTime"
                    placeholder="选择时间"
                    :picker-options="{
                      start: '08:00',
                      step: '00:05',
                      end: '23:55'
                    }"
                  />
                  <el-button type="primary" icon="el-icon-plus" @click="addScheduleTime">添加</el-button>
                </div>
              </el-card>
            </el-col>

            <el-col :md="14" :xs="24">
              <el-card shadow="never" class="section-card">
                <div class="section-header">
                  <h3>分析任务配置</h3>
                  <el-button
                    icon="el-icon-refresh"
                    :loading="scheduleLoading"
                    size="mini"
                    @click="loadSchedule"
                  >
                    刷新
                  </el-button>
                </div>
                <el-form label-width="120px" size="small" label-position="left">
                  <el-form-item label="分析模式">
                    <el-radio-group v-model="scheduleForm.analysis_mode" @change="markScheduleDirty">
                      <el-radio label="sequential">顺序分析</el-radio>
                      <el-radio label="parallel">并行分析</el-radio>
                    </el-radio-group>
                  </el-form-item>
                  <el-form-item label="并行线程">
                    <el-input-number
                      v-model="scheduleForm.max_workers"
                      :min="2"
                      :max="10"
                      :disabled="scheduleForm.analysis_mode === 'sequential'"
                      @change="markScheduleDirty"
                    />
                  </el-form-item>
                  <el-form-item label="自动同步">
                    <el-switch
                      v-model="scheduleForm.auto_sync"
                      active-text="同步到监测"
                      @change="markScheduleDirty"
                    />
                  </el-form-item>
                  <el-form-item label="发送通知">
                    <el-switch
                      v-model="scheduleForm.send_notification"
                      active-text="发送完成通知"
                      @change="markScheduleDirty"
                    />
                  </el-form-item>
                  <el-form-item>
                    <el-button
                      type="primary"
                      :disabled="!scheduleDirty"
                      :loading="scheduleSaving"
                      @click="saveSchedule"
                    >
                      💾 保存配置
                    </el-button>
                    <el-button type="text" @click="resetScheduleForm">恢复默认</el-button>
                  </el-form-item>
                </el-form>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>

        <el-tab-pane label="📈 分析历史" name="history">
          <el-card shadow="never" class="section-card">
            <div class="section-header">
              <h3>历史记录</h3>
              <div class="header-actions">
                <el-tag v-if="historyFallback" type="warning" effect="plain">示例记录</el-tag>
                <el-button icon="el-icon-refresh" :loading="historyLoading" @click="loadHistory">
                  刷新
                </el-button>
              </div>
            </div>
            <el-form :inline="true" size="small" class="history-toolbar">
              <el-form-item label="搜索">
                <el-input
                  v-model="historyKeyword"
                  placeholder="输入股票代码或名称"
                  clearable
                  @keyup.enter.native="handleHistorySearch"
                  @clear="handleHistorySearch"
                >
                  <el-button slot="append" icon="el-icon-search" @click="handleHistorySearch" />
                </el-input>
              </el-form-item>
            </el-form>

            <el-skeleton v-if="historyLoading" :rows="6" animated />
            <template v-else>
              <el-empty v-if="filteredHistory.length === 0" description="暂无历史记录" />
              <el-timeline v-else>
                <el-timeline-item
                  v-for="record in filteredHistory"
                  :key="record.id"
                  :timestamp="formatDate(record.analysis_time)"
                  placement="top"
                >
                  <el-card shadow="hover" class="history-card">
                    <div class="history-header">
                      <div>
                        <h4>{{ record.stock_name || '未命名' }}（{{ record.stock_code || record.symbol }}）</h4>
                        <el-tag :type="ratingTagType(record.rating)" size="mini">
                          {{ record.rating || '未知评级' }}
                        </el-tag>
                      </div>
                      <span v-if="record.confidence" class="confidence">
                        信心度 {{ Number(record.confidence).toFixed(1) }}/10
                      </span>
                    </div>
                    <el-row :gutter="12" class="history-grid">
                      <el-col :sm="6" :xs="12">
                        <p class="label">进场区间</p>
                        <p class="value">{{ formatRange(record.entry_min, record.entry_max) }}</p>
                      </el-col>
                      <el-col :sm="6" :xs="12">
                        <p class="label">目标价格</p>
                        <p class="value">{{ formatCurrency(record.target_price) }}</p>
                      </el-col>
                      <el-col :sm="6" :xs="12">
                        <p class="label">止盈位</p>
                        <p class="value">{{ formatCurrency(record.take_profit) }}</p>
                      </el-col>
                      <el-col :sm="6" :xs="12">
                        <p class="label">止损位</p>
                        <p class="value">{{ formatCurrency(record.stop_loss) }}</p>
                      </el-col>
                    </el-row>
                    <p v-if="record.summary" class="summary">{{ record.summary }}</p>
                  </el-card>
                </el-timeline-item>
              </el-timeline>
              <div v-if="showHistoryPagination" class="pagination-wrapper">
                <el-pagination
                  layout="prev, pager, next"
                  :current-page="historyPagination.page"
                  :page-size="historyPagination.page_size"
                  :total="historyPagination.total"
                  @current-change="handleHistoryPageChange"
                />
              </div>
            </template>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog
      :title="stockDialogTitle"
      :visible.sync="stockDialogVisible"
      width="520px"
      @closed="resetStockForm"
    >
      <el-form ref="stockFormRef" :model="stockForm" :rules="stockRules" label-width="100px">
        <el-form-item label="股票代码" prop="code">
          <el-input v-model="stockForm.code" placeholder="如 600519.SH / 000001.SZ / AAPL" />
        </el-form-item>
        <el-form-item label="股票名称">
          <el-input v-model="stockForm.name" placeholder="可选，留空将自动获取" />
        </el-form-item>
        <el-form-item label="成本价">
          <el-input-number
            v-model="stockForm.cost_price"
            :min="0"
            :step="0.01"
            :precision="2"
            controls-position="right"
            placeholder="可选"
          />
        </el-form-item>
        <el-form-item label="持仓数量">
          <el-input-number
            v-model="stockForm.quantity"
            :min="0"
            :step="100"
            controls-position="right"
            placeholder="可选"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="stockForm.note"
            type="textarea"
            :rows="3"
            maxlength="120"
            show-word-limit
            placeholder="记录买入理由、目标价等"
          />
        </el-form-item>
        <el-form-item label="自动监测">
          <el-switch
            v-model="stockForm.auto_monitor"
            active-text="分析完成后同步到实时监测"
          />
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="stockDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submittingStock" @click="submitStock">保存</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import {
  getPortfolioStocks,
  createPortfolioStock,
  updatePortfolioStock,
  deletePortfolioStock,
  batchAnalyzePortfolio,
  getPortfolioSchedule,
  setPortfolioSchedule,
  getPortfolioHistory
} from '@/api/portfolio'

const ROUTE_TAB_MAP = {
  PortfolioIndex: 'stocks',
  PortfolioAnalyze: 'batch',
  PortfolioSchedule: 'schedule',
  PortfolioHistory: 'history'
}

const TAB_ROUTE_MAP = Object.entries(ROUTE_TAB_MAP).reduce((acc, [routeName, tab]) => {
  acc[tab] = routeName
  return acc
}, {})

const FALLBACK_STOCKS = [
  {
    id: 1,
    code: '600519.SH',
    name: '贵州茅台',
    cost_price: 1800,
    quantity: 200,
    note: '核心持仓，长线价值股',
    auto_monitor: true,
    created_at: '2024-10-10 09:30'
  },
  {
    id: 2,
    code: 'AAPL',
    name: 'Apple Inc.',
    cost_price: 185,
    quantity: 100,
    note: '美股科技龙头，关注新品周期',
    auto_monitor: true,
    created_at: '2024-10-11 22:15'
  },
  {
    id: 3,
    code: '00700.HK',
    name: '腾讯控股',
    cost_price: 320,
    quantity: 300,
    note: '港股重仓，等待估值修复',
    auto_monitor: false,
    created_at: '2024-10-12 14:05'
  }
]

const FALLBACK_BATCH_RESULT = {
  success: true,
  mode: 'sequential',
  total: 3,
  succeeded: 3,
  failed: 0,
  elapsed_time: 320,
  results: [
    {
      code: '600519.SH',
      result: {
        success: true,
        stock_info: { name: '贵州茅台' },
        final_decision: {
          rating: '买入',
          confidence_level: 8.6,
          entry_range: '1780 - 1840',
          target_price: '2100',
          take_profit: '2120',
          stop_loss: '1700',
          operation_advice: '消费龙头，回调即是加仓机会，建议分批布局。'
        }
      }
    },
    {
      code: 'AAPL',
      result: {
        success: true,
        stock_info: { name: 'Apple Inc.' },
        final_decision: {
          rating: '持有',
          confidence_level: 7.2,
          entry_range: '180 - 188',
          target_price: '220',
          take_profit: '228',
          stop_loss: '172',
          operation_advice: '新品周期尚需验证，保持核心仓位即可。'
        }
      }
    },
    {
      code: '00700.HK',
      result: {
        success: true,
        stock_info: { name: '腾讯控股' },
        final_decision: {
          rating: '买入',
          confidence_level: 7.8,
          entry_range: '300 - 320',
          target_price: '365',
          take_profit: '370',
          stop_loss: '285',
          operation_advice: '游戏与广告复苏，建议低吸等待估值修复。'
        }
      }
    }
  ]
}

const FALLBACK_SCHEDULE = {
  times: ['09:35', '13:05', '15:05'],
  analysis_mode: 'sequential',
  max_workers: 3,
  auto_sync: true,
  send_notification: true
}

const FALLBACK_HISTORY = [
  {
    id: 1,
    stock_code: '600519.SH',
    stock_name: '贵州茅台',
    analysis_time: '2024-11-12 17:05',
    rating: '买入',
    confidence: 8.6,
    entry_min: 1780,
    entry_max: 1840,
    target_price: 2100,
    take_profit: 2120,
    stop_loss: 1700,
    summary: '白酒板块回暖，建议持有核心仓位，关注消费修复节奏。'
  },
  {
    id: 2,
    stock_code: 'AAPL',
    stock_name: 'Apple Inc.',
    analysis_time: '2024-11-11 21:20',
    rating: '持有',
    confidence: 7,
    entry_min: 180,
    entry_max: 188,
    target_price: 220,
    take_profit: 228,
    stop_loss: 172,
    summary: '宏观需求承压，维持持有评级，等待 Vision Pro 生态落地。'
  },
  {
    id: 3,
    stock_code: '00700.HK',
    stock_name: '腾讯控股',
    analysis_time: '2024-11-10 16:05',
    rating: '买入',
    confidence: 7.8,
    entry_min: 300,
    entry_max: 320,
    target_price: 365,
    take_profit: 370,
    stop_loss: 285,
    summary: '基本面改善趋势明确，建议逢低布局中长期机会。'
  }
]

export default {
  name: 'PortfolioLayout',
  props: {
    defaultTab: {
      type: String,
      default: 'stocks'
    }
  },
  data() {
    return {
      activeTab: ROUTE_TAB_MAP[this.$route.name] || this.defaultTab || 'stocks',
      stockList: [],
      stocksLoading: false,
      stocksFallback: false,
      stockDialogVisible: false,
      stockDialogTitle: '添加持仓',
      stockForm: this.getEmptyStockForm(),
      stockRules: {
        code: [{ required: true, message: '请输入股票代码', trigger: 'blur' }]
      },
      editingStockId: null,
      submittingStock: false,
      deleteLoadingId: null,
      batchForm: {
        mode: 'sequential',
        max_workers: 3,
        auto_sync: true,
        send_notification: true
      },
      batchLoading: false,
      batchResult: null,
      batchFallback: false,
      scheduleForm: { ...FALLBACK_SCHEDULE },
      scheduleLoading: false,
      scheduleFallback: false,
      scheduleDirty: false,
      scheduleSaving: false,
      newScheduleTime: '',
      historyLoading: false,
      historyList: [],
      historyFallback: false,
      historyKeyword: '',
      historyPagination: {
        page: 1,
        page_size: 10,
        total: 0
      }
    }
  },
  computed: {
    stockStats() {
      const total = this.stockList.length
      const autoMonitor = this.stockList.filter(item => item.auto_monitor).length
      const withPosition = this.stockList.filter(item => Number(item.quantity || 0) > 0).length
      const cost = this.stockList.reduce((sum, item) => {
        const price = Number(item.cost_price || 0)
        const qty = Number(item.quantity || 0)
        return sum + price * qty
      }, 0)
      return [
        { label: '持仓股票数', value: total, desc: '当前管理的股票' },
        { label: '自动同步', value: autoMonitor, desc: '启用实时监测的股票' },
        { label: '已填写持仓', value: withPosition, desc: '填写了成本或数量' },
        { label: '估算持仓成本', value: cost ? `¥${this.formatNumber(cost)}` : '—', desc: '成本 × 数量' }
      ]
    },
    batchSummary() {
      if (!this.batchResult) return []
      return [
        { label: '总股票数', value: this.batchResult.total || 0, desc: '参与批量分析' },
        { label: '成功', value: this.batchResult.succeeded || 0, desc: '完成 AI 分析' },
        { label: '失败', value: this.batchResult.failed || 0, desc: '需人工复查' },
        {
          label: '耗时',
          value: this.batchResult.elapsed_time ? `${this.batchResult.elapsed_time}s` : '--',
          desc: '整体分析耗时'
        }
      ]
    },
    filteredHistory() {
      if (!this.historyKeyword || !this.historyFallback) {
        return this.historyList
      }
      const keyword = this.historyKeyword.trim().toLowerCase()
      return this.historyList.filter(
        item =>
          (item.stock_code || item.symbol || '').toLowerCase().includes(keyword) ||
          (item.stock_name || '').toLowerCase().includes(keyword)
      )
    },
    showHistoryPagination() {
      return !this.historyFallback && this.historyPagination.total > this.historyPagination.page_size
    }
  },
  watch: {
    '$route.name': {
      immediate: true,
      handler(name) {
        const tab = ROUTE_TAB_MAP[name]
        if (tab && tab !== this.activeTab) {
          this.activeTab = tab
        }
      }
    },
    defaultTab(val) {
      if (!ROUTE_TAB_MAP[this.$route.name] && val && val !== this.activeTab) {
        this.activeTab = val
      }
    }
  },
  created() {
    if (!this.activeTab) {
      this.activeTab = 'stocks'
    }
    this.bootstrap()
  },
  methods: {
    bootstrap() {
      this.loadStocks()
      this.loadSchedule()
      if (this.activeTab === 'history') {
        this.loadHistory()
      }
    },
    handleTabChange(tab) {
      const name = tab.name
      this.syncRouteByTab(name)
      if (name === 'history' && this.historyList.length === 0) {
        this.loadHistory()
      }
    },
    syncRouteByTab(tabName) {
      const routeName = TAB_ROUTE_MAP[tabName]
      if (routeName && routeName !== this.$route.name) {
        this.$router.replace({ name: routeName })
      }
    },
    async loadStocks() {
      this.stocksLoading = true
      this.stocksFallback = false
      try {
        const res = await getPortfolioStocks()
        const items = Array.isArray(res?.items) ? res.items : Array.isArray(res) ? res : []
        this.stockList = items.length ? items : []
        if (!items.length) {
          this.stockList = []
        }
      } catch (error) {
        console.warn('Failed to load portfolio stocks, fallback to demo data', error)
        this.stockList = FALLBACK_STOCKS
        this.stocksFallback = true
        this.$message.warning('持仓接口暂不可用，已加载示例数据')
      } finally {
        this.stocksLoading = false
      }
    },
    openCreateDialog() {
      this.stockDialogTitle = '添加持仓'
      this.stockForm = this.getEmptyStockForm()
      this.editingStockId = null
      this.stockDialogVisible = true
    },
    openEditDialog(stock) {
      this.stockDialogTitle = `编辑 ${stock.code}`
      this.stockForm = {
        code: stock.code,
        name: stock.name,
        cost_price: stock.cost_price,
        quantity: stock.quantity,
        note: stock.note,
        auto_monitor: Boolean(stock.auto_monitor)
      }
      this.editingStockId = stock.id
      this.stockDialogVisible = true
    },
    getEmptyStockForm() {
      return {
        code: '',
        name: '',
        cost_price: null,
        quantity: null,
        note: '',
        auto_monitor: true
      }
    },
    resetStockForm() {
      this.$nextTick(() => {
        if (this.$refs.stockFormRef) {
          this.$refs.stockFormRef.resetFields()
        }
      })
      this.stockForm = this.getEmptyStockForm()
      this.editingStockId = null
    },
    submitStock() {
      this.$refs.stockFormRef.validate(async valid => {
        if (!valid) return
        this.submittingStock = true
        const payload = {
          ...this.stockForm,
          code: this.stockForm.code?.trim(),
          name: this.stockForm.name?.trim()
        }
        try {
          if (this.editingStockId) {
            await updatePortfolioStock(this.editingStockId, payload)
            this.$message.success('持仓已更新')
          } else {
            await createPortfolioStock(payload)
            this.$message.success('持仓已添加')
          }
          this.stockDialogVisible = false
          this.loadStocks()
        } catch (error) {
          console.warn('Save portfolio stock failed', error)
          this.$message.info('持仓接口暂未接入，当前为前端演示数据')
          if (this.stocksFallback) {
            if (this.editingStockId) {
              this.stockList = this.stockList.map(item =>
                item.id === this.editingStockId ? { ...item, ...payload } : item
              )
            } else {
              this.stockList = [
                {
                  ...payload,
                  id: Date.now(),
                  created_at: new Date().toISOString().slice(0, 16)
                },
                ...this.stockList
              ]
            }
            this.stockDialogVisible = false
          }
        } finally {
          this.submittingStock = false
        }
      })
    },
    async deleteStock(stock) {
      try {
        await this.$confirm(`确认删除 ${stock.code} 吗？该操作不可恢复`, '提示', {
          type: 'warning'
        })
      } catch {
        return
      }
      this.deleteLoadingId = stock.id
      try {
        await deletePortfolioStock(stock.id)
        this.$message.success('持仓已删除')
        this.loadStocks()
      } catch (error) {
        console.warn('Delete portfolio stock failed', error)
        this.$message.info('后端暂未实现删除接口，当前为前端演示数据')
        if (this.stocksFallback) {
          this.stockList = this.stockList.filter(item => item.id !== stock.id)
        }
      } finally {
        this.deleteLoadingId = null
      }
    },
    async handleBatchAnalyze() {
      this.batchLoading = true
      this.batchFallback = false
      try {
        const res = await batchAnalyzePortfolio(this.batchForm)
        this.batchResult = res
      } catch (error) {
        console.warn('Batch analyze failed, fallback to demo data', error)
        this.batchResult = FALLBACK_BATCH_RESULT
        this.batchFallback = true
        this.$message.info('批量分析接口暂不可用，展示示例结果')
      } finally {
        this.batchLoading = false
      }
    },
    getDecision(item) {
      return item?.result?.final_decision || {}
    },
    getStockInfo(item) {
      return item?.result?.stock_info || {}
    },
    ratingTagType(rating) {
      if (!rating) return 'info'
      if (rating.includes('买')) return 'success'
      if (rating.includes('卖')) return 'danger'
      if (rating.includes('持')) return 'warning'
      return 'info'
    },
    async loadSchedule() {
      this.scheduleLoading = true
      this.scheduleFallback = false
      try {
        const res = await getPortfolioSchedule()
        if (res) {
          this.scheduleForm = {
            times: res.times || res || [],
            analysis_mode: res.analysis_mode || 'sequential',
            max_workers: res.max_workers || 3,
            auto_sync: res.auto_sync !== undefined ? res.auto_sync : true,
            send_notification: res.send_notification !== undefined ? res.send_notification : true
          }
        } else {
          this.scheduleForm = { ...FALLBACK_SCHEDULE }
        }
        this.scheduleDirty = false
      } catch (error) {
        console.warn('Load schedule failed, fallback to demo config', error)
        this.scheduleForm = { ...FALLBACK_SCHEDULE }
        this.scheduleFallback = true
        this.scheduleDirty = false
        this.$message.info('定时配置接口暂不可用，已加载示例配置')
      } finally {
        this.scheduleLoading = false
      }
    },
    addScheduleTime() {
      if (!this.newScheduleTime) {
        this.$message.warning('请选择一个时间点')
        return
      }
      if (this.scheduleForm.times.includes(this.newScheduleTime)) {
        this.$message.info('该时间已存在')
        return
      }
      this.scheduleForm.times.push(this.newScheduleTime)
      this.scheduleForm.times.sort()
      this.newScheduleTime = ''
      this.markScheduleDirty()
    },
    removeScheduleTime(time) {
      this.scheduleForm.times = this.scheduleForm.times.filter(item => item !== time)
      this.markScheduleDirty()
    },
    markScheduleDirty() {
      this.scheduleDirty = true
    },
    async saveSchedule() {
      if (!this.scheduleForm.times.length) {
        this.$message.warning('请至少设置一个分析时间')
        return
      }
      this.scheduleSaving = true
      try {
        await setPortfolioSchedule(this.scheduleForm)
        this.scheduleDirty = false
        this.$message.success('定时配置已保存')
      } catch (error) {
        console.warn('Save schedule failed', error)
        this.scheduleFallback = true
        this.scheduleDirty = false
        this.$message.info('定时配置接口暂未接入，当前配置仅在前端示例中保存')
      } finally {
        this.scheduleSaving = false
      }
    },
    resetScheduleForm() {
      this.scheduleForm = { ...FALLBACK_SCHEDULE }
      this.scheduleDirty = true
      this.$message.success('已恢复默认配置')
    },
    async loadHistory() {
      this.historyLoading = true
      this.historyFallback = false
      try {
        const params = {
          stock_code: this.historyKeyword || undefined,
          page: this.historyPagination.page,
          page_size: this.historyPagination.page_size
        }
        const res = await getPortfolioHistory(params)
        const items = Array.isArray(res?.items) ? res.items : Array.isArray(res) ? res : []
        this.historyList = items
        if (typeof res?.total === 'number') {
          this.historyPagination.total = res.total
        } else {
          this.historyPagination.total = items.length
        }
      } catch (error) {
        console.warn('Load portfolio history failed, fallback to demo data', error)
        this.historyList = FALLBACK_HISTORY
        this.historyPagination.total = FALLBACK_HISTORY.length
        this.historyFallback = true
        this.$message.info('历史接口暂不可用，展示示例记录')
      } finally {
        this.historyLoading = false
      }
    },
    handleHistorySearch() {
      if (this.historyFallback) {
        return
      }
      this.historyPagination.page = 1
      this.loadHistory()
    },
    handleHistoryPageChange(page) {
      this.historyPagination.page = page
      if (!this.historyFallback) {
        this.loadHistory()
      }
    },
    formatRange(min, max) {
      if (
        min === undefined ||
        min === null ||
        max === undefined ||
        max === null ||
        min === '' ||
        max === ''
      ) {
        return '--'
      }
      const left = this.formatCurrency(min)
      const right = this.formatCurrency(max)
      return `${left} - ${right}`
    },
    formatCurrency(value) {
      if (value === null || value === undefined || value === '') return '--'
      const num = Number(value)
      if (Number.isNaN(num)) return value
      return `¥${num.toFixed(2)}`
    },
    formatQuantity(value) {
      if (value === null || value === undefined || value === '') return '--'
      return `${Number(value)} 股`
    },
    formatDate(value) {
      if (!value) return '--'
      return String(value).replace('T', ' ')
    },
    formatNumber(value) {
      if (!value && value !== 0) return '0'
      return Number(value).toLocaleString()
    }
  }
}
</script>

<style scoped>
.portfolio-page {
  padding-bottom: 24px;
}

.portfolio-panel {
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
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.page-tip {
  margin-bottom: 16px;
}

.portfolio-tabs ::v-deep(.el-tabs__content) {
  padding: 0;
}

.stat-row {
  margin: 16px 0;
}

.stat-card {
  text-align: center;
  border-radius: 10px;
}

.stat-card .label {
  margin: 0;
  color: #909399;
}

.stat-card .value {
  margin: 6px 0;
  font-size: 24px;
  color: #303133;
}

.stat-card .desc {
  margin: 0;
  color: #c0c4cc;
  font-size: 12px;
}

.stat-card.mini .value {
  font-size: 20px;
}

.section-card {
  margin-bottom: 16px;
  border-radius: 10px;
}

.stock-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.note-text {
  margin: 4px 0 0;
  color: #909399;
  font-size: 12px;
}

.hint-text {
  color: #909399;
  font-size: 12px;
  margin-left: 12px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.batch-item-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.detail-card {
  margin-top: 12px;
  border-radius: 8px;
}

.time-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  min-height: 48px;
  margin-bottom: 16px;
}

.time-input {
  display: flex;
  gap: 8px;
  align-items: center;
}

.history-toolbar {
  margin-bottom: 12px;
}

.history-card {
  border-radius: 12px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.history-grid .label {
  margin: 0;
  color: #909399;
}

.history-grid .value {
  margin: 4px 0 0;
  font-weight: 600;
}

.summary {
  margin-top: 12px;
  color: #606266;
}

.pagination-wrapper {
  margin-top: 16px;
  text-align: right;
}

.dialog-footer {
  text-align: right;
}
</style>
