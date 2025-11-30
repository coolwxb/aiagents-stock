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
                  <el-tab-pane label="🤝 团队讨论">
                    <div class="discussion-card">
                      <div class="markdown-content" v-html="renderMarkdown(analysisResult.discussion_result)"></div>
                    </div>
                  </el-tab-pane>
                  <el-tab-pane
                    v-for="agent in agentList"
                    :key="agent.agent_name"
                    :label="agent.agent_name"
                  >
                    <div class="agent-card">
                      <p class="role">{{ agent.agent_role }}</p>
                      <p class="focus">关注领域：{{ agent.focus_areas.join('、') }}</p>
                      <p class="timestamp">分析时间：{{ agent.timestamp }}</p>
                      <div class="markdown-content" v-html="renderMarkdown(agent.analysis)"></div>
                    </div>
                  </el-tab-pane>
                </el-tabs>
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
              :timestamp="formatDate(record.created_at)"
              placement="top"
            >
              <el-card shadow="never" class="history-card">
                <div class="card-header">
                  <div class="stock-info">
                    <h4>{{ record.stock_name }} ({{ record.stock_code }})</h4>
                    <div class="rating-section">
                      <el-tag :type="getRatingType(record.rating)">{{ record.rating }}</el-tag>
                      <span class="confidence">信心度：{{ formatConfidence(record.confidence_level) }}</span>
                    </div>
                  </div>
                  <div class="action-buttons">
                    <el-button size="mini" type="primary" @click="viewDetail(record)">查看详情</el-button>
                  </div>
                </div>
                
                <div class="decision-summary" v-if="record.analysis_result && record.analysis_result.final_decision">
                  <div class="summary-row">
                    <div class="summary-item">
                      <span class="label">目标价</span>
                      <span class="value">{{ formatCurrency(record.analysis_result.final_decision.target_price) }}</span>
                    </div>
                    <div class="summary-item">
                      <span class="label">持仓周期</span>
                      <span class="value">{{ record.analysis_result.final_decision.holding_period || 'N/A' }}</span>
                    </div>
                    <div class="summary-item">
                      <span class="label">建议仓位</span>
                      <span class="value">{{ record.analysis_result.final_decision.position_size || 'N/A' }}</span>
                    </div>
                  </div>
                  
                  <div class="summary-row">
                    <div class="summary-item">
                      <span class="label">进场区间</span>
                      <span class="value">{{ record.analysis_result.final_decision.entry_range || 'N/A' }}</span>
                    </div>
                    <div class="summary-item">
                      <span class="label">止盈位</span>
                      <span class="value">{{ formatCurrency(record.analysis_result.final_decision.take_profit) }}</span>
                    </div>
                    <div class="summary-item">
                      <span class="label">止损位</span>
                      <span class="value">{{ formatCurrency(record.analysis_result.final_decision.stop_loss) }}</span>
                    </div>
                  </div>
                  
                  <div class="operation-advice">
                    <p class="label">操作建议</p>
                    <p class="content">{{ record.analysis_result.final_decision.operation_advice || 'N/A' }}</p>
                  </div>
                  
                  <div class="risk-warning" v-if="record.analysis_result.final_decision.risk_warning">
                    <p class="label">风险提示</p>
                    <p class="content warning">{{ record.analysis_result.final_decision.risk_warning }}</p>
                  </div>
                </div>
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

  <!-- 分析详情对话框 -->
  <el-dialog
    :visible.sync="detailDialogVisible"
    :title="currentDetailRecord ? `${currentDetailRecord.stock_name} (${currentDetailRecord.stock_code}) 分析详情` : '分析详情'"
    width="80%"
    top="5vh"
    :before-close="closeDetailDialog"
  >
    <div v-if="currentDetailRecord" class="detail-dialog-content">
      <!-- 基本信息 -->
      <el-card shadow="never" class="detail-section">
        <div class="section-header">
          <h3>📊 投资决策</h3>
        </div>
        <div class="decision-grid" v-if="currentDetailRecord.analysis_result && currentDetailRecord.analysis_result.final_decision">
          <div class="decision-item">
            <p class="label">评级</p>
            <el-tag :type="getRatingType(currentDetailRecord.analysis_result.final_decision.rating)">
              {{ currentDetailRecord.analysis_result.final_decision.rating }}
            </el-tag>
          </div>
          <div class="decision-item">
            <p class="label">信心度</p>
            <p class="value">{{ formatConfidence(currentDetailRecord.analysis_result.final_decision.confidence_level) }}</p>
          </div>
          <div class="decision-item">
            <p class="label">目标价</p>
            <p class="value">{{ formatCurrency(currentDetailRecord.analysis_result.final_decision.target_price) }}</p>
          </div>
          <div class="decision-item">
            <p class="label">持仓周期</p>
            <p class="value">{{ currentDetailRecord.analysis_result.final_decision.holding_period || 'N/A' }}</p>
          </div>
          <div class="decision-item">
            <p class="label">建议仓位</p>
            <p class="value">{{ currentDetailRecord.analysis_result.final_decision.position_size || 'N/A' }}</p>
          </div>
          <div class="decision-item">
            <p class="label">进场区间</p>
            <p class="value">{{ currentDetailRecord.analysis_result.final_decision.entry_range || 'N/A' }}</p>
          </div>
          <div class="decision-item">
            <p class="label">止盈位</p>
            <p class="value">{{ formatCurrency(currentDetailRecord.analysis_result.final_decision.take_profit) }}</p>
          </div>
          <div class="decision-item">
            <p class="label">止损位</p>
            <p class="value">{{ formatCurrency(currentDetailRecord.analysis_result.final_decision.stop_loss) }}</p>
          </div>
        </div>
        
        <div class="decision-text" v-if="currentDetailRecord.analysis_result && currentDetailRecord.analysis_result.final_decision">
          <div class="text-item">
            <p class="label">操作建议</p>
            <p class="content">{{ currentDetailRecord.analysis_result.final_decision.operation_advice || 'N/A' }}</p>
          </div>
          <div class="text-item" v-if="currentDetailRecord.analysis_result.final_decision.risk_warning">
            <p class="label">风险提示</p>
            <p class="content warning">{{ currentDetailRecord.analysis_result.final_decision.risk_warning }}</p>
          </div>
        </div>
      </el-card>
      
      <!-- 分析师报告 -->
      <el-card shadow="never" class="detail-section" v-if="currentDetailRecord.analysis_result && currentDetailRecord.analysis_result.agents_results">
        <div class="section-header">
          <h3>🤖 AI 分析师团队报告</h3>
        </div>
        <el-tabs class="agent-tabs">
          <el-tab-pane label="🤝 团队讨论" v-if="currentDetailRecord.analysis_result && currentDetailRecord.analysis_result.discussion_result">
            <div class="discussion-content">
              <div class="markdown-content" v-html="renderMarkdown(currentDetailRecord.analysis_result.discussion_result)"></div>
            </div>
          </el-tab-pane>
          <el-tab-pane
            v-for="(agent, key) in currentDetailRecord.analysis_result.agents_results"
            :key="key"
            :label="agent.agent_name"
          >
            <div class="agent-detail-card">
              <div class="agent-header">
                <p class="role">{{ agent.agent_role }}</p>
                <p class="focus">关注领域：{{ agent.focus_areas ? agent.focus_areas.join('、') : 'N/A' }}</p>
                <p class="timestamp">分析时间：{{ agent.timestamp || 'N/A' }}</p>
              </div>
              <div class="agent-content">
                <div class="markdown-content" v-html="renderMarkdown(agent.analysis)"></div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>
    
    <span slot="footer" class="dialog-footer">
      <el-button @click="closeDetailDialog">关闭</el-button>
      <el-button type="primary" @click="exportDetailReport">导出报告</el-button>
    </span>
  </el-dialog>
  </div>
