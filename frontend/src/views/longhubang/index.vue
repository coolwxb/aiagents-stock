<template>
  <div class="lhb-page app-container">
    <el-card shadow="hover" class="hero-card">
      <div class="hero-content">
        <div>
          <p class="hero-eyebrow">Multi-Agent Dragon Tiger</p>
          <h2>🐲 智瞰龙虎 · 游资多维洞察</h2>
          <div class="hero-tags">
            <el-tag effect="dark" type="success">游资席位</el-tag>
            <el-tag effect="dark" type="warning">AI评分</el-tag>
            <el-tag effect="dark" type="info">PDF 报告</el-tag>
          </div>
        </div>
        <div class="hero-actions">
          <div class="action-block">
            <p class="label">最新分析时间</p>
            <p class="value">{{ (analysisResult && analysisResult.timestamp) || '尚未分析' }}</p>
            <p class="desc">每日 17:40 同步龙虎榜数据</p>
          </div>
          <div class="action-block">
            <p class="label">AI 模型</p>
            <el-select v-model="selectedModel" placeholder="选择模型" size="large" class="hero-select">
              <el-option v-for="item in modelOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </div>
        </div>
      </div>
    </el-card>

    <el-card shadow="hover" class="module-card">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="📊 龙虎榜分析" name="analysis">
          <el-form label-position="top" class="analysis-form">
            <el-row :gutter="16">
              <el-col :xs="24" :md="8">
                <el-form-item label="分析模式">
                  <el-radio-group v-model="analysisMode">
                    <el-radio-button label="date">指定日期</el-radio-button>
                    <el-radio-button label="recent">最近N天</el-radio-button>
                  </el-radio-group>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :md="8">
                <el-form-item v-if="analysisMode === 'date'" label="龙虎榜日期">
                  <el-date-picker
                    v-model="selectedDateObj"
                    type="date"
                    placeholder="选择日期"
                    format="yyyy-MM-dd"
                    value-format="yyyy-MM-dd"
                    :disabled-date="disableFutureDate"
                    style="width: 100%"
                  />
                </el-form-item>
                <el-form-item v-else label="最近天数">
                  <el-input-number
                    v-model="recentDays"
                    :min="1"
                    :max="10"
                    :step="1"
                    controls-position="right"
                    class="full-width"
                  />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :md="8">
                <el-form-item label="执行操作">
                  <div class="form-actions">
                    <el-button
                      v-if="!analysisLoading"
                      type="primary"
                      @click="handleAnalyze"
                    >
                      🚀 开始分析
                    </el-button>
                    <el-button
                      v-else
                      type="info"
                      disabled
                    >
                      ⏳ 分析中...
                    </el-button>
                    <el-button :disabled="!analysisResult || analysisLoading" @click="clearResult">清除结果</el-button>
                  </div>
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>

          <el-divider />

          <!-- 分析进度显示 -->
          <div v-if="analysisLoading" class="progress-section">
            <el-card shadow="never" class="progress-card">
              <div class="progress-header">
                <span class="progress-title">🔄 分析进行中...</span>
                <span class="progress-percent">{{ analysisProgress }}%</span>
              </div>
              <p class="task-id" v-if="taskId">任务ID: {{ taskId }}</p>
              <el-progress
                :percentage="analysisProgress"
                :stroke-width="12"
                :show-text="false"
                status="success"
              />
              <p class="progress-message">{{ analysisMessage }}</p>
              <div class="progress-logs" v-if="analysisLogs.length > 0">
                <div class="logs-header">
                  <span>📋 实时日志</span>
                  <el-button size="mini" type="text" @click="analysisLogs = []">清空</el-button>
                </div>
                <div class="logs-container" ref="logsContainer">
                  <p
                    v-for="(log, index) in analysisLogs"
                    :key="index"
                    :class="['log-item', `log-${log.level}`]"
                  >
                    <span class="log-time">{{ log.time }}</span>
                    <span class="log-text">{{ log.message }}</span>
                  </p>
                </div>
              </div>
            </el-card>
          </div>

          <el-row v-if="analysisResult" :gutter="16" class="quick-stats">
            <el-col v-for="card in quickCards" :key="card.label" :xs="12" :sm="6">
              <el-card shadow="never" class="stat-card">
                <p class="label">{{ card.label }}</p>
                <p class="value">{{ card.value }}</p>
                <p class="desc">{{ card.desc }}</p>
              </el-card>
            </el-col>
          </el-row>

          <el-empty
            v-if="!analysisResult"
            description="点击“开始分析”或从历史报告加载一份结果，即可查看 AI 智瞰龙虎。"
          />

          <div v-else class="analysis-content">
            <el-alert
              type="success"
              :closable="false"
              class="inline-alert"
              :title="`分析完成于 ${analysisResult.timestamp}`"
            />

            <section class="sub-section">
              <div class="section-header">
                <h3>🏆 AI 智能评分排名</h3>
                <el-button size="mini" icon="el-icon-download" @click="handleExport('pdf')">
                  导出 PDF
                </el-button>
              </div>
              <el-table :data="scoringTop10" border stripe size="small" empty-text="暂无评分数据">
                <el-table-column prop="rank" label="排名" width="70" />
                <el-table-column prop="name" label="股票名称" />
                <el-table-column prop="code" label="代码" width="110" />
                <el-table-column
                  prop="score"
                  label="综合评分"
                  width="120"
                  :formatter="formatScoreCell"
                />
                <el-table-column prop="eliteSeats" label="顶级游资" width="110" />
                <el-table-column prop="buySeats" label="买方席位" width="110" />
                <el-table-column prop="orgInvolved" label="机构共振" width="110" />
                <el-table-column
                  prop="netInflow"
                  label="净流入"
                  width="140"
                  :formatter="formatCurrencyCell"
                />
              </el-table>
            </section>

            <section class="sub-section">
              <div class="section-header">
                <h3>🎯 AI 推荐股票</h3>
                <el-tag type="info">结合 5 位分析师综合打分</el-tag>
              </div>
              <div class="recommend-grid">
                <el-card
                  v-for="stock in recommendedList"
                  :key="stock.code"
                  shadow="hover"
                  class="recommend-card"
                >
                  <div class="card-heading">
                    <div>
                      <h4>{{ stock.rank }}. {{ stock.name }} · {{ stock.code }}</h4>
                      <div class="tag-list">
                        <el-tag v-for="tag in stock.tags" :key="tag" size="mini" type="success">{{ tag }}</el-tag>
                      </div>
                    </div>
                    <div class="score-block">
                      <p class="label">净流入</p>
                      <p class="value">{{ formatCurrency(stock.netInflow) }}</p>
                      <p class="desc">{{ stock.confidence }} · 持有 {{ stock.holdPeriod }}</p>
                    </div>
                  </div>
                  <p class="reason">推荐理由：{{ stock.reason }}</p>
                  <p class="risk">风险提示：{{ stock.risk }}</p>
                  <div class="meta-row">
                    <span>核心游资：{{ stock.youzi }}（{{ stock.youziStyle }}）</span>
                    <span>目标价：{{ stock.targetPrice }} ｜ 止损：{{ stock.stopLoss }}</span>
                  </div>
                </el-card>
              </div>
            </section>

            <section class="sub-section">
              <h3>🤖 AI 分析师报告</h3>
              <el-collapse accordion>
                <el-collapse-item
                  v-for="agent in agentList"
                  :key="agent.agent_name"
                  :title="`${agent.agent_name} · ${agent.agent_role}`"
                >
                  <p class="focus">
                    关注领域：{{ (agent.focus_areas && agent.focus_areas.join('、')) || '暂无' }}
                  </p>
                  <p class="timestamp">分析时间：{{ agent.timestamp }}</p>
                  <div class="analysis-content-md" v-html="renderMarkdown(agent.analysis)"></div>
                </el-collapse-item>
              </el-collapse>
            </section>

            <section class="sub-section">
              <h3>📊 龙虎榜数据详情</h3>
              <div class="data-grid">
                <div>
                  <h4>🏆 活跃游资 TOP10</h4>
                  <el-table :data="topYouziList" border size="small" height="320px">
                    <el-table-column prop="rank" label="#" width="60" />
                    <el-table-column prop="name" label="游资" />
                    <el-table-column
                      prop="netInflow"
                      label="净流入"
                      width="140"
                      :formatter="formatCurrencyCell"
                    />
                  </el-table>
                </div>
                <div>
                  <h4>📈 资金净流入 TOP20 股票</h4>
                  <el-table :data="topStockList" border size="small" height="320px">
                    <el-table-column prop="code" label="代码" width="100" />
                    <el-table-column prop="name" label="股票" />
                    <el-table-column
                      prop="net_inflow"
                      label="净流入"
                      width="140"
                      :formatter="formatCurrencyCell"
                    />
                  </el-table>
                </div>
                <div>
                  <h4>🔥 热门概念 TOP20</h4>
                  <el-table :data="hotConceptList" border size="small" height="320px">
                    <el-table-column prop="rank" label="#" width="60" />
                    <el-table-column prop="name" label="概念" />
                    <el-table-column prop="count" label="出现次数" width="120" />
                  </el-table>
                </div>
              </div>
            </section>
          </div>
        </el-tab-pane>

        <el-tab-pane label="📚 历史报告" name="history">
          <div class="history-header">
            <el-input
              v-model="historySearch"
              placeholder="输入关键词过滤"
              prefix-icon="el-icon-search"
              clearable
              class="history-search"
            />
            <el-button icon="el-icon-refresh" :loading="historyLoading" @click="loadHistory">刷新</el-button>
          </div>
          <el-empty v-if="filteredHistory.length === 0" description="暂无历史报告，请先执行龙虎榜分析">
            <el-button type="primary" size="small" @click="activeTab = 'analysis'">
              去分析
            </el-button>
          </el-empty>
          <el-timeline v-else>
            <el-timeline-item
              v-for="item in filteredHistory"
              :key="item.id"
              :timestamp="item.created_at"
              placement="top"
            >
              <el-card shadow="never" class="history-card">
                <div class="card-header">
                  <div>
                    <h4>报告 #{{ item.id }}</h4>
                    <p class="subtitle">{{ item.summary }}</p>
                    <p class="tagline">数据区间：{{ item.data_date_range }}</p>
                  </div>
                  <div class="history-metrics">
                    <el-tag type="success">评分 {{ formatPercent(item.confidence_score) }}</el-tag>
                    <el-tag type="warning">{{ item.market_outlook }}</el-tag>
                  </div>
                </div>
                <div class="history-actions">
                  <el-button size="mini" type="primary" icon="el-icon-view" @click="loadHistoryItem(item)">
                    加载到分析视图
                  </el-button>
                </div>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </el-tab-pane>

        <el-tab-pane label="📈 数据统计" name="stats">
          <el-skeleton v-if="statsLoading" :rows="6" animated />
          <template v-else>
            <!-- 统计概览卡片 -->
            <el-row v-if="statsCards.length > 0" :gutter="16" class="quick-stats">
              <el-col v-for="card in statsCards" :key="card.label" :xs="12" :sm="6">
                <el-card shadow="never" class="stat-card">
                  <p class="label">{{ card.label }}</p>
                  <p class="value">{{ card.value }}</p>
                  <p class="desc">{{ card.desc }}</p>
                </el-card>
              </el-col>
            </el-row>
            <el-alert
              v-if="statsSummary && statsSummary.date_range && statsSummary.date_range.start"
              :closable="false"
              type="info"
              class="inline-alert"
              :title="`数据范围：${statsSummary.date_range.start} ~ ${statsSummary.date_range.end}`"
            />

            <!-- 无数据提示 -->
            <el-empty
              v-if="!statsSummary || statsSummary.total_records === 0"
              description="暂无龙虎榜统计数据，请先执行龙虎榜分析以获取数据"
            >
              <el-button type="primary" size="small" @click="activeTab = 'analysis'">
                去分析
              </el-button>
            </el-empty>

            <template v-else>
              <section class="sub-section">
                <h3>🏅 历史活跃游资 (近30天)</h3>
                <el-table :data="statsTopYouzi" border size="small" empty-text="暂无游资数据">
                  <el-table-column prop="name" label="游资名称" />
                  <el-table-column prop="trade_count" label="上榜次数" width="120" />
                  <el-table-column
                    prop="net_inflow"
                    label="总净流入"
                    width="160"
                    :formatter="formatCurrencyCell"
                  />
                </el-table>
              </section>
              <section class="sub-section">
                <h3>📈 历史热门股票 (近30天)</h3>
                <el-table :data="statsTopStocks" border size="small" empty-text="暂无股票数据">
                  <el-table-column prop="code" label="代码" width="110" />
                  <el-table-column prop="name" label="股票名称" />
                  <el-table-column prop="youzi_count" label="游资数量" width="120" />
                  <el-table-column
                    prop="net_inflow"
                    label="总净流入"
                    width="160"
                    :formatter="formatCurrencyCell"
                  />
                </el-table>
              </section>
              <section class="sub-section">
                <h3>🏆 综合评分 TOP20</h3>
                <el-table :data="statsScoreboard" border stripe size="small" empty-text="暂无评分数据，请先执行龙虎榜分析">
                  <el-table-column prop="rank" label="排名" width="70" />
                  <el-table-column prop="name" label="股票" />
                  <el-table-column prop="code" label="代码" width="110" />
                  <el-table-column
                    prop="score"
                    label="综合评分"
                    width="120"
                    :formatter="formatScoreCell"
                  />
                  <el-table-column
                    prop="netInflow"
                    label="净流入"
                    width="140"
                    :formatter="formatCurrencyCell"
                  />
                </el-table>
              </section>
            </template>
          </template>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script>
