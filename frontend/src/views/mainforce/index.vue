<template>
  <div class="mainforce-page app-container">
    <el-card shadow="hover" class="hero-card">
      <div class="hero-content">
        <div>
          <p class="hero-eyebrow">Smart Money Selection</p>
          <h2>🎯 主力选股 · 多维主力净流入筛选</h2>
          <p class="hero-subtitle">
            对齐 Streamlit 主力选股面板：问财数据 + 资金流向 + 行业基本面 + AI 研究员综合评分，精选 3-5 只优质标的。
          </p>
          <div class="hero-tags">
            <el-tag effect="dark" type="success">主力净流入</el-tag>
            <el-tag effect="dark" type="warning">涨跌幅过滤</el-tag>
            <el-tag effect="dark" type="info">AI 分析师报告</el-tag>
          </div>
        </div>
        <div class="hero-actions">
          <div class="action-block">
            <p class="label">最近一次分析</p>
            <p class="value">{{ (analysisResult && analysisResult.timestamp) || '尚未执行' }}</p>
            <p class="desc">数据源：问财 TOP100 主力净流入</p>
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
        <el-tab-pane label="🚀 智能主力筛选" name="analysis">
          <el-form label-position="top" class="analysis-form">
            <div class="time-range-block">
              <div class="time-header">
                <div>
                  <p class="label">时间区间</p>
                  <p class="desc">快速切换常用窗口，或选择自定义日期</p>
                </div>
                <el-radio-group v-model="rangeOption" size="medium" class="time-radios">
                  <el-radio-button label="3m">近3个月</el-radio-button>
                  <el-radio-button label="6m">近6个月</el-radio-button>
                  <el-radio-button label="1y">近1年</el-radio-button>
                  <el-radio-button label="custom">自定义</el-radio-button>
                </el-radio-group>
              </div>
              <div v-if="rangeOption === 'custom'" class="custom-date-row">
                <el-date-picker
                  v-model="customDate"
                  type="date"
                  placeholder="选择日期"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  :disabled-date="disableFutureDate"
                />
                <span class="tip">* 以该日期为起点计算问财区间</span>
              </div>
              <div class="mode-tips">
                <el-tag size="small" type="info">问财 TOP100</el-tag>
                <span>系统会自动抓取对应时间段的主力净流入榜单</span>
              </div>
            </div>

            <el-row :gutter="16">
              <el-col :xs="24" :md="8">
                <el-form-item label="最终精选数量">
                  <el-slider
                    v-model="finalCount"
                    :min="3"
                    :max="10"
                    :step="1"
                    show-input
                    input-size="small"
                  />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :md="8">
                <el-form-item label="执行操作">
                  <div class="form-actions">
                    <el-button type="primary" :loading="analysisLoading" @click="handleAnalyze">
                      🚀 开始主力选股
                    </el-button>
                    <el-button :disabled="!analysisResult" @click="clearResult">清除结果</el-button>
                  </div>
                </el-form-item>
              </el-col>
            </el-row>

            <el-card shadow="never" class="advanced-card">
              <div class="advanced-header" @click="toggleAdvanced">
                <div>
                  <h4>⚙️ 高级筛选参数</h4>
                  <p class="subtitle">参照 Streamlit 版，可设定涨跌幅与市值区间，提升安全边际</p>
                </div>
                <div class="advanced-toggle">
                  <span>{{ showAdvanced ? '收起参数' : '展开设置' }}</span>
                  <i :class="['el-icon-arrow-down', { open: showAdvanced }]" />
                </div>
              </div>
              <transition name="el-fade-in-linear">
                <div v-show="showAdvanced">
                  <el-row :gutter="16">
                    <el-col :xs="24" :md="8">
                      <el-form-item label="最大涨跌幅 (%)">
                        <el-input-number
                          v-model="maxChange"
                          :min="5"
                          :max="200"
                          :step="5"
                          controls-position="right"
                          class="full-width"
                        />
                      </el-form-item>
                    </el-col>
                    <el-col :xs="24" :md="8">
                      <el-form-item label="最小市值 (亿)">
                        <el-input-number
                          v-model="minCap"
                          :min="10"
                          :max="500"
                          :step="10"
                          controls-position="right"
                          class="full-width"
                        />
                      </el-form-item>
                    </el-col>
                    <el-col :xs="24" :md="8">
                      <el-form-item label="最大市值 (亿)">
                        <el-input-number
                          v-model="maxCap"
                          :min="50"
                          :max="50000"
                          :step="100"
                          controls-position="right"
                          class="full-width"
                        />
                      </el-form-item>
                    </el-col>
                  </el-row>
                </div>
              </transition>
            </el-card>
          </el-form>

          <el-divider />

          <el-empty
            v-if="!analysisResult"
            description="点击“开始主力选股”即可根据主力净流入与AI分析师报告生成候选与推荐列表。"
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
                <h3>⭐ 精选标的</h3>
                <el-tag type="info">AI 综合 3+ 分析师评估</el-tag>
              </div>
              <div class="recommend-grid">
                <el-card
                  v-for="stock in recommendedList"
                  :key="stock.symbol"
                  shadow="hover"
                  class="recommend-card"
                >
                  <div class="card-heading">
                    <div>
                      <h4>{{ stock.rank }}. {{ stock.symbol }} · {{ stock.name }}</h4>
                      <div class="tag-list">
                        <el-tag v-for="tag in stock.tags" :key="tag" size="mini" type="success">
                          {{ tag }}
                        </el-tag>
                      </div>
                    </div>
                    <div class="score-block">
                      <p class="label">主力净流入</p>
                      <p class="value">{{ formatCurrency(stock.netInflow) }}</p>
                      <p class="desc">涨跌幅 {{ formatPercent(stock.changePct) }}</p>
                    </div>
                  </div>
                  <div class="recommend-body">
                    <div>
                      <p class="title">推荐理由</p>
                      <ul>
                        <li v-for="reason in stock.reasons" :key="reason">{{ reason }}</li>
                      </ul>
                    </div>
                    <div>
                      <p class="title">配置建议</p>
                      <p>建议仓位：{{ stock.position }}</p>
                      <p>投资周期：{{ stock.investmentPeriod }}</p>
                    </div>
                    <div>
                      <p class="title">风险提示</p>
                      <p class="risk-text">{{ stock.risks }}</p>
                    </div>
                  </div>
                </el-card>
              </div>
            </section>

            <section class="sub-section">
              <div class="section-header">
                <h3>📋 候选股票列表（筛选后）</h3>
                <el-button icon="el-icon-download" size="mini" @click="downloadCandidates">导出 CSV</el-button>
              </div>
              <el-table :data="candidateList" border stripe size="small" height="360px">
                <el-table-column prop="symbol" label="股票代码" width="110" />
                <el-table-column prop="name" label="股票简称" />
                <el-table-column prop="industry" label="所属行业" min-width="120" />
                <el-table-column prop="netInflow" label="主力净流入" width="140" :formatter="formatCurrencyCell" />
                <el-table-column prop="changePct" label="区间涨跌幅" width="130" :formatter="formatPercentCell" />
                <el-table-column prop="marketCap" label="总市值(亿)" width="120" :formatter="formatNumberCell" />
                <el-table-column prop="pe" label="市盈率" width="100" :formatter="formatNumberCell" />
                <el-table-column prop="pb" label="市净率" width="100" :formatter="formatNumberCell" />
              </el-table>
            </section>

            <section class="sub-section">
              <h3>🤖 AI 分析师团队报告</h3>
              <el-collapse>
                <el-collapse-item v-for="report in analystReports" :key="report.key" :title="report.title">
                  <p class="analysis-text">{{ report.content }}</p>
                </el-collapse-item>
              </el-collapse>
            </section>
          </div>
        </el-tab-pane>

        <el-tab-pane label="📚 批量历史" name="history">
          <div class="history-header">
            <el-input
              v-model="historySearch"
              placeholder="输入关键词过滤历史记录"
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
                    <h4>历史批次 #{{ item.id }}</h4>
                    <p class="subtitle">{{ item.summary }}</p>
                    <p class="tagline">区间：{{ item.range }}</p>
                  </div>
                  <div class="history-metrics">
                    <el-tag type="success">成功 {{ item.success }} 只</el-tag>
                    <el-tag type="info">耗时 {{ item.duration }}</el-tag>
                  </div>
                </div>
                <div class="history-actions">
                  <el-button size="mini" type="primary" icon="el-icon-view" @click="loadHistoryItem(item)">
                    查看详情
                  </el-button>
                </div>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </el-tab-pane>

        <el-tab-pane label="📘 策略指引" name="guide">
          <el-row :gutter="16">
            <el-col :xs="24" :md="14">
              <el-card shadow="never" class="guide-card">
                <h3>功能流程</h3>
                <ol>
                  <li>从问财抓取指定区间内主力净流入 TOP100 股票</li>
                  <li>根据涨跌幅 / 市值等规则过滤，保留安全边际</li>
                  <li>AI 分析师团队从资金、行业、基本面三维打分</li>
                  <li>资深研究员综合定性，输出 3-5 只精选标的</li>
                  <li>可触发批量深度分析，将标的送往多智能体股票分析体系</li>
                </ol>
              </el-card>
            </el-col>
            <el-col :xs="24" :md="10">
              <el-card shadow="never" class="guide-card">
                <h3>使用贴士</h3>
                <ul class="guide-list">
                  <li>大盘震荡时，可收紧最大涨跌幅，重点寻找换手温和的龙头</li>
                  <li>若聚焦中小市值，可调低最小市值门槛并减少最终推荐数量</li>
                  <li>建议每日收盘后运行一次，与实时盯盘联动构建监测清单</li>
                </ul>
                <el-alert
                  type="warning"
                  :closable="false"
                  class="inline-alert"
                  title="批量深度分析会调用多智能体股票分析流程，执行时间可能 10-15 分钟。"
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
import { analyzeMainforce, getMainforceHistory } from '@/api/mainforce'