</template>

<script>
import dayjs from 'dayjs'
import { marked } from 'marked'
import {
  analyzeStock,
  batchAnalyzeStock,
  getStockHistory,
  generateStockPDF
} from '@/api/stock'

// 配置 marked 选项
marked.setOptions({
  breaks: true, // 支持 GitHub 风格的换行
  gfm: true, // 启用 GitHub 风格的 Markdown
  headerIds: false,
  mangle: false
})

const MODEL_OPTIONS = [
  { value: 'deepseek-chat', label: 'DeepSeek V3 Chat' },
  { value: 'deepseek-reasoner', label: 'DeepSeek-R1 Reasoner' },
  { value: 'openai-gpt4o', label: 'OpenAI GPT-4o' }
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
      historySearch: '',
      detailDialogVisible: false,
      currentDetailRecord: null,
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
    console.log('StockIndex component created, calling loadHistory...')
    this.loadHistory()
  },
  mounted() {
    console.log('StockIndex component mounted')
    // 如果 created 中没有成功调用，在 mounted 中再次尝试
    if (this.historyList.length === 0 && !this.historyLoading) {
      console.log('History list is empty, calling loadHistory from mounted...')
      this.loadHistory()
    }
  },
  methods: {
    renderMarkdown(text) {
      if (!text) return ''
      try {
        return marked(text)
      } catch (error) {
        console.error('Markdown 渲染失败:', error)
        return text
      }
    },
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
          stock_code: this.singleForm.symbol,
          period: this.singleForm.period,
          model: this.selectedModel,
          analysts: this.analysts
        }
        const res = await analyzeStock(payload)
        const data = (res && (res.data || res.result || res)) || {}
        if (data.success) {
          this.analysisResult = data
          this.analysisMode = 'single'
          this.$message.success('分析完成')
        } else {
          throw new Error(data.error || '分析失败')
        }
      } catch (error) {
        console.error('股票分析失败:', error)
        this.analysisResult = null
        const errorMsg = error?.response?.data?.error || error?.message || '分析失败，请检查网络连接或稍后重试'
        this.$message.error(errorMsg)
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
        console.error('批量分析失败:', error)
        this.batchResults = []
        const errorMsg = error?.response?.data?.error || error?.message || '批量分析失败，请检查网络连接或稍后重试'
        this.$message.error(errorMsg)
      } finally {
        this.analysisLoading = false
      }
    },
    async loadHistory() {
      console.log('loadHistory method called')
      this.historyLoading = true
      try {
        console.log('Calling getStockHistory API...')
        const res = await getStockHistory()
        console.log('getStockHistory response:', res)
        const list = Array.isArray(res && (res.items || res)) ? (res.items || res) : []
        this.historyList = list.length ? list : []
        console.log('History list updated, count:', this.historyList.length)
      } catch (error) {
        console.error('获取历史记录失败:', error)
        this.historyList = []
        this.$message.warning('获取历史记录失败，请稍后重试')
      } finally {
        this.historyLoading = false
        console.log('loadHistory completed')
      }
    },
    async exportReport(type) {
      if (!this.analysisResult || !this.analysisResult.final_decision) {
        this.$message.warning('请先完成一次分析')
        return
      }
      if (type === 'pdf') {
        try {
          const blob = await generateStockPDF({ stock_code: this.stockInfo.symbol })
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
    },

    async exportDetailReport() {
      if (!this.currentDetailRecord) {
        this.$message.warning('请先完成一次分析')
        return
      }

      try {
        const blob = await generateStockPDF({ stock_code: this.currentDetailRecord.stock_code })
        if (!blob) throw new Error('empty')
        const url = window.URL.createObjectURL(new Blob([blob]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `stock-report-${this.currentDetailRecord.stock_code}.pdf`)
        document.body.appendChild(link)
        link.click()
        link.remove()
      } catch (error) {
        console.warn('generateStockPDF fallback', error)
        this.$message.info('PDF 生成功能暂未开放')
      }
    },

    formatDate(value) {
      if (value instanceof Date) {
        return dayjs(value).format('YYYY-MM-DD HH:mm')
      }
      
      if (typeof value === 'string') {
        return dayjs(value).format('YYYY-MM-DD HH:mm')
      } 
      return value
    },
    formatConfidence(value) {
      if (value === null || value === undefined || value === '') return 'N/A'
      return `${Number(value).toFixed(1)}/10`
    },
    getRatingType(rating) {
      if (!rating) return 'info'
      if (rating.includes('买')) return 'success'
      if (rating.includes('卖')) return 'danger'
      return 'warning'
    },

    viewDetail(record) {
      this.currentDetailRecord = record
      this.detailDialogVisible = true
    },

    closeDetailDialog() {
      this.detailDialogVisible = false
      this.currentDetailRecord = null
    },

    getAgentList(record) {
      if (!record.analysis_result || !record.analysis_result.agents_results) return []
      return Object.values(record.analysis_result.agents_results)
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
      margin-bottom: 16px;
      padding-bottom: 12px;
      border-bottom: 1px solid #eee;

      .stock-info {
        h4 {
          margin: 0 0 8px 0;
          font-size: 16px;
          font-weight: 600;
        }

        .rating-section {
          display: flex;
          align-items: center;
          gap: 12px;

          .confidence {
            font-size: 12px;
            color: #909399;
          }
        }
      }

      .action-buttons {
        display: flex;
        align-items: flex-start;
      }
    }

    .decision-summary {
      .summary-row {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        margin-bottom: 12px;

        .summary-item {
          flex: 1;
          min-width: 120px;

          .label {
            font-size: 12px;
            color: #909399;
            margin: 0 0 4px 0;
          }

          .value {
            font-size: 14px;
            font-weight: 600;
            color: #303133;
          }
        }
      }

      .operation-advice, .risk-warning {
        margin-top: 16px;

        .label {
          font-size: 12px;
          color: #909399;
          margin: 0 0 4px 0;
        }

        .content {
          font-size: 13px;
          line-height: 1.5;
          color: #606266;
          margin: 0;

          &.warning {
            color: #e6a23c;
          }
        }
      }
    }
  }

  .guide-card {
    height: 100%;
    line-height: 1.8;
  }

  .inline-alert {
    margin-top: 12px;
  }

  // 鍘嗗彶璁板綍鍗＄墖鏍峰紡
  .history-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 12px;
      margin-bottom: 16px;
      padding-bottom: 12px;
      border-bottom: 1px solid #eee;

      .stock-info {
        h4 {
          margin: 0 0 8px 0;
          font-size: 16px;
          font-weight: 600;
        }

        .rating-section {
          display: flex;
          align-items: center;
          gap: 12px;

          .confidence {
            font-size: 12px;
            color: #909399;
          }
        }
      }

      .action-buttons {
        display: flex;
        align-items: flex-start;
      }
    }

    .decision-summary {
      .summary-row {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        margin-bottom: 12px;

        .summary-item {
          flex: 1;
          min-width: 120px;

          .label {
            font-size: 12px;
            color: #909399;
            margin: 0 0 4px 0;
          }

          .value {
            font-size: 14px;
            font-weight: 600;
            color: #303133;
          }
        }
      }

      .operation-advice, .risk-warning {
        margin-top: 16px;

        .label {
          font-size: 12px;
          color: #909399;
          margin: 0 0 4px 0;
        }

        .content {
          font-size: 13px;
          line-height: 1.5;
          color: #606266;
          margin: 0;

          &.warning {
            color: #e6a23c;
          }
        }
      }
    }
  }

  // 璇︽儏瀵硅瘽妗嗘牱寮?
  .detail-dialog-content {
    .detail-section {
      margin-bottom: 20px;

      .section-header {
        margin-bottom: 16px;

        h3 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
          color: #303133;
        }
      }

      .decision-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
        gap: 16px;
        margin-bottom: 20px;

        .decision-item {
          .label {
            font-size: 12px;
            color: #909399;
            margin: 0 0 4px 0;
          }

          .value {
            font-size: 14px;
            font-weight: 600;
            color: #303133;
          }
        }
      }

      .decision-text {
        .text-item {
          margin-bottom: 16px;

          &:last-child {
            margin-bottom: 0;
          }

          .label {
            font-size: 13px;
            color: #909399;
            margin: 0 0 6px 0;
            font-weight: 500;
          }

          .content {
            font-size: 14px;
            line-height: 1.6;
            color: #606266;
            margin: 0;

            &.warning {
              color: #e6a23c;
            }
          }
        }
      }

      .agent-detail-card {
        .agent-header {
          background: #f5f7fa;
          padding: 12px 16px;
          border-radius: 8px;
          margin-bottom: 16px;

          .role {
            font-size: 14px;
            font-weight: 600;
            color: #303133;
            margin: 0 0 6px 0;
          }

          .focus {
            font-size: 13px;
            color: #606266;
            margin: 0 0 6px 0;
          }

          .timestamp {
            font-size: 12px;
            color: #909399;
            margin: 0;
          }
        }

        .agent-content {
          .analysis-text {
            font-size: 14px;
            line-height: 1.7;
            color: #606266;
            margin: 0;
            white-space: pre-wrap;
          }
        }
      }

      .discussion-content {
        p {
          font-size: 14px;
          line-height: 1.7;
          color: #606266;
          margin: 0;
          white-space: pre-wrap;
        }
      }
    }

    .agent-tabs {
      ::v-deep .el-tabs__header {
        margin-bottom: 20px;
      }
    }
  }

  .dialog-footer {
    text-align: right;
  }

  // Markdown 内容样式
  .markdown-content {
    line-height: 1.8;
    color: #303133;
    word-wrap: break-word;

    ::v-deep {
      h1, h2, h3, h4, h5, h6 {
        margin: 16px 0 8px 0;
        font-weight: 600;
        line-height: 1.4;
        color: #303133;

        &:first-child {
          margin-top: 0;
        }
      }

      h1 {
        font-size: 24px;
        border-bottom: 1px solid #eee;
        padding-bottom: 8px;
      }

      h2 {
        font-size: 20px;
      }

      h3 {
        font-size: 18px;
      }

      h4 {
        font-size: 16px;
      }

      p {
        margin: 8px 0;
        line-height: 1.8;
      }

      ul, ol {
        padding-left: 24px;
        margin: 8px 0;

        li {
          margin: 4px 0;
          line-height: 1.8;
        }
      }

      blockquote {
        margin: 12px 0;
        padding: 8px 16px;
        border-left: 4px solid #409eff;
        background: #ecf5ff;
        color: #606266;

        p {
          margin: 0;
        }
      }

      code {
        padding: 2px 6px;
        margin: 0 2px;
        background: #f5f7fa;
        border: 1px solid #e4e7ed;
        border-radius: 3px;
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.9em;
        color: #e83e8c;
      }

      pre {
        margin: 12px 0;
        padding: 12px;
        background: #f5f7fa;
        border: 1px solid #e4e7ed;
        border-radius: 4px;
        overflow-x: auto;

        code {
          padding: 0;
          margin: 0;
          background: transparent;
          border: none;
          color: #303133;
        }
      }

      table {
        width: 100%;
        margin: 12px 0;
        border-collapse: collapse;
        border: 1px solid #e4e7ed;

        th, td {
          padding: 8px 12px;
          border: 1px solid #e4e7ed;
          text-align: left;
        }

        th {
          background: #f5f7fa;
          font-weight: 600;
        }

        tr:nth-child(even) {
          background: #fafafa;
        }
      }

      strong {
        font-weight: 600;
        color: #303133;
      }

      em {
        font-style: italic;
      }

      hr {
        margin: 16px 0;
        border: none;
        border-top: 1px solid #e4e7ed;
      }

      a {
        color: #409eff;
        text-decoration: none;

        &:hover {
          text-decoration: underline;
        }
      }
    }
  }

  .discussion-card {
    background: #fff;
    border-radius: 10px;
    padding: 16px;

    .markdown-content {
      min-height: 100px;
    }
  }
}
</style>
