<template>
  <div class="stock-page app-container">
    <el-card shadow="hover" class="hero-card">
      <div class="hero-content">
        <div>
          <p class="hero-eyebrow">Multi-Agent Stock Analysis</p>
          <h2>📈 股票分析 · 复合多智能体决策系统</h2>
          <p class="hero-subtitle">
            还原 Streamlit 主页体验：单股深度分析 + 批量模式 + 分析师团队协作，输出完整的行情、指标、报告与投资建议。
          </p>
          <div class="hero-tags">
            <el-tag effect="dark" type="success">技术面</el-tag>
            <el-tag effect="dark" type="warning">基本面</el-tag>
            <el-tag effect="dark" type="info">资金面</el-tag>
            <el-tag effect="dark" type="danger">风险控制</el-tag>
          </div>
        </div>
        <div class="hero-actions">
          <div class="action-block">
            <p class="label">最新分析</p>
            <p class="value">{{ (analysisResult && analysisResult.timestamp) || '尚未执行' }}</p>
            <p class="desc">选择模式输入股票代码即可开始</p>
          </div>
          <div class="action-block">
            <p class="label">AI 模型</p>
            <el-select v-model="selectedModel" placeholder="选择模型" size="large">
              <el-option
                v-for="item in modelOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </div>
        </div>
      </div>
    </el-card>

    <el-card shadow="hover" class="module-card">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="🔍 股票分析" name="analysis">
          <div class="mode-switch">
            <div class="mode-info">
              <p class="label">分析模式</p>
              <p class="desc">单股适用于深度报告，批量模式可快速筛选多只股票</p>
            </div>
            <el-radio-group v-model="analysisMode" size="medium">
              <el-radio-button label="single">单个分析</el-radio-button>
              <el-radio-button label="batch">批量分析</el-radio-button>
            </el-radio-group>
          </div>

          <el-form label-position="top" class="analysis-form">
            <template v-if="analysisMode === 'single'">
              <el-row :gutter="16">
                <el-col :xs="24" :md="12">
                  <el-form-item label="股票代码 / 名称">
                    <el-input
                      v-model="singleForm.symbol"
                      placeholder="如 AAPL、600519、00700"
                      clearable
                    />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="6">
                  <el-form-item label="数据周期">
                    <el-select v-model="singleForm.period" placeholder="选择周期">
                      <el-option label="1年" value="1y" />
                      <el-option label="6个月" value="6mo" />
                      <el-option label="3个月" value="3mo" />
                      <el-option label="1个月" value="1mo" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="6">
                  <el-form-item label="操作">
                    <div class="form-actions">
                      <el-button type="primary" :loading="analysisLoading" @click="handleAnalyze">
                        🚀 开始分析
                      </el-button>
                      <el-button :disabled="!analysisResult" @click="clearResult">清除结果</el-button>
                    </div>
                  </el-form-item>
                </el-col>
              </el-row>
            </template>

            <template v-else>
              <el-row :gutter="16">
                <el-col :xs="24" :md="14">
                  <el-form-item label="股票列表（每行一个或逗号分隔）">
                    <el-input
                      v-model="batchForm.symbols"
                      type="textarea"
                      :rows="4"
                      placeholder="000001\n600519\n00700\n或：AAPL, MSFT, NVDA"
                    />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="5">
                  <el-form-item label="批量周期">
                    <el-select v-model="batchForm.period" placeholder="选择周期">
                      <el-option label="1年" value="1y" />
                      <el-option label="6个月" value="6mo" />
                      <el-option label="3个月" value="3mo" />
                      <el-option label="1个月" value="1mo" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="批量模式">
                    <el-select v-model="batchForm.mode">
                      <el-option label="顺序分析（稳定）" value="sequential" />
                      <el-option label="并行分析（快速）" value="parallel" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="5">
                  <el-form-item label="操作">
                    <div class="form-actions vertical">
                      <el-button type="primary" :loading="analysisLoading" @click="handleAnalyze">
                        🚀 批量分析
                      </el-button>
                      <el-button @click="clearBatch">清除列表</el-button>
                    </div>
                  </el-form-item>
                </el-col>
              </el-row>
            </template>

            <div class="analyst-selector">
              <h4>👥 选择分析师团队</h4>
              <p class="desc">
                可按需开启 / 关闭分析维度，批量模式默认禁用情绪 & 新闻以提升速度。
              </p>
              <el-row :gutter="16">
                <el-col :xs="24" :md="8">
                  <el-checkbox v-model="analysts.technical">📊 技术分析师</el-checkbox>
                  <el-checkbox v-model="analysts.fundamental">💼 基本面分析师</el-checkbox>
                </el-col>
                <el-col :xs="24" :md="8">
                  <el-checkbox v-model="analysts.fund_flow">💰 资金面分析师</el-checkbox>
                  <el-checkbox v-model="analysts.risk">⚠️ 风险管理师</el-checkbox>
                </el-col>
                <el-col :xs="24" :md="8">
                  <el-checkbox v-model="analysts.sentiment">📈 情绪分析师（A股）</el-checkbox>
                  <el-checkbox v-model="analysts.news">📰 新闻分析师（A股）</el-checkbox>
                </el-col>
              </el-row>
              <el-alert
                type="info"
                :closable="false"
                class="inline-alert"
                title="至少选择一位分析师参与分析。批量模式默认沿用当前配置。"
              />
            </div>

            <el-card v-if="analysisMode === 'single'" shadow="never" class="cache-card">
              <div class="cache-info">
                <h4>🔄 缓存管理</h4>
                <p class="desc">Streamlit 版本支持清除缓存，这里可手动刷新分析结果以获取最新行情。</p>
              </div>
              <el-button icon="el-icon-refresh" size="mini" @click="refreshAnalysis">刷新数据</el-button>
            </el-card>
          </el-form>

          <el-divider />

          <template v-if="analysisMode === 'single'">
            <el-empty
              v-if="!analysisResult"
              description="输入股票代码并点击“开始分析”即可生成行情、指标、AI 报告与最终决策。"
            />

            <div v-else class="analysis-content">
              <el-row :gutter="16" class="quick-stats">
                <el-col v-for="card in quickCards" :key="card.label" :xs="12" :sm="6">
                  <el-card shadow="never" class="stat-card">
                    <p class="label">{{ card.label }}</p>
                    <p class="value">{{ card.value }}</p>
                    <p class="desc">{{ card.desc }}</p>
                  </el-card>
                </el-col>
              </el-row>

              <section class="sub-section">
                <div class="section-header">
                  <h3>📊 股票关键指标</h3>
                  <el-tag type="info">周期：{{ singleForm.period }}</el-tag>
                </div>
                <el-row :gutter="16">
                  <el-col :xs="24" :md="12">
                    <el-card shadow="never" class="info-card">
                      <h4>{{ stockInfo.name }} ({{ stockInfo.symbol }})</h4>
                      <p class="price">
                        {{ formatCurrency(stockInfo.current_price) }}
                        <span :class="stockInfo.change_percent >= 0 ? 'up' : 'down'">
                          {{ formatPercent(stockInfo.change_percent) }}
                        </span>
                      </p>
                      <div class="info-grid">
                        <div>
                          <p class="label">市盈率</p>
                          <p class="value">{{ stockInfo.pe_ratio }}</p>
                        </div>
                        <div>
                          <p class="label">市净率</p>
                          <p class="value">{{ stockInfo.pb_ratio }}</p>
                        </div>
                        <div>
                          <p class="label">市值</p>
                          <p class="value">{{ formatMarketCap(stockInfo.market_cap) }}</p>
                        </div>
                      </div>
                    </el-card>
                  </el-col>
                  <el-col :xs="24" :md="12">
                    <el-card shadow="never" class="info-card">
                      <h4>技术指标</h4>
                      <div class="indicator-grid">
                        <div>
                          <p class="label">RSI</p>
                          <p class="value">{{ indicators.rsi }}</p>
                        </div>
                        <div>
                          <p class="label">MA20</p>
                          <p class="value">{{ indicators.ma20 }}</p>
                        </div>
                        <div>
                          <p class="label">量比</p>
                          <p class="value">{{ indicators.volume_ratio }}</p>
                        </div>
                        <div>
                          <p class="label">MACD</p>
                          <p class="value">{{ indicators.macd }}</p>
                        </div>
                      </div>
                    </el-card>
                  </el-col>
                </el-row>
              </section>

              <section class="sub-section">
                <div class="section-header">
                  <h3>📈 股价走势图</h3>
                  <el-tag type="warning">示意图</el-tag>
                </div>
                <div class="chart-placeholder">
                  <p>图表展示区域（前端示例，真实场景可接入 ECharts / Plotly）</p>
                </div>
              </section>

              <section class="sub-section">
                <div class="section-header">
                  <h3>🤖 AI 分析师团队报告</h3>
                  <div>
                    <el-button size="mini" icon="el-icon-document" @click="exportReport('markdown')">
                      导出 Markdown
                    </el-button>
                    <el-button size="mini" type="primary" icon="el-icon-printer" @click="exportReport('pdf')">
                      导出 PDF
                    </el-button>
                  </div>
                </div>
                <el-tabs class="agent-tabs">
                  <el-tab-pane
                    v-for="agent in agentList"
                    :key="agent.agent_name"
                    :label="agent.agent_name"
                  >
                    <div class="agent-card">
                      <p class="role">{{ agent.agent_role }}</p>
                      <p class="focus">关注领域：{{ agent.focus_areas.join('、') }}</p>
                      <p class="timestamp">分析时间：{{ agent.timestamp }}</p>
                      <p class="analysis-text">{{ agent.analysis }}</p>
                    </div>
                  </el-tab-pane>
                </el-tabs>
              </section>

              <section class="sub-section">
                <h3>🤝 团队讨论</h3>
                <el-card shadow="never" class="discussion-card">
                  <p>{{ analysisResult.discussion_result }}</p>
                </el-card>
              </section>

              <section class="sub-section">
                <h3>📋 最终投资决策</h3>
                <el-row :gutter="16">
                  <el-col :xs="24" :md="8">
                    <el-card shadow="hover" class="decision-card">
                      <p class="rating">{{ finalDecision.rating }}</p>
                      <p class="label">投资评级</p>
                      <p class="metric">信心度：{{ finalDecision.confidence_level }}/10</p>
                      <p class="metric">建议仓位：{{ finalDecision.position_size }}</p>
                    </el-card>
                  </el-col>
                  <el-col :xs="24" :md="16">
                    <el-card shadow="hover" class="decision-card detail">
                      <div class="grid">
                        <div>
                          <p class="label">目标价</p>
                          <p class="value">{{ finalDecision.target_price }}</p>
                        </div>
                        <div>
                          <p class="label">进场区间</p>
                          <p class="value">{{ finalDecision.entry_range }}</p>
                        </div>
                        <div>
                          <p class="label">止盈位</p>
                          <p class="value">{{ finalDecision.take_profit }}</p>
                        </div>
                        <div>
                          <p class="label">止损位</p>
                          <p class="value">{{ finalDecision.stop_loss }}</p>
                        </div>
                        <div>
                          <p class="label">持有周期</p>
                          <p class="value">{{ finalDecision.holding_period }}</p>
                        </div>
                      </div>
                      <p class="label">操作建议</p>
                      <p>{{ finalDecision.operation_advice }}</p>
                      <el-alert
                        type="warning"
                        :closable="false"
                        class="inline-alert"
                        :title="finalDecision.risk_warning"
                      />
                    </el-card>
                  </el-col>
                </el-row>
              </section>
            </div>
          </template>

          <template v-else>
            <el-empty
              v-if="!batchResults.length"
              description="输入多只股票后点击“批量分析”，AI 将依次输出评级与关键价位。"
            />

            <div v-else class="batch-content">
              <el-alert
                type="success"
                :closable="false"
                class="inline-alert"
                :title="`批量分析完成：成功 ${batchSuccess} 只 / 共 ${batchResults.length} 只`"
              />
              <el-table :data="batchResults" border stripe>
                <el-table-column prop="symbol" label="代码" width="110" />
                <el-table-column prop="name" label="股票名称" />
                <el-table-column prop="rating" label="评级" width="110" />
                <el-table-column prop="confidence_level" label="信心度" width="100" />
                <el-table-column prop="target_price" label="目标价" width="120" />
                <el-table-column prop="entry_range" label="进场区间" width="140" />
                <el-table-column label="操作建议">
                  <template #default="{ row }">
                    <span>{{ row.operation_advice }}</span>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </template>
        </el-tab-pane>

        <el-tab-pane label="📚 历史记录" name="history">
          <div class="history-header">
            <el-input
              v-model="historySearch"
              placeholder="搜索股票代码 / 名称"
              prefix-icon="el-icon-search"
              clearable
              class="history-search"
            />
            <el-button icon="el-icon-refresh" :loading="historyLoading" @click="loadHistory">刷新</el-button>
          </div>
          <el-empty v-if="filteredHistory.length === 0" description="暂无历史记录" />
          <el-timeline v-else>
            <el-timeline-item
              v-for="record in filteredHistory"
              :key="record.id"
              :timestamp="record.analysis_date"
              placement="top"
            >
              <el-card shadow="never" class="history-card">
                <div class="card-header">
                  <div>
                    <h4>{{ record.stock_name }} ({{ record.symbol }})</h4>
                    <p class="subtitle">评级：{{ record.rating }}</p>
                    <p class="tagline">周期：{{ record.period }}</p>
                  </div>
                  <el-tag type="success">信心 {{ record.confidence || 'N/A' }}</el-tag>
                </div>
                <p class="summary">{{ record.summary || 'AI 分析记录' }}</p>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </el-tab-pane>

        <el-tab-pane label="💡 使用指南" name="guide">
          <el-row :gutter="16">
            <el-col :xs="24" :md="12">
              <el-card shadow="never" class="guide-card">
                <h3>流程说明</h3>
                <ol>
                  <li>输入股票代码，选择周期与分析师团队</li>
                  <li>系统获取行情、财务、资金流、情绪与新闻数据</li>
                  <li>六位 AI 分析师输出独立报告，团队讨论后形成结论</li>
                  <li>最终给出评级、信心度、目标价、进场 / 止盈 / 止损等建议</li>
                </ol>
              </el-card>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-card shadow="never" class="guide-card">
                <h3>支持市场</h3>
                <ul>
                  <li>A股：支持技术 / 基本面 / 资金 / 情绪 / 新闻等全量数据</li>
                  <li>港美股：支持行情、技术、财务指标（部分数据自动降级）</li>
                  <li>批量模式建议不超过 20 只股票，以免耗时过长</li>
                </ul>
                <el-alert
                  type="warning"
                  :closable="false"
                  class="inline-alert"
                  title="首次运行需确保后端已配置 DeepSeek API Key。"
                />
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script>
import dayjs from 'dayjs'
import {
  analyzeStock,
  batchAnalyzeStock,
  getStockHistory,
  generateStockPDF
} from '@/api/stock'

