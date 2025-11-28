<template>
  <div class="lhb-page app-container">
    <el-card shadow="hover" class="hero-card">
      <div class="hero-content">
        <div>
          <p class="hero-eyebrow">Multi-Agent Dragon Tiger</p>
          <h2>🐲 智瞰龙虎 · 游资多维洞察</h2>
          <p class="hero-subtitle">
            复刻 Streamlit 版本的智瞰龙虎：游资行为、个股潜力、题材风向与风控提示一应俱全，支持批量分析与历史报告回放。
          </p>
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
                    v-model="selectedDate"
                    type="date"
                    placeholder="选择日期"
                    format="YYYY-MM-DD"
                    value-format="YYYY-MM-DD"
                    :disabled-date="disableFutureDate"
                    class="full-width"
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
                    <el-button type="primary" :loading="analysisLoading" @click="handleAnalyze">
                      🚀 开始分析
                    </el-button>
                    <el-button :disabled="!analysisResult" @click="clearResult">清除结果</el-button>
                  </div>
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>

          <el-divider />

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
                  <p class="analysis-text">{{ agent.analysis }}</p>
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
                      prop="netInflow"
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
          <el-empty v-if="filteredHistory.length === 0" description="暂无历史记录" />
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
            <el-row :gutter="16" class="quick-stats">
              <el-col v-for="card in statsCards" :key="card.label" :xs="12" :sm="6">
                <el-card shadow="never" class="stat-card">
                  <p class="label">{{ card.label }}</p>
                  <p class="value">{{ card.value }}</p>
                  <p class="desc">{{ card.desc }}</p>
                </el-card>
              </el-col>
            </el-row>
            <el-alert
              v-if="statsSummary && statsSummary.date_range"
              :closable="false"
              type="info"
              class="inline-alert"
              :title="`数据范围：${statsSummary.date_range.start} ~ ${statsSummary.date_range.end}`"
            />
            <section class="sub-section">
              <h3>🏅 历史活跃游资</h3>
              <el-table :data="statsTopYouzi" border size="small">
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
              <h3>📈 历史热门股票</h3>
              <el-table :data="statsTopStocks" border size="small">
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
              <el-table :data="statsScoreboard" border stripe size="small">
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
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script>
import dayjs from 'dayjs'
import {
  analyzeLonghubang,
  getLonghubangHistory,
  getLonghubangScoring,
  generateLonghubangPDF
} from '@/api/longhubang'

const MODEL_OPTIONS = [
  { value: 'deepseek-chat', label: 'DeepSeek V3 Chat（默认）' },
  { value: 'deepseek-reasoner', label: 'DeepSeek-R1 Reasoner' },
  { value: 'openai-gpt4o', label: 'OpenAI GPT-4o' }
]

