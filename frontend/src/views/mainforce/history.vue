<template>
  <div class="history-page app-container">
    <el-card shadow="hover" class="hero-card">
      <div class="hero-content">
        <div>
          <p class="hero-eyebrow">Analysis History</p>
          <h2>📚 批量分析历史记录</h2>
          <p class="hero-subtitle">查看和管理主力选股批量分析的历史记录</p>
        </div>
        <el-button type="text" icon="el-icon-back" @click="goBack">返回主力选股</el-button>
      </div>
    </el-card>

    <!-- 统计信息 -->
    <el-row :gutter="16" class="stats-row" v-if="statistics">
      <el-col :xs="12" :sm="4">
        <el-card shadow="never" class="stat-card">
          <p class="label">总记录数</p>
          <p class="value">{{ statistics.total_records }}</p>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="4">
        <el-card shadow="never" class="stat-card">
          <p class="label">分析股票总数</p>
          <p class="value">{{ statistics.total_stocks_analyzed }}</p>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="4">
        <el-card shadow="never" class="stat-card success">
          <p class="label">成功分析</p>
          <p class="value">{{ statistics.total_success }}</p>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="4">
        <el-card shadow="never" class="stat-card">
          <p class="label">成功率</p>
          <p class="value">{{ statistics.success_rate }}%</p>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="4">
        <el-card shadow="never" class="stat-card">
          <p class="label">平均耗时</p>
          <p class="value">{{ formatDuration(statistics.average_time) }}</p>
        </el-card>
      </el-col>
    </el-row>

    <!-- 历史记录列表 -->
    <el-card shadow="hover" class="list-card">
      <div class="list-header">
        <h3>📋 历史记录</h3>
        <el-button icon="el-icon-refresh" :loading="loading" @click="loadHistory">刷新</el-button>
      </div>

      <el-empty v-if="!loading && historyList.length === 0" description="暂无历史记录" />

      <el-timeline v-else>
        <el-timeline-item v-for="item in historyList" :key="item.id" :timestamp="item.created_at" placement="top">
          <el-card shadow="never" class="history-card">
            <div class="card-header">
              <div>
                <h4>批次 #{{ item.id }}</h4>
                <p class="subtitle">{{ item.summary }}</p>
                <p class="tagline">分析时间：{{ item.range }}</p>
              </div>
              <div class="history-metrics">
                <el-tag type="success">成功 {{ item.success }} 只</el-tag>
                <el-tag type="danger" v-if="item.failed_count > 0">失败 {{ item.failed_count }} 只</el-tag>
                <el-tag type="info">{{ item.duration }}</el-tag>
                <el-tag>{{ item.analysis_mode === 'parallel' ? '并行' : '顺序' }}</el-tag>
              </div>
            </div>
            <div class="history-actions">
              <el-button size="mini" type="primary" icon="el-icon-view" @click="viewDetail(item)">查看详情</el-button>
              <el-button size="mini" type="danger" icon="el-icon-delete" @click="deleteRecord(item)">删除</el-button>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-card>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="批量分析详情" width="900px" top="5vh">
      <div class="detail-content" v-if="currentDetail">
        <el-row :gutter="16" class="detail-stats">
          <el-col :span="6"><el-statistic title="总计分析" :value="currentDetail.batch_count" suffix="只" /></el-col>
          <el-col :span="6"><el-statistic title="成功分析" :value="currentDetail.success" suffix="只" /></el-col>
          <el-col :span="6"><el-statistic title="失败分析" :value="currentDetail.failed_count" suffix="只" /></el-col>
          <el-col :span="6"><el-statistic title="总耗时" :value="formatDuration(currentDetail.total_time)" /></el-col>
        </el-row>
        <el-divider />
        <div v-if="detailSuccessResults.length > 0">
          <h4>✅ 成功分析的股票</h4>
          <el-table :data="detailSuccessResults" border stripe size="small" max-height="300">
            <el-table-column prop="symbol" label="代码" width="100" />
            <el-table-column prop="name" label="名称" width="120" />
            <el-table-column prop="rating" label="评级" width="100">
              <template #default="{ row }"><el-tag :type="getRatingType(row.rating)">{{ row.rating }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="confidence" label="信心度" width="100" />
            <el-table-column prop="entryRange" label="进场区间" width="140" />
            <el-table-column prop="takeProfit" label="止盈位" width="100" />
            <el-table-column prop="stopLoss" label="止损位" width="100" />
          </el-table>
        </div>
        <div v-if="detailFailedResults.length > 0" style="margin-top: 16px;">
          <h4>❌ 分析失败的股票</h4>
          <el-table :data="detailFailedResults" border stripe size="small" max-height="200">
            <el-table-column prop="symbol" label="代码" width="120" />
            <el-table-column prop="error" label="失败原因" />
          </el-table>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { getMainforceHistory, deleteMainforceHistory, getMainforceStatistics } from '@/api/mainforce'