const MODEL_OPTIONS = [
  { value: 'deepseek-chat', label: 'DeepSeek V3 Chat（默认）' },
  { value: 'deepseek-reasoner', label: 'DeepSeek-R1 Reasoner' },
  { value: 'openai-gpt4o', label: 'OpenAI GPT-4o' }
]

const createFallbackAnalysis = () => {
  const timestamp = dayjs().format('YYYY-MM-DD HH:mm:ss')
  return {
    success: true,
    timestamp,
    stock_info: {
      symbol: '600519',
      name: '贵州茅台',
      current_price: 1688.23,
      change_percent: 1.25,
      pe_ratio: 27.8,
      pb_ratio: 7.6,
      market_cap: 2120000000000
    },
    indicators: {
      rsi: 56.3,
      ma20: 1668.5,
      volume_ratio: 1.12,
      macd: 2.86
    },
    agents_results: {
      technical: {
        agent_name: '📊 技术分析师',
        agent_role: '趋势与结构研判',
        focus_areas: ['均线', '成交量', '形态'],
        timestamp,
        analysis:
          '股价站稳 MA20 上方，量能温和放大，短线有望延续震荡上行。若回踩 1650-1660 区域仍可关注。'
      },
      fundamental: {
        agent_name: '💼 基本面分析师',
        agent_role: '财务与估值分析',
        focus_areas: ['营收利润', '估值水平'],
        timestamp,
        analysis:
          '高端白酒需求稳健，Q3 毛利率 91%，ROE 33%，当前估值位于近三年 45% 分位，具备中长期配置价值。'
      },
      fund_flow: {
        agent_name: '💰 资金面分析师',
        agent_role: '主力资金跟踪',
        focus_areas: ['北向资金', '主力净流入'],
        timestamp,
        analysis:
          '北向资金近三日净买入 8.4 亿，机构席位呈现低位增持，短线资金偏向高确定性标的。'
      },
      risk: {
        agent_name: '⚠️ 风险管理师',
        agent_role: '风险识别',
        focus_areas: ['政策', '波动率'],
        timestamp,
        analysis:
          '白酒板块受消费预期影响较大，需关注宏观数据与渠道库存。若跌破 1600 将破坏中期结构。'
      }
    },
    discussion_result:
      '团队一致认为贵州茅台基本面坚实，当前处于震荡抬升阶段。建议保持中等仓位，以 1650 为回撤跟踪点。',
    final_decision: {
      rating: '买入',
      confidence_level: 8,
      target_price: '1850 元',
      position_size: '30%-40%',
      operation_advice: '震荡市中建议分批建仓，保持耐心等待估值回归；若出现放量突破可适度加仓。',
      entry_range: '1650-1680 元',
      take_profit: '1850 元',
      stop_loss: '1580 元',
      holding_period: '1-3 个月',
      risk_warning: '关注消费需求波动及政策对高端白酒的潜在影响。'
    }
  }
}