const MODEL_OPTIONS = [
  { value: 'deepseek-chat', label: 'DeepSeek V3 Chat（默认）' },
  { value: 'deepseek-reasoner', label: 'DeepSeek-R1 Reasoner' },
  { value: 'openai-gpt4o', label: 'OpenAI GPT-4o' }
]

const createFallbackResult = () => {
  const timestamp = dayjs().format('YYYY-MM-DD HH:mm:ss')
  return {
    success: true,
    timestamp,
    total_stocks: 100,
    filtered_stocks: 24,
    final_recommendations: [
      {
        rank: 1,
        symbol: '688041',
        name: '海光信息',
        netInflow: 320000000,
        changePct: 18.4,
        marketCap: 1500,
        position: '30%',
        investmentPeriod: '1-2 周',
        risks: '关注海外科技波动、北向资金态度变化',
        tags: ['算力', '东数西算'],
        reasons: ['章盟主+北上共振吸筹', '订单排期至 Q1，景气度高']
      },
      {
        rank: 2,
        symbol: '603986',
        name: '兆易创新',
        netInflow: 210000000,
        changePct: 12.1,
        marketCap: 1800,
        position: '25%',
        investmentPeriod: '2-3 周',
        risks: '芯片周期波动，对海外需求敏感',
        tags: ['半导体', '存储'],
        reasons: ['存储价格上行 + 国产替代', '游资封板后量能持续']
      },
      {
        rank: 3,
        symbol: '300750',
        name: '宁德时代',
        netInflow: 180000000,
        changePct: 8.3,
        marketCap: 12000,
        position: '20%',
        investmentPeriod: '1-2 月',
        risks: '原材料价格波动，全球新能源需求不确定',
        tags: ['新能源', '电池'],
        reasons: ['主力回流龙头，估值回到合理区间', '储能业务放量']
      }
    ],
    candidates: [
      {
        symbol: '688041',
        name: '海光信息',
        industry: '高性能芯片',
        netInflow: 320000000,
        changePct: 18.4,
        marketCap: 1500,
        pe: 76,
        pb: 8.2
      },
      {
        symbol: '603986',
        name: '兆易创新',
        industry: '半导体',
        netInflow: 210000000,
        changePct: 12.1,
        marketCap: 1800,
        pe: 55,
        pb: 6.4
      },
      {
        symbol: '300750',
        name: '宁德时代',
        industry: '新能源电池',
        netInflow: 180000000,
        changePct: 8.3,
        marketCap: 12000,
        pe: 34,
        pb: 5.1
      },
      {
        symbol: '600703',
        name: '三安光电',
        industry: '光电子',
        netInflow: 145000000,
        changePct: 15.2,
        marketCap: 1600,
        pe: 48,
        pb: 4.3
      }
    ],
    analyst_reports: {
      fund_flow:
        '近三日主力净流入集中在算力、功率半导体、新能源链，机构席位与头部游资出现共振迹象，趋势资金偏向高确定性龙头。',
      industry:
        '算力东数西算、AI 服务器依旧为市场主线；新能源电池在储能与海外需求的带动下方向逐步修复；消费电子仍以低位反弹为主。',
      fundamental:
        '精选标的普遍拥有高 ROE、稳健现金流与清晰成长路径，负债结构健康，估值处于历史 40% 分位以下。'
    }
  }
}