export default {
  name: 'MainforceHistory',
  data() {
    return {
      loading: false,
      historyList: [],
      statistics: null,
      detailVisible: false,
      currentDetail: null
    }
  },
  computed: {
    detailSuccessResults() {
      if (!this.currentDetail || !this.currentDetail.results) return []
      return this.currentDetail.results.filter(r => r.success).map(r => this.formatResult(r))
    },
    detailFailedResults() {
      if (!this.currentDetail || !this.currentDetail.results) return []
      return this.currentDetail.results.filter(r => !r.success)
    }
  },
  created() {
    this.loadHistory()
    this.loadStatistics()
  },
  methods: {
    goBack() { this.$router.push('/mainforce') },
    formatDuration(seconds) {
      if (!seconds) return '--'
      return seconds < 60 ? `${seconds.toFixed(1)}秒` : `${(seconds / 60).toFixed(1)}分钟`
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
        stopLoss: finalDecision.stop_loss || 'N/A'
      }
    },
    getRatingType(rating) {
      const map = { '强烈买入': 'danger', '买入': 'success', '持有': 'warning', '卖出': 'info', '强烈卖出': 'info' }
      return map[rating] || 'info'
    },
    async loadHistory() {
      this.loading = true
      try {
        const res = await getMainforceHistory({ page: 1, page_size: 50 })
        const data = res.data || res.result || res
        this.historyList = data.items || []
      } catch (error) {
        console.error('加载历史记录失败:', error)
        this.$message.error('加载历史记录失败')
      } finally {
        this.loading = false
      }
    },
    async loadStatistics() {
      try {
        const res = await getMainforceStatistics()
        this.statistics = res.data || res.result || res
      } catch (error) {
        console.error('加载统计信息失败:', error)
      }
    },
    viewDetail(item) {
      this.currentDetail = item
      this.detailVisible = true
    },
    async deleteRecord(item) {
      try {
        await this.$confirm(`确定要删除批次 #${item.id} 的记录吗？`, '确认删除', { type: 'warning' })
        await deleteMainforceHistory(item.id)
        this.$message.success('删除成功')
        this.loadHistory()
        this.loadStatistics()
      } catch (error) {
        if (error !== 'cancel') {
          this.$message.error('删除失败: ' + (error.message || '未知错误'))
        }
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.history-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  .hero-card {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    color: #fff;
    .hero-content { display: flex; justify-content: space-between; align-items: center; }
    .hero-eyebrow { font-size: 12px; opacity: 0.9; }
    h2 { margin: 8px 0; }
    .hero-subtitle { opacity: 0.95; }
  }
  .stats-row { margin-bottom: 16px; }
  .stat-card {
    text-align: center;
    .label { color: #909399; margin: 0; font-size: 12px; }
    .value { font-size: 20px; font-weight: 600; margin: 4px 0 0; }
    &.success .value { color: #67c23a; }
  }
  .list-card {
    .list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; h3 { margin: 0; } }
  }
  .history-card {
    .card-header { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 12px; margin-bottom: 12px; }
    h4 { margin: 0; }
    .subtitle { color: #606266; margin: 4px 0 0; }
    .tagline { color: #909399; font-size: 12px; margin: 4px 0 0; }
    .history-metrics { display: flex; gap: 8px; flex-wrap: wrap; }
    .history-actions { display: flex; justify-content: flex-end; gap: 8px; }
  }
  .detail-content {
    .detail-stats { margin-bottom: 16px; }
    h4 { margin: 0 0 12px; }
  }
}
</style>
