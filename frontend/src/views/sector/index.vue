<template>
  <div class="sector-page app-container">
    <el-card shadow="hover" class="hero-card">
      <div class="hero-content">
        <div>
          <p class="hero-eyebrow">Multi-Agent Sector Strategy</p>
          <h2>🎯 智策板块 · AI多智能体策略中心</h2>
          <p class="hero-subtitle">
            参考 Streamlit 版本的智策体验：一键发起板块多空、轮动、热度全链路分析，内置定时任务与报告管理。
          </p>
          <div class="hero-tags">
            <el-tag effect="dark" type="success">多智能体协同</el-tag>
            <el-tag effect="dark" type="warning">AKShare 数据</el-tag>
            <el-tag effect="dark" type="info">PDF 导出</el-tag>
          </div>
        </div>
        <div class="hero-actions">
          <el-select
            v-model="selectedModel"
            placeholder="选择模型"
            size="large"
            class="hero-select"
          >
            <el-option
              v-for="item in modelOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
          <div class="hero-buttons">
            <el-button
              type="primary"
              icon="el-icon-cpu"
              :loading="analysisLoading"
              @click="handleAnalyze"
            >
              🚀 开始智策分析
            </el-button>
            <el-button icon="el-icon-delete" :disabled="!analysisResult" @click="clearResult">清除结果</el-button>
          </div>
        </div>
      </div>
    </el-card>

    <el-card shadow="hover" class="module-card">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="📊 智策分析" name="analysis">
          <el-row :gutter="16" class="quick-stats">
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
            description="点击上方按钮即可触发智策分析，或从历史报告加载一次结果。"
          />
          <div v-else class="analysis-content">
            <el-alert
              type="success"
              class="inline-alert"
              :closable="false"
              :title="`分析完成于 ${analysisResult.timestamp}`"
            />
            <el-alert
              v-if="analysisResult.cache_meta && analysisResult.cache_meta.from_cache"
              type="warning"
              :closable="false"
              class="inline-alert"
              title="当前分析基于缓存数据，若需实时行情请重新采集后再试。"
            />
            <section class="sub-section">
              <h3>📈 市场数据概览</h3>
              <el-row :gutter="16">
                <el-col v-for="metric in dataMetrics" :key="metric.label" :xs="12" :md="6">
                  <el-card shadow="never" class="metric-card">
                    <p class="label">{{ metric.label }}</p>
                    <p class="value">{{ metric.value }}</p>
                    <p class="desc">{{ metric.desc }}</p>
                  </el-card>
                </el-col>
              </el-row>
            </section>

            <section class="sub-section">
              <div class="section-header">
                <h3>🎯 核心预测</h3>
                <div>
                  <el-button size="mini" icon="el-icon-document" @click="handleExport('markdown')">导出 Markdown</el-button>
                  <el-button
                    size="mini"
                    type="primary"
                    icon="el-icon-printer"
                    @click="handleExport('pdf')"
                  >
                    导出 PDF
                  </el-button>
                </div>
              </div>
              <div class="prediction-grid">
                <div class="prediction-column">
                  <h4>🟢 看多板块</h4>
                  <el-empty v-if="bullishList.length === 0" description="暂无数据" />
                  <el-card
                    v-for="item in bullishList"
                    :key="`bull-${item.sector}`"
                    shadow="never"
                    class="prediction-card bullish"
                  >
                    <div class="card-row">
                      <strong>{{ item.sector }}</strong>
                      <el-tag type="success">{{ item.confidence }}/10</el-tag>
                    </div>
                    <p class="reason">理由：{{ item.reason }}</p>
                    <p class="risk">风险：{{ item.risk }}</p>
                  </el-card>
                </div>
                <div class="prediction-column">
                  <h4>🔴 看空板块</h4>
                  <el-empty v-if="bearishList.length === 0" description="暂无数据" />
                  <el-card
                    v-for="item in bearishList"
                    :key="`bear-${item.sector}`"
                    shadow="never"
                    class="prediction-card bearish"
                  >
                    <div class="card-row">
                      <strong>{{ item.sector }}</strong>
                      <el-tag type="danger">{{ item.confidence }}/10</el-tag>
                    </div>
                    <p class="reason">理由：{{ item.reason }}</p>
                    <p class="risk">风险：{{ item.risk }}</p>
                  </el-card>
                </div>
              </div>
            </section>

            <section class="sub-section">
              <h3>🔄 板块轮动地图</h3>
              <el-row :gutter="16">
                <el-col :md="8" :xs="24">
                  <h4>💪 当前强势</h4>
                  <el-empty v-if="rotation.current_strong.length === 0" description="暂无" />
                  <el-timeline>
                    <el-timeline-item
                      v-for="item in rotation.current_strong"
                      :key="item.sector"
                      color="#4CAF50"
                    >
                      <strong>{{ item.sector }}</strong>
                      <p>时间窗口：{{ item.time_window }}</p>
                      <p>逻辑：{{ item.logic }}</p>
                      <p>建议：{{ item.advice }}</p>
                    </el-timeline-item>
                  </el-timeline>
                </el-col>
                <el-col :md="8" :xs="24">
                  <h4>🌱 潜力接力</h4>
                  <el-empty v-if="rotation.potential.length === 0" description="暂无" />
                  <el-timeline>
                    <el-timeline-item v-for="item in rotation.potential" :key="item.sector" color="#00BCD4">
                      <strong>{{ item.sector }}</strong>
                      <p>时间窗口：{{ item.time_window }}</p>
                      <p>逻辑：{{ item.logic }}</p>
                      <p>建议：{{ item.advice }}</p>
                    </el-timeline-item>
                  </el-timeline>
                </el-col>
                <el-col :md="8" :xs="24">
                  <h4>📉 衰退板块</h4>
                  <el-empty v-if="rotation.declining.length === 0" description="暂无" />
                  <el-timeline>
                    <el-timeline-item v-for="item in rotation.declining" :key="item.sector" color="#FF7043">
                      <strong>{{ item.sector }}</strong>
                      <p>时间窗口：{{ item.time_window }}</p>
                      <p>逻辑：{{ item.logic }}</p>
                      <p>建议：{{ item.advice }}</p>
                    </el-timeline-item>
                  </el-timeline>
                </el-col>
              </el-row>
            </section>

            <section class="sub-section">
              <h3>🔥 板块热度排行</h3>
              <el-row :gutter="16">
                <el-col :md="8" :xs="24">
                  <h4>最热板块</h4>
                  <el-table :data="heatRanks.hottest" size="small" border>
                    <el-table-column prop="sector" label="板块" />
                    <el-table-column prop="score" label="热度" width="70" />
                    <el-table-column prop="trend" label="趋势" width="80" />
                  </el-table>
                </el-col>
                <el-col :md="8" :xs="24">
                  <h4>升温板块</h4>
                  <el-table :data="heatRanks.heating" size="small" border>
                    <el-table-column prop="sector" label="板块" />
                    <el-table-column prop="score" label="热度" width="70" />
                  </el-table>
                </el-col>
                <el-col :md="8" :xs="24">
                  <h4>降温板块</h4>
                  <el-table :data="heatRanks.cooling" size="small" border>
                    <el-table-column prop="sector" label="板块" />
                    <el-table-column prop="score" label="热度" width="70" />
                  </el-table>
                </el-col>
              </el-row>
            </section>

            <section class="sub-section">
              <h3>📝 策略总结</h3>
              <el-row :gutter="16">
                <el-col :md="6" :xs="12">
                  <el-card shadow="never" class="summary-card">
                    <p class="label">市场观点</p>
                    <p class="value">{{ summary.market_view }}</p>
                  </el-card>
                </el-col>
                <el-col :md="6" :xs="12">
                  <el-card shadow="never" class="summary-card">
                    <p class="label">核心机会</p>
                    <p class="value">{{ summary.key_opportunity }}</p>
                  </el-card>
                </el-col>
                <el-col :md="6" :xs="12">
                  <el-card shadow="never" class="summary-card warning">
                    <p class="label">主要风险</p>
                    <p class="value">{{ summary.major_risk }}</p>
                  </el-card>
                </el-col>
                <el-col :md="6" :xs="12">
                  <el-card shadow="never" class="summary-card">
                    <p class="label">整体策略</p>
                    <p class="value">{{ summary.strategy }}</p>
                  </el-card>
                </el-col>
              </el-row>
            </section>

            <section class="sub-section">
              <h3>🤝 智能体报告</h3>
              <el-collapse>
                <el-collapse-item
                  v-for="(agent, idx) in agentList"
                  :key="agent.agent_name + idx"
                  :title="`${agent.agent_name} · ${agent.agent_role}`"
                >
                  <p class="subtitle">关注领域：{{ agent.focus_areas.join('、') }}</p>
                  <p class="timestamp">分析时间：{{ agent.timestamp }}</p>
                  <p class="analysis-text">{{ agent.analysis }}</p>
                </el-collapse-item>
              </el-collapse>
            </section>

            <section class="sub-section">
              <h3>📋 综合研判</h3>
              <el-card shadow="never" class="report-card">
                <p>{{ analysisResult.comprehensive_report }}</p>
              </el-card>
            </section>
          </div>
        </el-tab-pane>
        <el-tab-pane label="⏰ 定时任务" name="schedule">
          <el-row :gutter="16" class="scheduler-row">
            <el-col :xs="24" :lg="14">
              <el-card shadow="hover" class="scheduler-card">
                <template #header>
                  <div class="card-header">
                    <div>
                      <h3>定时执行与通知</h3>
                      <p class="subtitle">每日指定时间自动拉取数据并推送到邮箱 / Webhook</p>
                    </div>
                    <el-tag :type="scheduleForm.enabled ? 'success' : 'info'">
                      {{ scheduleForm.enabled ? '运行中' : '未启用' }}
                    </el-tag>
                  </div>
                </template>
                <el-form label-position="top" :model="scheduleForm">
                  <el-form-item label="运行时间">
                    <el-time-picker
                      v-model="scheduleForm.time"
                      placeholder="选择时间"
                      format="HH:mm"
                      value-format="HH:mm"
                      class="full-width"
                    />
                  </el-form-item>
                  <el-form-item label="启用状态">
                    <el-switch v-model="scheduleForm.enabled" active-text="每日运行" inactive-text="关闭" />
                  </el-form-item>
                  <el-form-item label="邮件通知">
                    <el-switch v-model="scheduleForm.notifyEmail" active-text="开启" inactive-text="关闭" />
                  </el-form-item>
                </el-form>
                <div class="form-actions">
                  <el-button type="primary" :loading="scheduleSaving" @click="saveSchedule">保存设置</el-button>
                  <el-button :loading="scheduleLoading" @click="loadSchedule">刷新状态</el-button>
                  <el-button icon="el-icon-video-play" :loading="manualRunning" @click="handleManualRun">立即运行</el-button>
                </div>
                <el-alert
                  v-if="scheduleInfo.nextRun"
                  type="info"
                  :closable="false"
                  class="inline-alert"
                  :title="`下次运行：${scheduleInfo.nextRun}`"
                />
              </el-card>
            </el-col>
            <el-col :xs="24" :lg="10">
              <el-card shadow="never" class="about-card">
                <h3>使用指引</h3>
                <ul class="guide-list">
                  <li>在 `.env` 中配置 `EMAIL_*`、`WEBHOOK_*`，即可同步 Streamlit 通知策略</li>
                  <li>开启“仅交易时段”可避免盘后噪声；可配合实时监控联动</li>
                  <li>“立即运行”会复用 DeepSeek 模型，耗时约 5~10 分钟</li>
                </ul>
                <el-alert
                  type="warning"
                  :closable="false"
                  title="量化交易账户（MINIQMT）未启用时，自动下单功能不会触发。"
                  class="inline-alert"
                />
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>
        <el-tab-pane label="📚 历史报告" name="history">
          <div class="history-header">
            <el-input
              v-model="historySearch"
              placeholder="输入关键字快速过滤"
              prefix-icon="el-icon-search"
              clearable
              class="history-search"
            />
            <el-button icon="el-icon-refresh" :loading="historyLoading" @click="loadHistory">刷新列表</el-button>
          </div>
          <el-empty v-if="historyList.length === 0" description="暂未找到历史报告" />
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
                    <el-tag type="success">置信度 {{ formatPercent(item.confidence_score) }}</el-tag>
                    <el-tag type="warning">{{ item.market_outlook }}</el-tag>
                  </div>
                </div>
                <div class="history-actions">
                  <el-button size="mini" type="primary" icon="el-icon-view" @click="loadFromHistory(item)">
                    加载到分析视图
                  </el-button>
                </div>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </el-tab-pane>
        <el-tab-pane label="🤖 团队介绍" name="team">
          <el-row :gutter="16">
            <el-col :xs="24" :lg="14">
              <el-card shadow="never" class="about-card">
                <template #header>
                  <div class="card-header">
                    <div>
                      <h3>智策分析师团队</h3>
                      <p class="subtitle">四位 AI 智能体分工协作，复刻 Streamlit 多智能体链路</p>
                    </div>
                  </div>
                </template>
                <el-timeline>
                  <el-timeline-item
                    v-for="member in teamMembers"
                    :key="member.title"
                    placement="top"
                    :color="member.color"
                  >
                    <h4>{{ member.title }}</h4>
                    <p class="subtitle">{{ member.desc }}</p>
                    <p class="tagline">{{ member.focus }}</p>
                  </el-timeline-item>
                </el-timeline>
              </el-card>
            </el-col>
            <el-col :xs="24" :lg="10">
              <el-card shadow="never" class="about-card">
                <h3>功能亮点</h3>
                <ul class="guide-list">
                  <li>宏观/板块/资金/情绪四维度，覆盖多空、轮动、热度核心预测</li>
                  <li>支持 PDF / Markdown 导出，与历史报告一键联动</li>
                  <li>可在侧边栏与主站实时盯盘、主力选股等功能互通</li>
                </ul>
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
  analyzeSector,
  getSectorSchedule,
  setSectorSchedule,
  triggerSectorAnalysis,
  getSectorHistory,
  generateSectorPDF
} from '@/api/sector'