const createFallbackResult = () => {
  const timestamp = dayjs().subtract(1, 'day').format('YYYY-MM-DD HH:mm:ss')
  return {
    success: true,
    timestamp,
    data_info: {
      total_records: 128,
      total_stocks: 62,
      total_youzi: 31,
      data_range: dayjs().subtract(1, 'day').format('YYYY-MM-DD'),
      summary: {
        top_youzi: {
          章盟主: 360000000,
          赵老哥: 240000000,
          宁波桑田路: 180000000,
          玲珑羽: 150000000,
          作手新一: 138000000
        },
        top_stocks: [
          { code: '688041', name: '海光信息', netInflow: 142000000 },
          { code: '300124', name: '汇川技术', netInflow: 126000000 },
          { code: '600703', name: '三安光电', netInflow: 118000000 },
          { code: '603986', name: '兆易创新', netInflow: 96000000 },
          { code: '300327', name: '中颖电子', netInflow: 83000000 }
        ],
        hot_concepts: {
          东数西算: 9,
          AI服务器: 8,
          光模块: 7,
          特高压: 6,
          新能源车: 6,
          Chiplet: 5
        }
      }
    },
    scoring_ranking: [
      {
        rank: 1,
        name: '海光信息',
        code: '688041',
        score: 92.5,
        eliteSeats: 3,
        buySeats: 5,
        orgInvolved: '是',
        netInflow: 142000000
      },
      {
        rank: 2,
        name: '兆易创新',
        code: '603986',
        score: 90.1,
        eliteSeats: 2,
        buySeats: 5,
        orgInvolved: '否',
        netInflow: 118000000
      },
      {
        rank: 3,
        name: '中际旭创',
        code: '300308',
        score: 87.6,
        eliteSeats: 2,
        buySeats: 4,
        orgInvolved: '是',
        netInflow: 102000000
      },
      {
        rank: 4,
        name: '汇川技术',
        code: '300124',
        score: 85.8,
        eliteSeats: 1,
        buySeats: 4,
        orgInvolved: '否',
        netInflow: 96000000
      },
      {
        rank: 5,
        name: '三安光电',
        code: '600703',
        score: 84.2,
        eliteSeats: 1,
        buySeats: 3,
        orgInvolved: '是',
        netInflow: 92000000
      }
    ],
    recommended_stocks: [
      {
        rank: 1,
        code: '688041',
        name: '海光信息',
        netInflow: 142000000,
        youzi: '章盟主',
        youziStyle: '超强趋势打板',
        tags: ['算力', '东数西算'],
        confidence: '高',
        holdPeriod: 'T+3',
        reason: '连板+顶级游资二次加仓，北向资金同步吸筹，AI 服务器链条高景气。',
        risk: '需关注美股科技波动及情绪退潮风险。',
        targetPrice: '108 元',
        stopLoss: '88 元'
      },
      {
        rank: 2,
        code: '603986',
        name: '兆易创新',
        netInflow: 118000000,
        youzi: '赵老哥',
        youziStyle: '高低切换',
        tags: ['存储芯片', '国产替代'],
        confidence: '中高',
        holdPeriod: '5 个交易日',
        reason: 'HBM 产业链景气延续，游资与机构共振，量价齐升。',
        risk: '短线涨幅较大，谨防高位回撤。',
        targetPrice: '165 元',
        stopLoss: '142 元'
      },
      {
        rank: 3,
        code: '300327',
        name: '中颖电子',
        netInflow: 83000000,
        youzi: '宁波桑田路',
        youziStyle: '打板接力',
        tags: ['MCU', '汽车电子'],
        confidence: '中',
        holdPeriod: 'T+2',
        reason: '国产 MCU 催化不断，游资集中度高，换手健康。',
        risk: '基本面兑现节奏需跟踪订单数据。',
        targetPrice: '75 元',
        stopLoss: '62 元'
      }
    ],
    agents_analysis: {
      youzi: {
        agent_name: '🎯 游资行为分析师',
        agent_role: '识别活跃游资及其操作风格',
        focus_areas: ['顶级游资', '席位动向'],
        timestamp,
        analysis: '章盟主、赵老哥、宁波桑田路三大席位集中在算力与半导体方向，偏好高流动性标的，整体进攻欲望较强。'
      },
      stock: {
        agent_name: '📈 个股潜力分析师',
        agent_role: '挖掘潜力股与次日大概率上涨标的',
        focus_areas: ['净流入', '量价结构'],
        timestamp,
        analysis: '海光信息、兆易创新等龙头具备游资+机构共振，且量能持续放大，预期短线仍有冲高空间。'
      },
      theme: {
        agent_name: '🔥 题材追踪分析师',
        agent_role: '识别热点题材及持续性',
        focus_areas: ['算力', '东数西算', '新能源'],
        timestamp,
        analysis: '算力+AI 服务器为绝对主线，东数西算、特高压等题材提供支撑，短期尚未出现明确分歧。'
      },
      risk: {
        agent_name: '⚠️ 风险控制专家',
        agent_role: '识别风险事件与出货信号',
        focus_areas: ['游资出货', '高位筹码'],
        timestamp,
        analysis: '部分高位题材股存在游资轮动出货迹象，建议控制杠杆、分批止盈，谨防情绪高点回落。'
      },
      chief: {
        agent_name: '👔 首席策略师',
        agent_role: '综合所有分析师观点给出操作策略',
        focus_areas: ['仓位策略', '题材轮动'],
        timestamp,
        analysis: '维持进攻为主、滚动低吸策略，主线仍在算力+半导体，辅以新能源电力等防守组合。'
      }
    },
    saved_report: {
      id: 1001
    }
  }
}