const createFallbackBatch = () => [
  {
    symbol: '600519',
    name: '贵州茅台',
    rating: '买入',
    confidence_level: 8,
    target_price: '1850',
    entry_range: '1650-1680',
    operation_advice: '高确定性标的，震荡偏多。'
  },
  {
    symbol: '300750',
    name: '宁德时代',
    rating: '持有',
    confidence_level: 6,
    target_price: '240',
    entry_range: '205-215',
    operation_advice: '关注储能业务放量，等待放量突破再行加仓。'
  }
]

const createFallbackHistory = () => [
  {
    id: 401,
    symbol: '600036',
    stock_name: '招商银行',
    rating: '持有',
    analysis_date: '2024-11-26 18:10',
    period: '6mo',
    confidence: 6.5,
    summary: '息差企稳迹象出现，建议持有等待估值修复。'
  },
  {
    id: 398,
    symbol: 'AAPL',
    stock_name: 'Apple Inc.',
    rating: '买入',
    analysis_date: '2024-11-24 10:30',
    period: '1y',
    confidence: 8.2,
    summary: '服务与可穿戴驱动营收创新高，继续维持买入评级。'
  }
]

export default {
  name: 'StockIndex',
  data() {
    return {
      modelOptions: MODEL_OPTIONS,
      selectedModel: MODEL_OPTIONS[0].value,
      analysisMode: 'single',
      singleForm: {
        symbol: '',
        period: '1y'
      },
      batchForm: {
        symbols: '',
        period: '3mo',
        mode: 'sequential'
      },
      analysts: {
        technical: true,
        fundamental: true,
        fund_flow: true,
        risk: true,
        sentiment: false,
        news: false
      },
      activeTab: 'analysis',
      analysisLoading: false,
      analysisResult: null,
      batchResults: [],
      historyList: [],
      historyLoading: false,
      historySearch: ''
    }
  },
  computed: {
    stockInfo() {
      return (this.analysisResult && this.analysisResult.stock_info) || {}
    },
    indicators() {
      return (this.analysisResult && this.analysisResult.indicators) || {}
    },
    agentList() {
      if (!this.analysisResult || !this.analysisResult.agents_results) return []
      return Object.values(this.analysisResult.agents_results)
    },
    finalDecision() {
      return (this.analysisResult && this.analysisResult.final_decision) || {}
    },
    quickCards() {
      const info = this.stockInfo
      return [
        { label: '现价', value: this.formatCurrency(info.current_price), desc: '最新收盘价' },
        { label: '涨跌幅', value: this.formatPercent(info.change_percent), desc: '相较上一交易日' },
        { label: '市盈率', value: info.pe_ratio || '--', desc: 'PE(TTM)' },
        { label: '市值', value: this.formatMarketCap(info.market_cap), desc: '按人民币计价' }
      ]
    },
    batchSuccess() {
      return this.batchResults.filter(item => item.rating && item.rating !== '失败').length
    },
    filteredHistory() {
      if (!this.historySearch) return this.historyList
      const keyword = this.historySearch.toLowerCase()
      return this.historyList.filter(record => {
        return (
          (record.symbol && record.symbol.toLowerCase().includes(keyword)) ||
          (record.stock_name && record.stock_name.toLowerCase().includes(keyword))
        )
      })
    }
  },
  created() {
    this.loadHistory()
  },
  methods: {
    refreshAnalysis() {
      this.analysisResult = null
      this.$message.success('缓存已清除，请重新发起分析')
    },
    clearResult() {
      this.analysisResult = null
    },
    clearBatch() {
      this.batchForm.symbols = ''
      this.batchResults = []
    },
    formatCurrency(value) {
      const num = Number(value)
      if (Number.isNaN(num)) return '--'
      return num >= 1000 ? `${num.toFixed(2)} 元` : num.toFixed(2)
    },
    formatMarketCap(value) {
      const num = Number(value)
      if (Number.isNaN(num)) return '--'
      return num > 1e12 ? `${(num / 1e12).toFixed(2)} 万亿` : `${(num / 1e8).toFixed(2)} 亿`
    },
    formatPercent(value) {
      const num = Number(value)
      if (Number.isNaN(num)) return '--'
      return `${num.toFixed(2)}%`
    },
    ensureAnalystsValid() {
      const enabled = Object.values(this.analysts).some(Boolean)
      if (!enabled) {
        this.$message.error('请至少选择一位分析师')
      }
      return enabled
    },
    parseBatchSymbols() {
      if (!this.batchForm.symbols) return []
      const lines = this.batchForm.symbols.split(/\n|,/)
      const codes = lines
        .map(item => item.trim())
        .filter(Boolean)
        .filter((code, idx, arr) => arr.indexOf(code) === idx)
      return codes
    },
    async handleAnalyze() {
      if (!this.ensureAnalystsValid()) return
      if (this.analysisMode === 'single') {
        if (!this.singleForm.symbol) {
          this.$message.warning('请输入股票代码')
          return
        }
        await this.runSingleAnalysis()
      } else {
        const codes = this.parseBatchSymbols()
        if (!codes.length) {
          this.$message.warning('请输入至少一只股票')
          return
        }
        if (codes.length > 20) {
          this.$message.warning('建议一次批量分析不超过 20 只股票')
        }
        await this.runBatchAnalysis(codes)
      }
    },
    async runSingleAnalysis() {
      this.analysisLoading = true
      try {
        const payload = {
          symbol: this.singleForm.symbol,
          period: this.singleForm.period,
          model: this.selectedModel,
          analysts: this.analysts
        }
        const res = await analyzeStock(payload)
        const data = (res && (res.data || res.result || res)) || {}
        if (data.success) {
          this.analysisResult = data
          this.analysisMode = 'single'
          this.$message.success('单股分析完成')
        } else {
          throw new Error(data.error || '分析失败')
        }
      } catch (error) {
        console.warn('analyzeStock fallback', error)
        this.analysisResult = createFallbackAnalysis()
        this.$message.info('接口未连通，展示示例分析结果')
      } finally {
        this.analysisLoading = false
      }
    },
    async runBatchAnalysis(codes) {
      this.analysisLoading = true
      try {
        const payload = {
          symbols: codes,
          period: this.batchForm.period,
          mode: this.batchForm.mode,
          model: this.selectedModel,
          analysts: this.analysts
        }
        const res = await batchAnalyzeStock(payload)
        const data = (res && (res.data || res.result || res)) || {}
        if (data.success && Array.isArray(data.results)) {
          this.batchResults = data.results
          this.$message.success(`批量分析完成，成功 ${this.batchSuccess} 只`)
        } else {
          throw new Error(data.error || '批量分析失败')
        }
      } catch (error) {
        console.warn('batchAnalyzeStock fallback', error)
        this.batchResults = createFallbackBatch()
        this.$message.info('批量接口未打通，展示示例结果')
      } finally {
        this.analysisLoading = false
      }
    },
    async loadHistory() {
      this.historyLoading = true
      try {
        const res = await getStockHistory()
        const list = Array.isArray(res && (res.items || res)) ? (res.items || res) : []
        this.historyList = list.length ? list : createFallbackHistory()
      } catch (error) {
        console.warn('getStockHistory fallback', error)
        this.historyList = createFallbackHistory()
        this.$message.info('历史记录接口未打通，展示示例')
      } finally {
        this.historyLoading = false
      }
    },
    async exportReport(type) {
      if (!this.analysisResult || !this.analysisResult.final_decision) {
        this.$message.warning('请先完成一次分析')
        return
      }
      if (type === 'pdf') {
        try {
          const blob = await generateStockPDF({ symbol: this.stockInfo.symbol })
          if (!blob) throw new Error('empty')
          const url = window.URL.createObjectURL(new Blob([blob]))
          const link = document.createElement('a')
          link.href = url
          link.setAttribute('download', `stock-report-${this.stockInfo.symbol}.pdf`)
          document.body.appendChild(link)
          link.click()
          link.remove()
        } catch (error) {
          console.warn('generateStockPDF fallback', error)
          this.$message.info('PDF 生成功能暂未开放')
        }
      } else {
        this.$message.info('Markdown 导出将在后续版本开放')
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.stock-page {
  display: flex;
  flex-direction: column;
  gap: 16px;

  .hero-card {
    background: linear-gradient(135deg, #1f8ef1 0%, #5f27cd 100%);
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
      max-width: 540px;
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
        background: rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        padding: 12px 16px;
        min-width: 220px;

        .label {
          font-size: 13px;
          opacity: 0.85;
          margin: 0;
        }

        .value {
          font-size: 18px;
          font-weight: 600;
          margin: 6px 0;
        }

        .desc {
          font-size: 12px;
          opacity: 0.85;
          margin: 0;
        }
      }
    }
  }

  .mode-switch {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: #f5f7fa;
    border-radius: 10px;
    margin-bottom: 16px;

    .mode-info {
      .label {
        font-weight: 600;
        margin: 0;
      }

      .desc {
        margin: 4px 0 0;
        color: #909399;
        font-size: 13px;
      }
    }
  }

  .analysis-form {
    .form-actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;

      &.vertical {
        flex-direction: column;
      }
    }
  }

  .analyst-selector {
    background: #fafafa;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;

    h4 {
      margin: 0;
    }

    .desc {
      color: #909399;
      margin: 4px 0 12px;
    }
  }

  .cache-card {
    margin-top: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;

    .cache-info {
      .desc {
        color: #909399;
        margin: 4px 0 0;
      }
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

    .sub-section {
      background: #fafafa;
      border-radius: 10px;
      padding: 16px;
      margin-bottom: 16px;

      h3 {
        margin: 0 0 12px;
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

    .info-card {
      height: 100%;

      .price {
        font-size: 24px;
        font-weight: 600;

        .up {
          color: #67c23a;
          margin-left: 12px;
        }

        .down {
          color: #f56c6c;
          margin-left: 12px;
        }
      }
    }

    .info-grid,
    .indicator-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
      gap: 12px;

      .label {
        color: #909399;
        margin: 0;
      }

      .value {
        font-size: 16px;
        font-weight: 600;
      }
    }

    .chart-placeholder {
      height: 220px;
      background: repeating-linear-gradient(
        45deg,
        rgba(255, 255, 255, 0.3),
        rgba(255, 255, 255, 0.3) 10px,
        rgba(0, 0, 0, 0.03) 10px,
        rgba(0, 0, 0, 0.03) 20px
      );
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #606266;
    }

    .agent-card {
      background: #fff;
      border-radius: 10px;
      padding: 16px;
      line-height: 1.7;
    }

    .discussion-card {
      line-height: 1.7;
    }

    .decision-card {
      text-align: center;
      .rating {
        font-size: 24px;
        font-weight: 700;
      }
    }

    .decision-card.detail {
      text-align: left;

      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 12px;
      }

      .label {
        color: #909399;
        margin-bottom: 4px;
      }
    }

    .batch-content {
      .inline-alert {
        margin-bottom: 12px;
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
  }

  .guide-card {
    height: 100%;
    line-height: 1.8;
  }

  .inline-alert {
    margin-top: 12px;
  }
}
</style>