const MODEL_OPTIONS = [
  { value: 'deepseek-chat', label: 'DeepSeek V3 Chat（默认）' },
  { value: 'deepseek-reasoner', label: 'DeepSeek-R1 Reasoner' },
  { value: 'openai-gpt4o', label: 'OpenAI GPT-4o' }
]

const TEAM_MEMBERS = [
  {
    title: '🌐 宏观策略师',
    desc: '追踪宏观经济与政策导向，研判市场风格',
    focus: '宏观经济 · 政策驱动 · 新闻事件',
    color: '#409EFF'
  },
  {
    title: '📊 板块诊断师',
    desc: '量化行业估值与景气度，识别轮动逻辑',
    focus: '行业轮动 · 基本面 · 估值水平',
    color: '#67C23A'
  },
  {
    title: '💰 资金流向分析师',
    desc: '跟踪主力与北向资金偏好，识别资金窗口',
    focus: '主力行为 · 北向资金 · 资金温度计',
    color: '#E6A23C'
  },
  {
    title: '📈 市场情绪解码员',
    desc: '量化 ARBR、赚钱效应与热点热度',
    focus: '情绪指标 · 热度排行 · 风险提示',
    color: '#F56C6C'
  }
]

const createFallbackAnalysis = () => {
  const timestamp = dayjs().format('YYYY-MM-DD HH:mm:ss')
  return {
    success: true,
    timestamp,
    cache_meta: { from_cache: false },
    data_summary: {
      market_overview: {
        sh_index: { close: 3048.32, change_pct: 0.86 },
        up_count: 2481,
        up_ratio: 72.4
      },
      sectors_count: 29,
      concepts_count: 118
    },
    final_predictions: {
      long_short: {
        bullish: [
          {
            sector: '算力与东数西算',
            confidence: 9,
            reason: '海外 AI 训练需求放量 + 国家大算力新基建推进',
            risk: '美股科技回调触发短线共振'
          },
          {
            sector: '新能源车链条',
            confidence: 8,
            reason: '12 月销量冲刺 + 锂矿价格企稳支撑利润端',
            risk: '出口数据若不及预期将压制 Beta'
          }
        ],
        bearish: [
          {
            sector: '房地产开发',
            confidence: 7,
            reason: '销售修复迟缓，资金面持续承压',
            risk: '政策超预期宽松带来反弹'
          },
          {
            sector: '传统券商',
            confidence: 6,
            reason: '成交量未明显放大，投行业务处淡季',
            risk: '若市场量能持续放大将反转'
          }
        ]
      },
      rotation: {
        current_strong: [
          {
            sector: '算力服务器',
            time_window: '1-2 周',
            logic: '海外 GPU 出货高增 + 国内 AI 云算力落地兑现',
            advice: '保持高仓位，关注龙头缩量回踩介入'
          }
        ],
        potential: [
          {
            sector: '光伏储能',
            time_window: '2-4 周',
            logic: '硅料价格见底 + 海外需求回暖',
            advice: '左侧布局，优先选择逆变器龙头'
          }
        ],
        declining: [
          {
            sector: '医美概念',
            time_window: '1 周内',
            logic: '高频数据下滑，盈利修复缓慢',
            advice: '逢反弹减仓'
          }
        ]
      },
      heat: {
        hottest: [
          { sector: '东数西算', score: 93, trend: '升温' },
          { sector: '光模块', score: 90, trend: '维持高温' },
          { sector: '新能源整车', score: 88, trend: '升温' }
        ],
        heating: [
          { sector: '风电装备', score: 82 },
          { sector: '工业母机', score: 78 }
        ],
        cooling: [
          { sector: '医药商业', score: 55 },
          { sector: '白酒', score: 52 }
        ]
      },
      summary: {
        market_view: '指数震荡偏强，成长赛道主导结构',
        key_opportunity: '算力 + 新能源双主线',
        major_risk: '海外科技回调与北向流出',
        strategy: '以进攻为主，结合轮动多线操作'
      }
    },
    agents_analysis: {
      macro: {
        agent_name: '🌐 宏观策略师',
        agent_role: '政策与宏观脉搏',
        focus_areas: ['政策', '宏观数据'],
        timestamp,
        analysis:
          'PMI 回升叠加财政政策逐步落地，成长风格占优；短期需关注海外长端利率变化带来的风险溢价扰动。'
      },
      sector: {
        agent_name: '📊 板块诊断师',
        agent_role: '行业景气侦测',
        focus_areas: ['行业轮动', '估值'],
        timestamp,
        analysis:
          'TMT 估值经调整后重新获得安全边际，新能源链条盈利能力改善，周期板块缺乏催化维度。'
      },
      fund: {
        agent_name: '💰 资金流向分析师',
        agent_role: '主力资金观察',
        focus_areas: ['主力资金', '北向资金'],
        timestamp,
        analysis: '北向净流入集中在电子与电力设备，量化资金加仓高景气成长，存量博弈格局延续。'
      },
      sentiment: {
        agent_name: '📈 市场情绪解码员',
        agent_role: '情绪与热度监控',
        focus_areas: ['情绪指标', '热点追踪'],
        timestamp,
        analysis: '赚钱效应指数处高位，涨停家数回升但连板高度一般，短线仍需控制节奏。'
      }
    },
    comprehensive_report:
      '综合来看，主线依旧围绕算力+新能源的高景气组合展开，可在龙头稳态中寻找低位补涨标的；防守端适度配置高股息电力与交通。短线控制仓位节奏，避免追涨高位题材。',
    saved_report: {
      id: 101,
      summary: '市场震荡向上，成长双主线领跑；关注算力与新能源轮动机会，看空地产与券商。',
      confidence_score: 0.78,
      risk_level: '中等',
      market_outlook: '谨慎乐观',
      data_date_range: dayjs().subtract(7, 'day').format('YYYY-MM-DD') + ' ~ ' + dayjs().format('YYYY-MM-DD'),
      created_at: timestamp
    }
  }
}