const createFallbackHistory = () => {
  const baseResult = createFallbackResult()
  return [
    {
      id: 501,
      summary: '游资继续围绕 AI 算力主线轮动，章盟主与北向共振买入海光信息，建议保持进攻节奏。',
      data_date_range: '2024-11-24 ~ 2024-11-26',
      created_at: '2024-11-26 18:05',
      confidence_score: 0.82,
      market_outlook: '乐观',
      analysis_content: baseResult
    },
    {
      id: 498,
      summary: '新能源链条获北上资金加仓，特高压与汽车电子迎来二线补涨机会。',
      data_date_range: '2024-11-21 ~ 2024-11-23',
      created_at: '2024-11-23 18:02',
      confidence_score: 0.75,
      market_outlook: '中性偏多',
      analysis_content: {
        ...baseResult,
        timestamp: '2024-11-23 18:02'
      }
    }
  ]
}

const createFallbackStats = () => ({
  summary: {
    total_records: 3520,
    total_stocks: 910,
    total_youzi: 248,
    total_reports: 162,
    date_range: {
      start: '2024-01-02',
      end: dayjs().format('YYYY-MM-DD')
    }
  },
  top_youzi: [
    { name: '章盟主', trade_count: 42, net_inflow: 1240000000 },
    { name: '赵老哥', trade_count: 35, net_inflow: 980000000 },
    { name: '宁波桑田路', trade_count: 31, net_inflow: 860000000 },
    { name: '华泰江阴人民路', trade_count: 28, net_inflow: 720000000 }
  ],
  top_stocks: [
    { code: '688041', name: '海光信息', youzi_count: 15, net_inflow: 520000000 },
    { code: '300750', name: '宁德时代', youzi_count: 12, net_inflow: 460000000 },
    { code: '603986', name: '兆易创新', youzi_count: 11, net_inflow: 430000000 },
    { code: '601012', name: '隆基绿能', youzi_count: 9, net_inflow: 390000000 }
  ],
  scoreboard: createFallbackResult().scoring_ranking
})

export default {
  name: 'LonghubangIndex',
  data() {
    return {
      modelOptions: MODEL_OPTIONS,
      selectedModel: MODEL_OPTIONS[0].value,
      analysisMode: 'date',
      selectedDate: dayjs().subtract(1, 'day').format('YYYY-MM-DD'),
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
  },
  methods: {
    disableFutureDate(date) {
      return date.getTime() > Date.now()
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
    async handleAnalyze() {
      this.analysisLoading = true
      try {
        const payload = { model: this.selectedModel }
        if (this.analysisMode === 'date') {
          payload.date = this.selectedDate || dayjs().subtract(1, 'day').format('YYYY-MM-DD')
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
      } catch (error) {
        console.warn('analyzeLonghubang fallback', error)
        this.analysisResult = createFallbackResult()
        this.$message.info('接口暂未打通，展示示例分析结果')
      } finally {
        this.analysisLoading = false
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
        const res = await getLonghubangHistory()
        const list = Array.isArray(res?.items) ? res.items : Array.isArray(res) ? res : []
        this.historyList = list.length ? list : createFallbackHistory()
      } catch (error) {
        console.warn('getLonghubangHistory fallback', error)
        this.historyList = createFallbackHistory()
        this.$message.info('历史报告接口未连通，展示示例记录')
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
        const res = await getLonghubangScoring({ limit: 20 })
        const list = Array.isArray(res?.items) ? res.items : Array.isArray(res) ? res : []
        const normalized = list.length ? this.normalizeScoring(list) : null
        const fallback = createFallbackStats()
        this.statsScoreboard = normalized || fallback.scoreboard
        this.statsSummary = fallback.summary
        this.statsTopYouzi = fallback.top_youzi
        this.statsTopStocks = fallback.top_stocks
      } catch (error) {
        console.warn('getLonghubangScoring fallback', error)
        const fallback = createFallbackStats()
        this.statsScoreboard = fallback.scoreboard
        this.statsSummary = fallback.summary
        this.statsTopYouzi = fallback.top_youzi
        this.statsTopStocks = fallback.top_stocks
        this.$message.info('统计接口未准备好，展示示例数据')
      } finally {
        this.statsLoading = false
      }
    },
    async handleExport(type) {
      if (type !== 'pdf') {
        this.$message.info('暂仅支持导出 PDF')
        return
      }
      const reportId = this.analysisResult?.saved_report?.id
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
    .timestamp,
    .analysis-text {
      line-height: 1.7;
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
}
</style>