import dayjs from 'dayjs'
import { marked } from 'marked'
import {
  analyzeLonghubang,
  getLonghubangHistory,
  getLonghubangScoring,
  getLonghubangStatistics,
  getTopYouzi,
  getTopStocks,
  generateLonghubangPDF
} from '@/api/longhubang'

// 配置 marked 选项
marked.setOptions({
  breaks: true, // 支持换行
  gfm: true // 支持 GitHub 风格 Markdown
})

const MODEL_OPTIONS = [
  { value: 'deepseek-chat', label: 'DeepSeek V3 Chat（默认）' },
  { value: 'deepseek-reasoner', label: 'DeepSeek-R1 Reasoner' },
  { value: 'openai-gpt4o', label: 'OpenAI GPT-4o' }
]

export default {
  name: 'LonghubangIndex',
  data() {
    return {
      modelOptions: MODEL_OPTIONS,
      selectedModel: MODEL_OPTIONS[0].value,
      // WebSocket 相关
      websocket: null,
      taskId: null,
      analysisProgress: 0,
      analysisMessage: '准备开始分析...',
      analysisLogs: [],
      analysisMode: 'date',
      selectedDateObj: dayjs().subtract(1, 'day').format('YYYY-MM-DD'),
      recentDays: 1,
      analysisLoading: false,
      analysisResult: null,
      activeTab: 'analysis',
      historyList: [],
      historyLoading: false,
      historySearch: '',
      statsLoading: false,
      statsSummary: null,
      statsTopYouzi: [],
      statsTopStocks: [],
      statsScoreboard: []
    }
  },
  computed: {
    quickCards() {
      const info = this.analysisResult?.data_info || {}
      return [
        { label: '龙虎榜记录', value: info.total_records || '--', desc: '当日上榜总数' },
        { label: '涉及股票', value: info.total_stocks || '--', desc: '出现的个股数量' },
        { label: '活跃游资', value: info.total_youzi || '--', desc: '统计的游资席位' },
        {
          label: '推荐股票',
          value: this.analysisResult?.recommended_stocks?.length || 0,
          desc: 'AI 甄选潜力标的'
        }
      ]
    },
    scoringTop10() {
      return (this.analysisResult?.scoring_ranking || []).slice(0, 10)
    },
    recommendedList() {
      return this.analysisResult?.recommended_stocks || []
    },
    agentList() {
      if (!this.analysisResult?.agents_analysis) return []
      return Object.values(this.analysisResult.agents_analysis)
    },
    topYouziList() {
      const source = this.analysisResult?.data_info?.summary?.top_youzi || {}
      return Object.entries(source).map(([name, netInflow], index) => ({
        rank: index + 1,
        name,
        netInflow
      }))
    },
    topStockList() {
      return this.analysisResult?.data_info?.summary?.top_stocks || []
    },
    hotConceptList() {
      const source = this.analysisResult?.data_info?.summary?.hot_concepts || {}
      return Object.entries(source).map(([name, count], index) => ({
        rank: index + 1,
        name,
        count
      }))
    },
    filteredHistory() {
      if (!this.historySearch) return this.historyList
      const keyword = this.historySearch.toLowerCase()
      return this.historyList.filter(
        item =>
          item.summary?.toLowerCase().includes(keyword) ||
          String(item.id).includes(keyword) ||
          item.data_date_range?.toLowerCase().includes(keyword)
      )
    },
    statsCards() {
      if (!this.statsSummary) return []
      return [
        { label: '累计记录', value: this.formatNumber(this.statsSummary.total_records), desc: 'longhubang_records' },
        { label: '覆盖股票', value: this.formatNumber(this.statsSummary.total_stocks), desc: 'distinct stock_code' },
        { label: '游资席位', value: this.formatNumber(this.statsSummary.total_youzi), desc: 'distinct youzi' },
        { label: '分析报告', value: this.formatNumber(this.statsSummary.total_reports), desc: 'longhubang_analysis' }
      ]
    }
  },
  created() {
    this.loadHistory()
    this.loadStats()
    // 检查是否有正在执行的任务
    this.checkPendingTask()
  },
  beforeDestroy() {
    // 组件销毁时不关闭 WebSocket，保持任务继续执行
    // 但要移除事件监听，避免内存泄漏
    if (this.websocket) {
      // 保存当前状态到 localStorage
      this.saveTaskState()
    }
  },
  methods: {
    disableFutureDate(date) {
      return date.getTime() > Date.now()
    },
    renderMarkdown(text) {
      if (!text) return ''
      try {
        return marked(text)
      } catch (e) {
        console.warn('Markdown 渲染失败:', e)
        return text
      }
    },
    formatCurrency(value) {
      const num = Number(value)
      if (Number.isNaN(num)) return '--'
      if (Math.abs(num) >= 1e8) {
        return `${(num / 1e8).toFixed(2)} 亿`
      }
      if (Math.abs(num) >= 1e6) {
        return `${(num / 1e6).toFixed(1)} 百万`
      }
      return `${num.toFixed(0)} 元`
    },
    formatNumber(value) {
      const num = Number(value)
      if (Number.isNaN(num)) return '--'
      return num.toLocaleString()
    },
    formatPercent(value) {
      if (value === null || value === undefined) return '--'
      return `${(Number(value) * 100).toFixed(1)}%`
    },
    formatScoreCell(row, column, value) {
      const num = Number(value)
      return Number.isNaN(num) ? '--' : `${num.toFixed(1)} 分`
    },
    formatCurrencyCell(row, column, value) {
      return this.formatCurrency(value)
    },
    normalizeScoring(list) {
      return list.map((item, index) => ({
        rank: Number(item.rank ?? item.排名 ?? index + 1),
        name: item.name || item.stock_name || item['股票名称'] || '--',
        code: item.code || item.stock_code || item['股票代码'] || '--',
        score: Number(item.score ?? item['综合评分'] ?? 0),
        eliteSeats: Number(item.eliteSeats ?? item['顶级游资'] ?? item.top_youzi ?? 0),
        buySeats: Number(item.buySeats ?? item['买方数'] ?? 0),
        orgInvolved: item.orgInvolved ?? item['机构参与'] ?? '否',
        netInflow: Number(item.netInflow ?? item['净流入'] ?? 0)
      }))
    },
    generateTaskId() {
      return 'lhb_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
    },
    // 任务状态持久化相关方法
    getTaskStorageKey() {
      return 'longhubang_pending_task'
    },
    saveTaskState() {
      if (!this.taskId || !this.analysisLoading) return
      const state = {
        taskId: this.taskId,
        progress: this.analysisProgress,
        message: this.analysisMessage,
        logs: this.analysisLogs.slice(-20), // 只保存最近20条日志
        startTime: Date.now(),
        params: {
          model: this.selectedModel,
          mode: this.analysisMode,
          date: this.selectedDateObj,
          days: this.recentDays
        }
      }
      localStorage.setItem(this.getTaskStorageKey(), JSON.stringify(state))
      console.log('[龙虎榜] 任务状态已保存:', state.taskId)
    },
    loadTaskState() {
      try {
        const stateStr = localStorage.getItem(this.getTaskStorageKey())
        if (!stateStr) return null
        const state = JSON.parse(stateStr)
        // 检查任务是否超时（超过30分钟认为已失效）
        if (Date.now() - state.startTime > 30 * 60 * 1000) {
          this.clearTaskState()
          return null
        }
        return state
      } catch (e) {
        console.warn('[龙虎榜] 加载任务状态失败:', e)
        return null
      }
    },
    clearTaskState() {
      localStorage.removeItem(this.getTaskStorageKey())
      console.log('[龙虎榜] 任务状态已清除')
    },
    async checkPendingTask() {
      const state = this.loadTaskState()
      if (!state) return

      console.log('[龙虎榜] 发现未完成的任务:', state.taskId)

      // 恢复任务状态
      this.taskId = state.taskId
      this.analysisProgress = state.progress
      this.analysisMessage = state.message || '正在恢复任务...'
      this.analysisLogs = state.logs || []
      this.analysisLoading = true

      // 恢复参数
      if (state.params) {
        this.selectedModel = state.params.model || this.selectedModel
        this.analysisMode = state.params.mode || this.analysisMode
        this.selectedDateObj = state.params.date || this.selectedDateObj
        this.recentDays = state.params.days || this.recentDays
      }

      this.addLog('info', '检测到未完成的分析任务，正在恢复...')

      // 尝试重新连接 WebSocket
      try {
        await this.connectWebSocket(this.taskId)
        this.addLog('info', '已重新连接到分析任务')
      } catch (error) {
        console.warn('[龙虎榜] 重新连接失败，任务可能已完成或失败:', error)
        this.addLog('warning', '无法重新连接，任务可能已完成')
        // 清除任务状态，允许开始新任务
        this.clearTaskState()
        this.analysisLoading = false
        this.taskId = null
        // 刷新历史记录，可能任务已完成
        this.loadHistory()
      }
    },
    cancelTask() {
      this.$confirm('确定要取消当前分析任务吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.closeWebSocket()
        this.clearTaskState()
        this.analysisLoading = false
        this.taskId = null
        this.analysisProgress = 0
        this.analysisMessage = ''
        this.analysisLogs = []
        this.$message.info('已取消分析任务')
      }).catch(() => {})
    },
    getWebSocketUrl(taskId) {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = window.location.host
      // 开发环境使用后端端口
      const wsHost = process.env.NODE_ENV === 'development' ? 'localhost:8000' : host
      return `${protocol}//${wsHost}/api/v1/longhubang/ws/${taskId}`
    },
    addLog(level, message) {
      const time = dayjs().format('HH:mm:ss')
      this.analysisLogs.push({ level, message, time })
      // 保持最多50条日志
      if (this.analysisLogs.length > 50) {
        this.analysisLogs.shift()
      }
      // 滚动到底部
      this.$nextTick(() => {
        const container = this.$refs.logsContainer
        if (container) {
          container.scrollTop = container.scrollHeight
        }
      })
    },
    connectWebSocket(taskId) {
      return new Promise((resolve, reject) => {
        const wsUrl = this.getWebSocketUrl(taskId)
        this.addLog('info', `正在连接 WebSocket: ${wsUrl}`)

        this.websocket = new WebSocket(wsUrl)

        this.websocket.onopen = () => {
          this.addLog('info', 'WebSocket 连接成功')
          resolve()
        }

        this.websocket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            this.handleWebSocketMessage(data)
          } catch (e) {
            console.warn('WebSocket 消息解析失败', e)
          }
        }

        this.websocket.onerror = (error) => {
          this.addLog('error', 'WebSocket 连接错误')
          console.error('WebSocket error:', error)
          reject(error)
        }

        this.websocket.onclose = () => {
          this.addLog('info', 'WebSocket 连接已关闭')
          this.websocket = null
        }

        // 5秒超时
        setTimeout(() => {
          if (this.websocket && this.websocket.readyState !== WebSocket.OPEN) {
            reject(new Error('WebSocket 连接超时'))
          }
        }, 5000)
      })
    },
    handleWebSocketMessage(data) {
      switch (data.type) {
        case 'progress':
          this.analysisProgress = data.progress || 0
          this.analysisMessage = data.message || ''
          if (data.stage) {
            this.addLog('info', `[${data.stage}] ${data.message}`)
          }
          // 定期保存任务状态
          this.saveTaskState()
          break
        case 'log':
          this.addLog(data.level || 'info', data.message || '')
          break
        case 'complete':
          // 任务完成，清除持久化状态
          this.clearTaskState()
          if (data.success && data.result) {
            this.analysisResult = this.decorateResult(data.result)
            this.$message.success('龙虎榜分析完成')
          } else {
            this.$message.error(data.error || '分析失败')
            this.addLog('error', data.error || '分析失败')
          }
          this.analysisLoading = false
          this.taskId = null
          this.closeWebSocket()
          // 刷新历史记录
          this.loadHistory()
          break
        case 'pong':
          // 心跳响应
          break
        default:
          console.log('未知消息类型:', data)
      }
    },
    closeWebSocket() {
      if (this.websocket) {
        this.websocket.close()
        this.websocket = null
      }
    },
    async handleAnalyze() {
      // 检查是否有正在执行的任务
      if (this.analysisLoading && this.taskId) {
        this.$message.warning('当前有分析任务正在执行，请等待完成或取消后再试')
        return
      }

      this.analysisLoading = true
      this.analysisProgress = 0
      this.analysisMessage = '准备开始分析...'
      this.analysisLogs = []

      // 生成任务ID
      this.taskId = this.generateTaskId()

      try {
        // 先尝试使用 WebSocket 异步分析
        await this.connectWebSocket(this.taskId)

        // 保存任务状态
        this.saveTaskState()

        // 构建请求参数
        const payload = {
          model: this.selectedModel,
          task_id: this.taskId
        }
        if (this.analysisMode === 'date') {
          payload.date = this.selectedDateObj || dayjs().subtract(1, 'day').format('YYYY-MM-DD')
        } else {
          payload.days = this.recentDays
        }

        // 调用异步分析接口
        const { analyzeAsyncLonghubang } = await import('@/api/longhubang')
        const res = await analyzeAsyncLonghubang(payload)
        const data = res?.data || res

        if (data?.status !== 'started') {
          throw new Error(data?.message || '启动分析失败')
        }

        this.addLog('info', '分析任务已启动，等待结果...')
        // 分析结果会通过 WebSocket 推送

      } catch (error) {
        console.warn('WebSocket 分析失败，回退到同步模式', error)
        this.closeWebSocket()
        this.addLog('warning', '回退到同步分析模式...')

        // 回退到同步分析
        try {
          const payload = { model: this.selectedModel }
          if (this.analysisMode === 'date') {
            payload.date = this.selectedDateObj || dayjs().subtract(1, 'day').format('YYYY-MM-DD')
          } else {
            payload.days = this.recentDays
          }
          const res = await analyzeLonghubang(payload)
          const data = res?.data || res?.result || res
          if (data?.success) {
            this.analysisResult = this.decorateResult(data)
            this.$message.success('龙虎榜分析完成')
          } else {
            throw new Error(data?.error || '分析失败')
          }
        } catch (syncError) {
          console.error('分析失败', syncError)
          this.$message.error(syncError.message || '分析请求失败，请检查后端服务')
        } finally {
          this.analysisLoading = false
        }
      }
    },
    decorateResult(result) {
      const normalized = { ...result }
      if (Array.isArray(normalized.scoring_ranking)) {
        normalized.scoring_ranking = this.normalizeScoring(normalized.scoring_ranking)
      }
      if (!normalized.recommended_stocks) {
        normalized.recommended_stocks = []
      }
      return normalized
    },
    clearResult() {
      this.analysisResult = null
      this.$message.success('已清除分析结果')
    },
    async loadHistory() {
      this.historyLoading = true
      try {
        const res = await getLonghubangHistory({ page: 1, page_size: 50 })
        // 后端返回格式: { code: 200, data: { items: [...], total: N } }
        const data = res?.data || res
        const list = Array.isArray(data?.items) ? data.items : Array.isArray(data) ? data : []
        this.historyList = list
      } catch (error) {
        console.error('获取历史报告失败', error)
        this.historyList = []
        this.$message.error('获取历史报告失败')
      } finally {
        this.historyLoading = false
      }
    },
    loadHistoryItem(item) {
      if (!item.analysis_content) {
        this.$message.error('该报告缺少分析内容')
        return
      }
    
      this.analysisResult = this.decorateResult(item.analysis_content)
      this.activeTab = 'analysis'
      this.$message.success(`已加载报告 #${item.id}`)
    },
    async loadStats() {
      this.statsLoading = true
      try {
        // 计算日期范围（近30天）
        const endDate = dayjs().format('YYYY-MM-DD')
        const startDate = dayjs().subtract(30, 'day').format('YYYY-MM-DD')

        console.log('[龙虎榜统计] 开始加载数据，日期范围:', startDate, '~', endDate)

        // 并行请求统计数据、评分排名、活跃游资、热门股票
        const [statsRes, scoringRes, youziRes, stocksRes] = await Promise.allSettled([
          getLonghubangStatistics(),
          getLonghubangScoring({ limit: 20 }),
          getTopYouzi({ start_date: startDate, end_date: endDate, limit: 20 }),
          getTopStocks({ start_date: startDate, end_date: endDate, limit: 20 })
        ])

        // 处理统计数据
        // 注意：request.js 拦截器已经返回 res.data，所以 value 直接就是数据
        if (statsRes.status === 'fulfilled') {
          const data = statsRes.value
          console.log('[龙虎榜统计] 统计数据:', data)
          this.statsSummary = data || null
        } else {
          console.warn('[龙虎榜统计] 获取统计数据失败:', statsRes.reason)
          this.statsSummary = null
        }

        // 处理评分排名
        if (scoringRes.status === 'fulfilled') {
          const data = scoringRes.value
          console.log('[龙虎榜统计] 评分数据:', data)
          const list = Array.isArray(data?.items) ? data.items : []
          this.statsScoreboard = this.normalizeScoring(list)
        } else {
          console.warn('[龙虎榜统计] 获取评分数据失败:', scoringRes.reason)
          this.statsScoreboard = []
        }

        // 处理活跃游资
        if (youziRes.status === 'fulfilled') {
          const data = youziRes.value
          console.log('[龙虎榜统计] 游资数据:', data)
          const items = Array.isArray(data?.items) ? data.items : []
          this.statsTopYouzi = items.map(item => {
            const netInflowValue = item.total_net_inflow ?? item.net_inflow ?? 0
            return {
              name: item.youzi_name || item.name || '--',
              trade_count: Number(item.trade_count) || 0,
              net_inflow: Number(netInflowValue) || 0
            }
          })
        } else {
          console.warn('[龙虎榜统计] 获取游资数据失败:', youziRes.reason)
          this.statsTopYouzi = []
        }

        // 处理热门股票
        if (stocksRes.status === 'fulfilled') {
          const data = stocksRes.value
          console.log('[龙虎榜统计] 股票数据:', data)
          const items = Array.isArray(data?.items) ? data.items : []
          this.statsTopStocks = items.map(item => {
            // 数据库返回字段是 total_net_inflow
            const netInflowValue = item.total_net_inflow ?? item.net_inflow ?? 0
            console.log('[龙虎榜统计] 股票净流入:', item.stock_name, netInflowValue, item)
            return {
              code: item.stock_code || item.code || '--',
              name: item.stock_name || item.name || '--',
              youzi_count: Number(item.youzi_count) || 0,
              net_inflow: Number(netInflowValue) || 0
            }
          })
        } else {
          console.warn('[龙虎榜统计] 获取股票数据失败:', stocksRes.reason)
          this.statsTopStocks = []
        }

        console.log('[龙虎榜统计] 数据加载完成')
      } catch (error) {
        console.error('[龙虎榜统计] 加载失败:', error)
        this.statsScoreboard = []
        this.statsSummary = null
        this.statsTopYouzi = []
        this.statsTopStocks = []
        this.$message.error('加载统计数据失败，请检查后端服务')
      } finally {
        this.statsLoading = false
      }
    },
    async handleExport(type) {
      if (type !== 'pdf') {
        this.$message.info('暂仅支持导出 PDF')
        return
      }
      // 兼容多种字段名: report_id, saved_report.id
      const reportId = this.analysisResult?.report_id || this.analysisResult?.saved_report?.id
      if (!reportId) {
        this.$message.warning('请先完成一次分析以生成报告')
        return
      }
      try {
        const blob = await generateLonghubangPDF({ report_id: reportId })
        if (blob) {
          const url = window.URL.createObjectURL(new Blob([blob]))
          const link = document.createElement('a')
          link.href = url
          link.setAttribute('download', `longhubang-report-${reportId}.pdf`)
          document.body.appendChild(link)
          link.click()
          link.remove()
        } else {
          throw new Error('empty file')
        }
      } catch (error) {
        console.warn('generateLonghubangPDF fallback', error)
        this.$message.info('PDF 生成功能暂未开放')
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.lhb-page {
  display: flex;
  flex-direction: column;
  gap: 16px;

  .hero-card {
    background: linear-gradient(135deg, #ff9a9e 0%, #fad0c4 100%);
    color: #fff;

    .hero-content {
      display: flex;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 24px;
    }

    .hero-eyebrow {
      letter-spacing: 1px;
      font-size: 12px;
      opacity: 0.9;
    }

    h2 {
      margin: 8px 0;
      font-size: 24px;
    }

    .hero-subtitle {
      max-width: 520px;
      line-height: 1.6;
      opacity: 0.95;
    }

    .hero-tags {
      margin-top: 12px;
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    .hero-actions {
      display: flex;
      gap: 16px;
      flex-wrap: wrap;
      min-width: 280px;

      .action-block {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 12px 16px;
        min-width: 220px;

        .label {
          font-size: 13px;
          opacity: 0.8;
          margin: 0;
        }

        .value {
          font-size: 18px;
          font-weight: 600;
          margin: 6px 0;
        }

        .desc {
          font-size: 12px;
          opacity: 0.8;
          margin: 0;
        }
      }
    }
  }

  .analysis-form {
    .form-actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
  }

  .module-card {
    .quick-stats {
      margin-bottom: 16px;
    }

    .stat-card {
      .label {
        color: #909399;
        margin-bottom: 4px;
      }

      .value {
        font-size: 20px;
        font-weight: 600;
        margin-bottom: 6px;
      }

      .desc {
        color: #909399;
        font-size: 12px;
      }
    }

    .analysis-content {
      display: flex;
      flex-direction: column;
      gap: 24px;
    }

    .inline-alert {
      margin-bottom: 12px;
    }

    .sub-section {
      background: #fafafa;
      border-radius: 8px;
      padding: 16px;

      h3 {
        margin: 0 0 16px;
      }
    }

    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;

      h3 {
        margin: 0;
      }
    }

    .recommend-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 16px;

      .recommend-card {
        .card-heading {
          display: flex;
          justify-content: space-between;
          gap: 12px;
          margin-bottom: 12px;
        }

        .tag-list {
          display: flex;
          gap: 6px;
          flex-wrap: wrap;
        }

        .score-block {
          text-align: right;

          .label {
            color: #909399;
            margin: 0;
          }

          .value {
            font-size: 18px;
            font-weight: 600;
            margin: 4px 0;
          }

          .desc {
            color: #909399;
            margin: 0;
          }
        }

        .reason,
        .risk {
          margin: 4px 0;
          color: #606266;
        }

        .meta-row {
          display: flex;
          justify-content: space-between;
          flex-wrap: wrap;
          font-size: 13px;
          color: #909399;
        }
      }
    }

    .data-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;

      h4 {
        margin-bottom: 12px;
      }
    }

    .focus,
    .timestamp {
      line-height: 1.7;
    }

    .analysis-content-md {
      line-height: 1.8;
      color: #303133;

      :deep(h1),
      :deep(h2),
      :deep(h3),
      :deep(h4) {
        margin: 16px 0 8px;
        font-weight: 600;
        color: #1f2937;
      }

      :deep(h1) { font-size: 1.5em; }
      :deep(h2) { font-size: 1.3em; }
      :deep(h3) { font-size: 1.15em; }
      :deep(h4) { font-size: 1em; }

      :deep(p) {
        margin: 8px 0;
      }

      :deep(ul),
      :deep(ol) {
        margin: 8px 0;
        padding-left: 24px;
      }

      :deep(li) {
        margin: 4px 0;
      }

      :deep(strong) {
        font-weight: 600;
        color: #1f2937;
      }

      :deep(em) {
        font-style: italic;
      }

      :deep(code) {
        background: #f3f4f6;
        padding: 2px 6px;
        border-radius: 4px;
        font-family: 'Monaco', 'Menlo', monospace;
        font-size: 0.9em;
      }

      :deep(blockquote) {
        margin: 12px 0;
        padding: 8px 16px;
        border-left: 4px solid #667eea;
        background: #f8f9fa;
        color: #606266;
      }

      :deep(table) {
        width: 100%;
        border-collapse: collapse;
        margin: 12px 0;

        th, td {
          border: 1px solid #e4e7ed;
          padding: 8px 12px;
          text-align: left;
        }

        th {
          background: #f5f7fa;
          font-weight: 600;
        }
      }

      :deep(hr) {
        border: none;
        border-top: 1px solid #e4e7ed;
        margin: 16px 0;
      }
    }
  }

  .history-header {
    display: flex;
    gap: 12px;
    align-items: center;
    margin-bottom: 16px;

    .history-search {
      flex: 1;
    }
  }

  .history-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 12px;
      margin-bottom: 12px;
    }

    .subtitle {
      color: #606266;
    }

    .tagline {
      color: #909399;
      font-size: 12px;
    }

    .history-actions {
      display: flex;
      justify-content: flex-end;
    }
  }

  // 进度显示样式
  .progress-section {
    margin-bottom: 20px;

    .progress-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: #fff;
      padding: 20px;

      .progress-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;

        .progress-title {
          font-size: 16px;
          font-weight: 600;
        }

        .progress-percent {
          font-size: 24px;
          font-weight: bold;
        }
      }

      .task-id {
        font-size: 11px;
        opacity: 0.7;
        margin: 4px 0 0;
        font-family: 'Monaco', 'Menlo', monospace;
      }

      .progress-message {
        margin: 12px 0 0;
        font-size: 14px;
        opacity: 0.95;
      }

      .progress-logs {
        margin-top: 16px;
        background: rgba(0, 0, 0, 0.2);
        border-radius: 8px;
        padding: 12px;

        .logs-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
          font-size: 13px;
          opacity: 0.9;
        }

        .logs-container {
          max-height: 200px;
          overflow-y: auto;
          font-family: 'Monaco', 'Menlo', monospace;
          font-size: 12px;

          &::-webkit-scrollbar {
            width: 6px;
          }

          &::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.3);
            border-radius: 3px;
          }

          .log-item {
            margin: 4px 0;
            padding: 2px 0;
            display: flex;
            gap: 8px;

            .log-time {
              opacity: 0.7;
              flex-shrink: 0;
            }

            .log-text {
              word-break: break-all;
            }

            &.log-info {
              color: #fff;
            }

            &.log-warning {
              color: #ffd93d;
            }

            &.log-error {
              color: #ff6b6b;
            }
          }
        }
      }
    }
  }
}
</style>
