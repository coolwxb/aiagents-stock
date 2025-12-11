<template>
  <div class="batch-page app-container">
    <el-card shadow="hover" class="hero-card">
      <div class="hero-content">
        <div>
          <p class="hero-eyebrow">Batch Deep Analysis</p>
          <h2>🚀 批量深度分析</h2>
          <p class="hero-subtitle">
            对主力资金净流入TOP股票进行完整的AI团队分析，获取投资评级和关键价位。
          </p>
        </div>
        <el-button type="text" icon="el-icon-back" @click="goBack">返回主力选股</el-button>
      </div>
    </el-card>

    <!-- 分析配置 -->
    <el-card shadow="hover" class="config-card" v-if="!analysisStarted">
      <h3>📋 分析配置</h3>
      <el-form label-position="top">
        <el-form-item label="股票代码列表">
          <el-input
            v-model="stockCodesInput"
            type="textarea"
            :rows="4"
            placeholder="输入股票代码，多个代码用逗号、空格或换行分隔"
          />
          <p class="input-tip">已识别 {{ parsedCodes.length }} 个股票代码</p>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :xs="24" :md="8">
            <el-form-item label="分析模式">
              <el-select v-model="analysisMode" class="full-width">
                <el-option value="sequential" label="顺序分析（稳定）" />
                <el-option value="parallel" label="并行分析（快速）" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="8" v-if="analysisMode === 'parallel'">
            <el-form-item label="并行线程数">
              <el-input-number v-model="maxWorkers" :min="2" :max="5" class="full-width" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="8">
            <el-form-item label="AI模型">
              <el-select v-model="selectedModel" class="full-width">
                <el-option value="deepseek-chat" label="DeepSeek V3 Chat" />
                <el-option value="deepseek-reasoner" label="DeepSeek-R1 Reasoner" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <div class="form-actions">
          <el-button type="primary" size="large" :disabled="parsedCodes.length === 0" @click="startAnalysis">
            🚀 开始批量分析 ({{ parsedCodes.length }} 只)
          </el-button>
        </div>
      </el-form>
    </el-card>

    <!-- 分析进度 -->
    <el-card shadow="hover" class="progress-card" v-if="analysisStarted && !analysisCompleted">
      <h3>⏳ 分析进行中</h3>
      <el-progress :percentage="progressPercent" :stroke-width="20" :format="progressFormat" />
      <p class="progress-text">{{ progressText }}</p>
      <el-alert type="info" :closable="false">
        批量分析可能需要较长时间，请耐心等待。分析完成后结果将自动保存到历史记录。
      </el-alert>
    </el-card>

    <!-- 分析结果 -->
    <el-card shadow="hover" class="result-card" v-if="analysisCompleted">
      <div class="result-header">
        <h3>📊 分析结果</h3>
        <el-button type="text" icon="el-icon-refresh" @click="resetAnalysis">重新分析</el-button>
      </div>
      <el-row :gutter="16" class="stats-row">
        <el-col :xs="12" :sm="6">
          <el-card shadow="never" class="stat-card">
            <p class="label">总计分析</p>
            <p class="value">{{ analysisResult.total }} 只</p>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="6">
          <el-card shadow="never" class="stat-card success">
            <p class="label">成功分析</p>
            <p class="value">{{ analysisResult.success }} 只</p>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="6">
          <el-card shadow="never" class="stat-card danger">
            <p class="label">失败分析</p>
            <p class="value">{{ analysisResult.failed }} 只</p>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="6">
          <el-card shadow="never" class="stat-card">
            <p class="label">总耗时</p>
            <p class="value">{{ formatDuration(analysisResult.elapsed_time) }}</p>
          </el-card>
        </el-col>
      </el-row>

      <div class="result-section" v-if="successResults.length > 0">
        <h4>✅ 成功分析的股票 ({{ successResults.length }} 只)</h4>
        <el-table :data="successResults" border stripe size="small">
          <el-table-column prop="symbol" label="股票代码" width="100" />
          <el-table-column prop="name" label="股票名称" width="120" />
          <el-table-column prop="rating" label="评级" width="100">
            <template #default="{ row }">
              <el-tag :type="getRatingType(row.rating)">{{ row.rating }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="confidence" label="信心度" width="100" />
          <el-table-column prop="entryRange" label="进场区间" width="140" />
          <el-table-column prop="takeProfit" label="止盈位" width="100" />
          <el-table-column prop="stopLoss" label="止损位" width="100" />
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button type="text" size="small" @click="showDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="result-section" v-if="failedResults.length > 0">
        <h4>❌ 分析失败的股票 ({{ failedResults.length }} 只)</h4>
        <el-table :data="failedResults" border stripe size="small">
          <el-table-column prop="symbol" label="股票代码" width="120" />
          <el-table-column prop="error" label="失败原因" />
        </el-table>
      </div>
    </el-card>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" :title="`${currentDetail.symbol} - ${currentDetail.name} 分析详情`" width="800px">
      <div class="detail-content" v-if="currentDetail">
        <el-row :gutter="16">
          <el-col :span="8">
            <el-card shadow="never">
              <p class="label">投资评级</p>
              <p class="value"><el-tag :type="getRatingType(currentDetail.rating)" size="large">{{ currentDetail.rating }}</el-tag></p>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="never">
              <p class="label">信心度</p>
              <p class="value">{{ currentDetail.confidence }}</p>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="never">
              <p class="label">目标价</p>
              <p class="value">{{ currentDetail.targetPrice }}</p>
            </el-card>
          </el-col>
        </el-row>
        <el-divider />
        <el-row :gutter="16">
          <el-col :span="8"><p class="label">进场区间</p><p>{{ currentDetail.entryRange }}</p></el-col>
          <el-col :span="8"><p class="label">止盈位</p><p>{{ currentDetail.takeProfit }}</p></el-col>
          <el-col :span="8"><p class="label">止损位</p><p>{{ currentDetail.stopLoss }}</p></el-col>
        </el-row>
        <el-divider />
        <div v-if="currentDetail.advice">
          <h4>💡 投资建议</h4>
          <p class="advice-text">{{ currentDetail.advice }}</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { batchAnalyzeMainforce } from '@/api/mainforce'

export default {
  name: 'MainforceBatch',
  data() {
    return {
      stockCodesInput: '',
      analysisMode: 'sequential',
      maxWorkers: 3,
      selectedModel: 'deepseek-chat',
      analysisStarted: false,
      analysisCompleted: false,
      analysisResult: null,
      progressPercent: 0,
      progressText: '',
      detailVisible: false,
      currentDetail: {}
    }
  },
  computed: {
    parsedCodes() {
      if (!this.stockCodesInput) return []
      const codes = this.stockCodesInput.split(/[,\s\n]+/).map(code => code.trim()).filter(code => code && /^\d{6}$/.test(code))
      return [...new Set(codes)]
    },
    successResults() {
      if (!this.analysisResult || !this.analysisResult.results) return []
      return this.analysisResult.results.filter(r => r.success).map(r => this.formatResult(r))
    },
    failedResults() {
      if (!this.analysisResult || !this.analysisResult.results) return []
      return this.analysisResult.results.filter(r => !r.success)
    }
  },
  created() {
    const codes = this.$route.query.codes
    if (codes) this.stockCodesInput = codes
  },
  methods: {
    goBack() { this.$router.push('/mainforce') },
    progressFormat(percentage) { return `${percentage}%` },
    formatDuration(seconds) {
      if (!seconds) return '--'
      return seconds < 60 ? `${seconds.toFixed(1)} 秒` : `${(seconds / 60).toFixed(1)} 分钟`
    },
    formatResult(r) {
      const stockInfo = r.stock_info || {}
      const finalDecision = r.final_decision || {}
      return {
        symbol: stockInfo.symbol || r.symbol || '',
        name: stockInfo.name || '',
        rating: finalDecision.rating || 'N/A',
        confidence: finalDecision.confidence_level || 'N/A',
        entryRange: finalDecision.entry_range || 'N/A',
        takeProfit: finalDecision.take_profit || 'N/A',
        stopLoss: finalDecision.stop_loss || 'N/A',
        targetPrice: finalDecision.target_price || 'N/A',
        advice: finalDecision.operation_advice || finalDecision.advice || '',
        raw: r
      }
    },
    getRatingType(rating) {
      const map = { '强烈买入': 'danger', '买入': 'success', '持有': 'warning', '卖出': 'info', '强烈卖出': 'info' }
      return map[rating] || 'info'
    },
    async startAnalysis() {
      if (this.parsedCodes.length === 0) { this.$message.warning('请输入有效的股票代码'); return }
      this.analysisStarted = true
      this.analysisCompleted = false
      this.progressPercent = 0
      this.progressText = '正在初始化分析...'
      const progressInterval = setInterval(() => {
        if (this.progressPercent < 90) {
          this.progressPercent += Math.random() * 5
          this.progressText = `正在分析中... (${Math.floor(this.progressPercent)}%)`
        }
      }, 2000)
      try {
        const res = await batchAnalyzeMainforce({
          stock_codes: this.parsedCodes,
          analysis_mode: this.analysisMode,
          max_workers: this.maxWorkers,
          model: this.selectedModel
        })
        clearInterval(progressInterval)
        this.progressPercent = 100
        this.progressText = '分析完成！'
        const data = res.data || res
        this.analysisResult = data
        this.analysisCompleted = true
        this.$message.success(`批量分析完成！成功 ${data.success} 只，失败 ${data.failed} 只`)
      } catch (error) {
        clearInterval(progressInterval)
        this.$message.error('批量分析失败: ' + (error.message || '未知错误'))
        this.analysisStarted = false
      }
    },
    resetAnalysis() {
      this.analysisStarted = false
      this.analysisCompleted = false
      this.analysisResult = null
      this.progressPercent = 0
    },
    showDetail(row) {
      this.currentDetail = row
      this.detailVisible = true
    }
  }
}
</script>

<style lang="scss" scoped>
.batch-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  .hero-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
    .hero-content { display: flex; justify-content: space-between; align-items: center; }
    .hero-eyebrow { font-size: 12px; opacity: 0.9; }
    h2 { margin: 8px 0; }
    .hero-subtitle { opacity: 0.95; }
  }
  .config-card, .progress-card, .result-card { h3 { margin: 0 0 16px; } }
  .input-tip { color: #909399; font-size: 12px; margin-top: 8px; }
  .full-width { width: 100%; }
  .form-actions { margin-top: 24px; text-align: center; }
  .progress-text { text-align: center; color: #606266; margin: 16px 0; }
  .result-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; h3 { margin: 0; } }
  .stats-row { margin-bottom: 24px; }
  .stat-card {
    text-align: center;
    .label { color: #909399; margin: 0; }
    .value { font-size: 24px; font-weight: 600; margin: 8px 0 0; }
    &.success .value { color: #67c23a; }
    &.danger .value { color: #f56c6c; }
  }
  .result-section { margin-top: 24px; h4 { margin: 0 0 12px; } }
  .detail-content {
    .label { color: #909399; margin: 0 0 4px; }
    .value { font-size: 18px; font-weight: 600; margin: 0; }
    .advice-text { background: #f5f7fa; padding: 12px; border-radius: 8px; line-height: 1.8; }
  }
}
</style>