const createFallbackHistory = () => [
  {
    id: 1201,
    summary: '算力主线连续吸金，新能源链条接力，成功输出 5 只核心标的。',
    range: '2024-11-01 ~ 2024-11-28',
    created_at: '2024-11-28 18:30',
    success: 4,
    duration: '8.5 分钟'
  },
  {
    id: 1192,
    summary: '关注中特估 + 高股息轮动，筛选出电力与交通中军品种。',
    range: '2024-10-10 ~ 2024-11-09',
    created_at: '2024-11-09 18:20',
    success: 5,
    duration: '9.2 分钟'
  }
]

export default {
  name: 'MainforceIndex',
  data() {
    return {
      modelOptions: MODEL_OPTIONS,
      selectedModel: MODEL_OPTIONS[0].value,
      rangeOption: '3m',
      customDate: dayjs().subtract(90, 'day').format('YYYY-MM-DD'),
      finalCount: 5,
      maxChange: 30,
      minCap: 50,
      maxCap: 5000,
      advancedCollapse: [],
      analysisLoading: false,
      analysisResult: null,
      candidateCsvCache: '',
      activeTab: 'analysis',
      historyLoading: false,
      historyList: [],
      historySearch: '',
      showAdvanced: false
    }
  },
  computed: {
    quickCards() {
      const result = this.analysisResult || {}
      return [
        { label: '获取股票数', value: result.total_stocks || 0, desc: '问财净流入 TOP100' },
        { label: '筛选后', value: result.filtered_stocks || 0, desc: '剔除涨幅/市值不符' },
        {
          label: '最终推荐',
          value: (result.final_recommendations && result.final_recommendations.length) || 0,
          desc: 'AI 研究员团队定稿'
        },
        { label: '主力净流入阈值', value: `${this.formatCurrency(this.minNetInflow())}`, desc: '前排平均值参考' }
      ]
    },
    recommendedList() {
      return (this.analysisResult && this.analysisResult.final_recommendations) || []
    },
    candidateList() {
      return (this.analysisResult && this.analysisResult.candidates) || []
    },
    analystReports() {
      const reports = []
      const data = this.analysisResult && this.analysisResult.analyst_reports
      if (!data) return reports
      reports.push({
        key: 'fund_flow',
        title: '💰 资金流向分析师',
        content: data.fund_flow || '暂无分析'
      })
      reports.push({
        key: 'industry',
        title: '📊 行业板块分析师',
        content: data.industry || '暂无分析'
      })
      reports.push({
        key: 'fundamental',
        title: '📈 财务基本面分析师',
        content: data.fundamental || '暂无分析'
      })
      return reports
    },
    filteredHistory() {
      if (!this.historySearch) return this.historyList
      const keyword = this.historySearch.toLowerCase()
      return this.historyList.filter(item => {
        const summary = (item.summary || '').toLowerCase()
        const range = (item.range || '').toLowerCase()
        return summary.includes(keyword) || range.includes(keyword) || String(item.id).includes(keyword)
      })
    }
  },
  created() {
    this.loadHistory()
  },
  methods: {
    toggleAdvanced() {
      this.showAdvanced = !this.showAdvanced
    },
    disableFutureDate(date) {
      return date.getTime() > Date.now()
    },
    minNetInflow() {
      if (!this.candidateList.length) return 0
      const sorted = [...this.candidateList].sort((a, b) => Number(b.netInflow || 0) - Number(a.netInflow || 0))
      return sorted[Math.min(2, sorted.length - 1)].netInflow || 0
    },
    formatCurrency(value) {
      const num = Number(value)
      if (Number.isNaN(num)) return '--'
      if (Math.abs(num) >= 1e8) return `${(num / 1e8).toFixed(2)} 亿`
      if (Math.abs(num) >= 1e6) return `${(num / 1e6).toFixed(1)} 百万`
      return `${num.toFixed(0)} 元`
    },
    formatPercent(value) {
      const num = Number(value)
      if (Number.isNaN(num)) return '--'
      return `${num.toFixed(2)}%`
    },
    formatCurrencyCell(row, column, value) {
      return this.formatCurrency(value)
    },
    formatPercentCell(row, column, value) {
      return this.formatPercent(value)
    },
    formatNumberCell(row, column, value) {
      const num = Number(value)
      if (Number.isNaN(num)) return '--'
      return num.toFixed(2)
    },
    composePayload() {
      const payload = {
        model: this.selectedModel,
        final_n: this.finalCount,
        max_range_change: this.maxChange,
        min_market_cap: this.minCap,
        max_market_cap: this.maxCap
      }
      if (this.rangeOption === 'custom') {
        payload.start_date = this.customDate
      } else {
        payload.days_ago = this.rangeOption === '6m' ? 180 : this.rangeOption === '1y' ? 365 : 90
      }
      return payload
    },
    async handleAnalyze() {
      this.analysisLoading = true
      try {
        const res = await analyzeMainforce(this.composePayload())
        const data = res && (res.data || res.result || res)
        if (data && data.success) {
          this.analysisResult = data
          this.$message.success('主力选股分析完成')
        } else {
          throw new Error((data && data.error) || '分析失败')
        }
      } catch (error) {
        console.warn('analyzeMainforce fallback', error)
        this.analysisResult = createFallbackResult()
        this.$message.info('接口暂未打通，展示示例分析结果')
      } finally {
        this.analysisLoading = false
      }
    },
    clearResult() {
      this.analysisResult = null
      this.candidateCsvCache = ''
      this.$message.success('已清除当前分析结果')
    },
    downloadCandidates() {
      if (!this.candidateList.length) {
        this.$message.warning('暂无候选数据')
        return
      }
      if (!this.candidateCsvCache) {
        const header = '股票代码,股票简称,所属行业,主力净流入,涨跌幅(%),总市值(亿),市盈率,市净率\n'
        const rows = this.candidateList
          .map(item => {
            const values = [
              item.symbol,
              item.name,
              item.industry,
              item.netInflow,
              item.changePct,
              item.marketCap,
              item.pe,
              item.pb
            ]
            return values.join(',')
          })
          .join('\n')
        this.candidateCsvCache = `${header}${rows}`
      }
      const blob = new Blob([this.candidateCsvCache], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `mainforce_candidates_${dayjs().format('YYYYMMDD_HHmm')}.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    },
    async loadHistory() {
      this.historyLoading = true
      try {
        const res = await getMainforceHistory()
        const list = Array.isArray(res && (res.items || res)) ? (res.items || res) : []
        this.historyList = list.length ? list : createFallbackHistory()
      } catch (error) {
        console.warn('getMainforceHistory fallback', error)
        this.historyList = createFallbackHistory()
        this.$message.info('历史接口未就绪，展示示例数据')
      } finally {
        this.historyLoading = false
      }
    },
    loadHistoryItem(item) {
      this.$alert('批量历史详情功能将在后续版本开放，敬请期待。', '提示', {
        confirmButtonText: '好的'
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.mainforce-page {
  display: flex;
  flex-direction: column;
  gap: 16px;

  .hero-card {
    background: linear-gradient(135deg, #42a5f5 0%, #5c6bc0 100%);
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
        background: rgba(255, 255, 255, 0.12);
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
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
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

        .recommend-body {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 12px;

          .title {
            font-weight: 600;
            margin-bottom: 4px;
          }

          ul {
            padding-left: 18px;
            margin: 0;
          }

          .risk-text {
            color: #e53935;
          }
        }
      }
    }

    .analysis-text {
      white-space: pre-line;
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

  .guide-card {
    height: 100%;
    line-height: 1.8;
  }

  .guide-list {
    padding-left: 18px;
    line-height: 1.8;
  }

  .inline-alert {
    margin-top: 12px;
  }

  .time-range-block {
    border: 1px solid #ebeef5;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;

    .time-header {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      justify-content: space-between;
      align-items: center;

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

    .time-radios {
      background: #f5f7fa;
      border-radius: 24px;
      padding: 4px;
    }

    .custom-date-row {
      margin-top: 12px;
      display: flex;
      align-items: center;
      gap: 12px;

      .tip {
        color: #909399;
        font-size: 13px;
      }
    }

    .mode-tips {
      margin-top: 12px;
      display: flex;
      align-items: center;
      gap: 8px;
      color: #606266;
      font-size: 13px;
    }
  }

  .advanced-card {
    margin-top: 12px;

    .advanced-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      cursor: pointer;

      h4 {
        margin: 0;
      }

      .subtitle {
        margin: 4px 0 0;
        color: #909399;
        font-size: 13px;
      }

      .advanced-toggle {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        color: #409eff;

        .el-icon-arrow-down {
          transition: transform 0.2s ease;

          &.open {
            transform: rotate(180deg);
          }
        }
      }
    }
  }
}
</style>