const createFallbackHistory = () => [
  {
    id: 96,
    summary: '消费复苏乏力，新能源开始接力，保持结构性进攻。',
    confidence_score: 0.72,
    market_outlook: '中性偏多',
    data_date_range: '2024-11-12 ~ 2024-11-20',
    created_at: '2024-11-20 09:35',
    analysis_content: createFallbackAnalysis()
  },
  {
    id: 92,
    summary: '外部扰动加剧，建议仓位降至五成，关注电力和高股息防守。',
    confidence_score: 0.63,
    market_outlook: '谨慎',
    data_date_range: '2024-11-01 ~ 2024-11-10',
    created_at: '2024-11-10 09:30',
    analysis_content: createFallbackAnalysis()
  }
]

export default {
  name: 'SectorIndex',
  data() {
    return {
      modelOptions: MODEL_OPTIONS,
      teamMembers: TEAM_MEMBERS,
      selectedModel: MODEL_OPTIONS[0].value,
      analysisLoading: false,
      analysisResult: null,
      activeTab: 'analysis',
      scheduleForm: {
        enabled: false,
        time: '09:00',
        notifyEmail: true
      },
      scheduleInfo: {
        nextRun: ''
      },
      scheduleSaving: false,
      scheduleLoading: false,
      manualRunning: false,
      historyLoading: false,
      historyList: [],
      historySearch: ''
    }
  },
  computed: {
    quickCards() {
      return [
        {
          label: 'AI 模型',
          value: this.modelOptions.find(item => item.value === this.selectedModel)?.label || '-',
          desc: '当前用于智策推理的模型'
        },
        {
          label: '报告保存',
          value: this.analysisResult?.saved_report?.id ? '已写入历史库' : '待保存',
          desc: '分析完成后自动入库'
        },
        {
          label: '定时任务',
          value: this.scheduleForm.enabled ? '已开启' : '关闭',
          desc: this.scheduleInfo.nextRun ? `下次：${this.scheduleInfo.nextRun}` : '暂无计划'
        },
        {
          label: '历史报告',
          value: this.historyList.length,
          desc: '最近可回看报告数量'
        }
      ]
    },
    dataMetrics() {
      if (!this.analysisResult) return []
      const overview = this.analysisResult.data_summary?.market_overview || {}
      const sh = overview.sh_index || {}
      return [
        { label: '上证指数', value: sh.close ? `${sh.close.toFixed(2)}` : '--', desc: sh.change_pct ? `${sh.change_pct.toFixed(2)}%` : '--' },
        { label: '上涨家数', value: overview.up_count || '--', desc: overview.up_ratio ? `${overview.up_ratio}%` : '涨跌比' },
        { label: '行业板块', value: this.analysisResult.data_summary?.sectors_count || '--', desc: '覆盖的申万行业' },
        { label: '概念板块', value: this.analysisResult.data_summary?.concepts_count || '--', desc: '热门概念追踪数' }
      ]
    },
    bullishList() {
      return this.analysisResult?.final_predictions?.long_short?.bullish || []
    },
    bearishList() {
      return this.analysisResult?.final_predictions?.long_short?.bearish || []
    },
    rotation() {
      return this.analysisResult?.final_predictions?.rotation || { current_strong: [], potential: [], declining: [] }
    },
    heatRanks() {
      return this.analysisResult?.final_predictions?.heat || { hottest: [], heating: [], cooling: [] }
    },
    summary() {
      return this.analysisResult?.final_predictions?.summary || {
        market_view: '--',
        key_opportunity: '--',
        major_risk: '--',
        strategy: '--'
      }
    },
    agentList() {
      if (!this.analysisResult?.agents_analysis) return []
      return Object.values(this.analysisResult.agents_analysis)
    },
    filteredHistory() {
      if (!this.historySearch) return this.historyList
      const keyword = this.historySearch.toLowerCase()
      return this.historyList.filter(item => item.summary?.toLowerCase().includes(keyword) || String(item.id).includes(keyword))
    }
  },
  created() {
    this.loadSchedule()
    this.loadHistory()
  },
  methods: {
    async handleAnalyze() {
      this.analysisLoading = true
      try {
        const res = await analyzeSector({ model: this.selectedModel })
        const payload = res?.data || res?.result || res
        if (payload && payload.success) {
          this.analysisResult = payload
          this.$message.success('智策分析完成')
        } else {
          throw new Error(payload?.error || '分析失败')
        }
      } catch (error) {
        console.warn('analyzeSector fallback', error)
        this.analysisResult = createFallbackAnalysis()
        this.$message.info('接口暂未打通，已展示示例分析结果')
      } finally {
        this.analysisLoading = false
      }
    },
    clearResult() {
      this.analysisResult = null
      this.$message.success('已清除当前分析结果')
    },
    async loadSchedule() {
      this.scheduleLoading = true
      try {
        const res = await getSectorSchedule()
        const data = res?.data || res || {}
        this.scheduleForm.enabled = Boolean(data.enabled)
        this.scheduleForm.time = data.time || this.scheduleForm.time
        this.scheduleForm.notifyEmail = data.notifyEmail ?? this.scheduleForm.notifyEmail
        this.scheduleInfo.nextRun = data.nextRun || ''
      } catch (error) {
        console.warn('getSectorSchedule fallback', error)
        this.scheduleInfo.nextRun = dayjs().add(1, 'day').format('YYYY-MM-DD 09:00')
        this.$message.info('定时任务接口未准备好，使用默认配置')
      } finally {
        this.scheduleLoading = false
      }
    },
    async saveSchedule() {
      this.scheduleSaving = true
      try {
        await setSectorSchedule(this.scheduleForm)
        this.$message.success('定时任务设置已保存')
        this.loadSchedule()
      } catch (error) {
        console.warn('setSectorSchedule fallback', error)
        this.$message.info('后端暂未实现，示例配置已更新')
      } finally {
        this.scheduleSaving = false
      }
    },
    async handleManualRun() {
      if (!this.scheduleForm.enabled) {
        this.$message.warning('请先开启定时任务再手动触发，或直接点击上方“开始智策分析”。')
        return
      }
      this.manualRunning = true
      try {
        await triggerSectorAnalysis()
        this.$message.success('已触发一次定时任务运行')
      } catch (error) {
        console.warn('triggerSectorAnalysis fallback', error)
        this.$message.info('调度接口未就绪，模拟执行完成')
      } finally {
        this.manualRunning = false
      }
    },
    async loadHistory() {
      this.historyLoading = true
      try {
        const res = await getSectorHistory()
        const list = Array.isArray(res?.items) ? res.items : Array.isArray(res) ? res : []
        this.historyList = list
      } catch (error) {
        console.warn('getSectorHistory fallback', error)
        this.historyList = createFallbackHistory()
        this.$message.info('历史报告接口未连通，展示示例记录')
      } finally {
        this.historyLoading = false
      }
    },
    loadFromHistory(item) {
      if (!item.analysis_content) {
        this.$message.error('该报告缺少分析内容')
        return
      }
      this.analysisResult = item.analysis_content
      this.activeTab = 'analysis'
      this.$message.success(`已加载报告 #${item.id}`)
    },
    formatPercent(value) {
      if (value === null || value === undefined) return '--'
      return `${(Number(value) * 100).toFixed(1)}%`
    },
    async handleExport(type) {
      if (!this.analysisResult?.saved_report?.id) {
        this.$message.warning('请先完成一次分析以生成报告内容')
        return
      }
      if (type === 'markdown') {
        this.$message.info('Markdown 导出将在后端完成，当前展示示例')
        return
      }
      try {
        const blob = await generateSectorPDF({ report_id: this.analysisResult.saved_report.id })
        if (blob) {
          const url = window.URL.createObjectURL(new Blob([blob]))
          const link = document.createElement('a')
          link.href = url
          link.setAttribute('download', `sector-report-${this.analysisResult.saved_report.id}.pdf`)
          document.body.appendChild(link)
          link.click()
          link.remove()
        } else {
          throw new Error('empty file')
        }
      } catch (error) {
        console.warn('generateSectorPDF fallback', error)
        this.$message.info('PDF 生成功能暂未开放，敬请期待')
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.sector-page {
  display: flex;
  flex-direction: column;
  gap: 16px;

  .hero-card {
    background: linear-gradient(135deg, #667eea, #764ba2);
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
      min-width: 280px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
  }

  .quick-stats {
    .stat-card {
      text-align: left;

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
  }

  .scheduler-row {
    .scheduler-card,
    .about-card {
      height: 100%;
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      h3 {
        margin: 0;
      }
    }

    .subtitle {
      color: #909399;
      margin: 4px 0 0;
    }

    .form-actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 12px;
    }

    .inline-alert {
      margin-top: 12px;
    }
  }

  .module-card {
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

    .metric-card {
      .label {
        color: #909399;
      }

      .value {
        font-size: 20px;
        font-weight: 600;
      }
    }

    .prediction-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 16px;

      .prediction-column {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      .prediction-card {
        &.bullish {
          border-left: 4px solid #67c23a;
        }

        &.bearish {
          border-left: 4px solid #f56c6c;
        }

        .card-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .reason,
        .risk {
          margin: 4px 0;
          color: #606266;
        }
      }
    }

    .summary-card {
      min-height: 120px;

      &.warning {
        background: #fff7e6;
      }

      .label {
        color: #909399;
        margin-bottom: 8px;
      }

      .value {
        font-weight: 600;
        line-height: 1.4;
      }
    }

    .analysis-text {
      white-space: pre-line;
      line-height: 1.7;
    }

    .report-card {
      line-height: 1.8;
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

  .guide-list {
    padding-left: 16px;
    line-height: 1.8;
    color: #606266;
    li {
      margin-bottom: 4px;
    }
  }
}
</style>
