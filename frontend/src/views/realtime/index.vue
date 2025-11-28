<template>
  <div class="realtime-page app-container">
    <el-card shadow="hover" class="realtime-panel">
      <div slot="header" class="card-header">
        <div>
          <h2>📡 实时监测面板</h2>
          <p class="subtitle">对标 Streamlit 版本的实时盯盘：监控任务、最新提醒与操作控制一应俱全</p>
        </div>
        <div class="header-actions">
          <el-button icon="el-icon-refresh" :loading="tasksLoading" @click="loadAllData">刷新数据</el-button>
          <el-button type="primary" icon="el-icon-plus" @click="setActiveTab('add')">添加监控</el-button>
        </div>
      </div>

      <el-alert
        title="AI 会按照设置的监测间隔检查价格区间并触发通知。仅交易时段模式可避免盘后噪声。"
        type="info"
        class="page-tip"
        show-icon
        :closable="false"
      />

      <section class="status-block">
        <el-row :gutter="16">
          <el-col v-for="card in statusCards" :key="card.label" :sm="6" :xs="12">
            <el-card shadow="never" class="stat-card">
              <p class="label">{{ card.label }}</p>
              <h3 class="value">{{ card.value }}</h3>
              <p class="desc">{{ card.desc }}</p>
            </el-card>
          </el-col>
        </el-row>
        <div class="status-actions">
          <el-button
            type="success"
            icon="el-icon-video-play"
            :disabled="!hasPausedStocks"
            @click="startAll"
          >
            启动全部
          </el-button>
          <el-button
            type="warning"
            icon="el-icon-video-pause"
            :disabled="!hasRunningStocks"
            @click="stopAll"
          >
            暂停全部
          </el-button>
          <el-button icon="el-icon-refresh-right" @click="loadTasks">刷新列表</el-button>
        </div>
      </section>

      <el-tabs v-model="activeTab" class="realtime-tabs">
        <el-tab-pane label="📈 监控列表" name="list">
          <el-card shadow="never" class="section-card">
            <div class="section-header">
              <h3>监控中的股票</h3>
              <div class="header-actions">
                <el-input
                  v-model="filters.keyword"
                  size="small"
                  placeholder="输入代码或名称"
                  clearable
                  @clear="handleFilterChange"
                  @keyup.enter.native="handleFilterChange"
                >
                  <el-button slot="append" icon="el-icon-search" @click="handleFilterChange" />
                </el-input>
                <el-select v-model="filters.rating" size="small" @change="handleFilterChange">
                  <el-option label="全部评级" value="all" />
                  <el-option label="买入" value="买入" />
                  <el-option label="持有" value="持有" />
                  <el-option label="卖出" value="卖出" />
                </el-select>
              </div>
            </div>
            <el-skeleton v-if="tasksLoading" :rows="4" animated />
            <el-empty v-else-if="filteredStocks.length === 0" description="暂无监控任务" />
            <div v-else class="task-grid">
              <el-card
                v-for="task in filteredStocks"
                :key="task.id"
                shadow="always"
                class="task-card"
              >
                <div class="task-header">
                  <div>
                    <h4>{{ task.symbol }} · {{ task.name || '未命名' }}</h4>
                    <div class="task-tags">
                      <el-tag :type="ratingTagType(task.rating)" size="mini">{{ task.rating }}</el-tag>
                      <el-tag :type="task.status === 'running' ? 'success' : 'info'" size="mini">
                        {{ statusText(task.status) }}
                      </el-tag>
                      <el-tag
                        v-if="task.trading_hours_only"
                        type="warning"
                        size="mini"
                      >
                        仅交易时段
                      </el-tag>
                    </div>
                  </div>
                  <div class="price-block">
                    <p class="label">当前价格</p>
                    <p class="value">{{ formatCurrency(task.current_price) }}</p>
                    <p class="extra">{{ formatTime(task.last_checked) }}</p>
                  </div>
                </div>
                <el-row :gutter="12" class="task-grid-row">
                  <el-col :sm="12" :xs="12">
                    <p class="label">进场区间</p>
                    <p class="value">{{ formatRange(task.entry_min, task.entry_max) }}</p>
                  </el-col>
                  <el-col :sm="6" :xs="12">
                    <p class="label">止盈位</p>
                    <p class="value">{{ formatCurrency(task.take_profit) }}</p>
                  </el-col>
                  <el-col :sm="6" :xs="12">
                    <p class="label">止损位</p>
                    <p class="value">{{ formatCurrency(task.stop_loss) }}</p>
                  </el-col>
                </el-row>
                <div class="task-actions">
                  <el-button
                    size="mini"
                    type="success"
                    :disabled="task.status === 'running'"
                    icon="el-icon-video-play"
                    @click="handleStart(task)"
                  >
                    启动
                  </el-button>
                  <el-button
                    size="mini"
                    type="warning"
                    :disabled="task.status !== 'running'"
                    icon="el-icon-video-pause"
                    @click="handleStop(task)"
                  >
                    暂停
                  </el-button>
                  <el-popconfirm title="确认移除该监控？" @confirm="handleRemove(task)">
                    <el-button
                      slot="reference"
                      size="mini"
                      type="danger"
                      icon="el-icon-delete"
                    >
                      移除
                    </el-button>
                  </el-popconfirm>
                </div>
              </el-card>
            </div>
          </el-card>
        </el-tab-pane>

        <el-tab-pane label="➕ 添加监控" name="add">
          <el-card shadow="never" class="section-card">
            <div class="section-header">
              <h3>添加实时监控任务</h3>
            </div>
            <el-form
              ref="createFormRef"
              :model="createForm"
              :rules="createRules"
              label-width="120px"
            >
              <el-row :gutter="16">
                <el-col :xs="24" :md="12">
                  <el-form-item label="股票代码" prop="symbol">
                    <el-input v-model="createForm.symbol" placeholder="如 600519 / AAPL" clearable />
                  </el-form-item>
                  <el-form-item label="股票名称">
                    <el-input v-model="createForm.name" placeholder="可选" clearable />
                  </el-form-item>
                  <el-form-item label="投资评级">
                    <el-select v-model="createForm.rating">
                      <el-option label="买入" value="买入" />
                      <el-option label="持有" value="持有" />
                      <el-option label="卖出" value="卖出" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="仅交易时段">
                    <el-switch v-model="createForm.trading_hours_only" />
                    <span class="form-tip">建议开启，盘后不再重复提醒</span>
                  </el-form-item>
                  <el-form-item label="启用通知">
                    <el-switch v-model="createForm.notification_enabled" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="12">
                  <el-form-item label="监测间隔 (分钟)">
                    <el-slider
                      v-model="createForm.check_interval"
                      :min="5"
                      :max="120"
                      :step="5"
                      show-input
                      input-size="small"
                    />
                  </el-form-item>
                  <el-form-item label="进场区间" required>
                    <div class="range-input">
                      <el-input-number v-model="createForm.entry_min" :min="0" :precision="2" :step="0.1" />
                      <span class="range-split">~</span>
                      <el-input-number v-model="createForm.entry_max" :min="0" :precision="2" :step="0.1" />
                    </div>
                  </el-form-item>
                  <el-form-item label="止盈价位">
                    <el-input-number v-model="createForm.take_profit" :min="0" :precision="2" :step="0.1" />
                  </el-form-item>
                  <el-form-item label="止损价位">
                    <el-input-number v-model="createForm.stop_loss" :min="0" :precision="2" :step="0.1" />
                  </el-form-item>
                </el-col>
              </el-row>
              <div class="form-actions">
                <el-button @click="resetCreateForm">重置</el-button>
                <el-button type="primary" :loading="creatingTask" @click="handleCreate">添加监控</el-button>
              </div>
            </el-form>
          </el-card>
        </el-tab-pane>

        <el-tab-pane label="🔔 最新提醒" name="notifications">
          <el-card shadow="never" class="section-card">
            <div class="section-header">
              <h3>最近通知</h3>
              <el-button size="mini" icon="el-icon-delete" @click="clearNotifications">清空提醒</el-button>
            </div>
            <el-timeline>
              <el-timeline-item
                v-for="item in notificationList"
                :key="item.id"
                :timestamp="item.time"
                :color="itemColor(item.type)"
              >
                {{ item.message }} · {{ item.status }}
              </el-timeline-item>
            </el-timeline>
            <el-empty v-if="notificationList.length === 0" description="暂无提醒" />
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script>
import {
  getMonitorTasks,
  createMonitorTask,
  deleteMonitorTask,
  startMonitorTask,
  stopMonitorTask
} from '@/api/monitor'

const FALLBACK_TASKS = [
  {
    id: 1,
    symbol: '600519',
    name: '贵州茅台',
    rating: '买入',
    status: 'running',
    entry_min: 1780,
    entry_max: 1850,
    take_profit: 2100,
    stop_loss: 1700,
    trading_hours_only: true,
    check_interval: 15,
    current_price: 1895.2,
    last_checked: '2024-11-28 09:35'
  },
  {
    id: 2,
    symbol: 'AAPL',
    name: 'Apple Inc.',
    rating: '持有',
    status: 'paused',
    entry_min: 180,
    entry_max: 188,
    take_profit: 220,
    stop_loss: 172,
    trading_hours_only: false,
    check_interval: 20,
    current_price: 191.4,
    last_checked: '2024-11-27 22:15'
  }
]

const FALLBACK_NOTIFICATIONS = [
  { id: 1, symbol: '600519', type: 'entry', status: '未发送', message: '接近进场区间 1790', time: '2024-11-28 09:40' },
  { id: 2, symbol: 'AAPL', type: 'take_profit', status: '已发送', message: '触发止盈提示 220', time: '2024-11-27 22:20' }
]

export default {
  name: 'RealtimeIndex',
  data() {
    return {
      tasksLoading: false,
      tasks: [],
      notifications: [],
      activeTab: 'list',
      filters: {
        keyword: '',
        rating: 'all'
      },
      createForm: this.getEmptyForm(),
      createRules: {
        symbol: [{ required: true, message: '请输入股票代码', trigger: 'blur' }]
      },
      creatingTask: false
    }
  },
  computed: {
    filteredStocks() {
      return this.tasks.filter(task => {
        const matchKeyword =
          !this.filters.keyword ||
          task.symbol.toLowerCase().includes(this.filters.keyword.toLowerCase()) ||
          (task.name || '').toLowerCase().includes(this.filters.keyword.toLowerCase())
        const matchRating = this.filters.rating === 'all' || task.rating === this.filters.rating
        return matchKeyword && matchRating
      })
    },
    statusCards() {
      const running = this.tasks.filter(task => task.status === 'running').length
      return [
        { label: '监控任务', value: this.tasks.length, desc: '已加入实时监测的股票' },
        { label: '运行中', value: running, desc: '当前活跃的盯盘任务' },
        { label: '暂停中', value: this.tasks.length - running, desc: '等待启动的任务' },
        { label: '提醒数量', value: this.notifications.length, desc: '今日生成的提醒' }
      ]
    },
    notificationList() {
      return this.notifications
    },
    hasRunningStocks() {
      return this.tasks.some(task => task.status === 'running')
    },
    hasPausedStocks() {
      return this.tasks.some(task => task.status !== 'running')
    }
  },
  created() {
    this.loadAllData()
  },
  methods: {
    loadAllData() {
      this.loadTasks()
      this.loadNotifications()
    },
    async loadTasks() {
      this.tasksLoading = true
      try {
        const res = await getMonitorTasks()
        const items = Array.isArray(res?.items) ? res.items : Array.isArray(res) ? res : []
        this.tasks = items
      } catch (error) {
        console.warn('加载实时监测任务失败，使用示例数据', error)
        this.tasks = FALLBACK_TASKS
        this.$message.info('实时监测接口暂未实现，展示示例任务')
      } finally {
        this.tasksLoading = false
      }
    },
    loadNotifications() {
      this.notifications = FALLBACK_NOTIFICATIONS
    },
    handleFilterChange() {
      // computed 已处理筛选，方法用于触发响应
    },
    formatRange(min, max) {
      if (min === null || max === null || min === undefined || max === undefined) return '--'
      return `${this.formatCurrency(min)} ~ ${this.formatCurrency(max)}`
    },
    formatCurrency(value) {
      if (value === null || value === undefined || value === '') return '--'
      const num = Number(value)
      if (Number.isNaN(num)) return value
      return num >= 1000 ? `¥${num.toFixed(2)}` : num.toFixed(2)
    },
    formatTime(value) {
      if (!value) return '--'
      return String(value).replace('T', ' ')
    },
    ratingTagType(rating) {
      if (rating === '买入') return 'success'
      if (rating === '卖出') return 'danger'
      if (rating === '持有') return 'warning'
      return 'info'
    },
    statusText(status) {
      return status === 'running' ? '运行中' : '暂停中'
    },
    itemColor(type) {
      const map = {
        entry: '#67C23A',
        take_profit: '#E6A23C',
        stop_loss: '#F56C6C'
      }
      return map[type] || '#909399'
    },
    setActiveTab(tab) {
      this.activeTab = tab
    },
    resetCreateForm() {
      this.createForm = this.getEmptyForm()
      this.$nextTick(() => {
        if (this.$refs.createFormRef) {
          this.$refs.createFormRef.clearValidate()
        }
      })
    },
    validateRange(form) {
      if (!form.entry_min || !form.entry_max || form.entry_min <= 0 || form.entry_max <= 0) {
        this.$message.error('请填写有效的进场区间')
        return false
      }
      if (form.entry_max <= form.entry_min) {
        this.$message.error('进场区间上限需大于下限')
        return false
      }
      return true
    },
    handleCreate() {
      this.$refs.createFormRef.validate(async valid => {
        if (!valid || !this.validateRange(this.createForm)) return
        this.creatingTask = true
        try {
          await createMonitorTask(this.createForm)
          this.$message.success('监控任务已创建')
          this.resetCreateForm()
          this.loadTasks()
        } catch (error) {
          console.warn('创建监控任务失败', error)
          this.tasks.unshift({ ...this.createForm, id: Date.now(), status: 'running', current_price: '--' })
          this.$message.info('接口暂未实现，已在示例数据中添加')
          this.resetCreateForm()
        } finally {
          this.creatingTask = false
        }
      })
    },
    async handleStart(task) {
      try {
        await startMonitorTask(task.id)
        this.$message.success('已启动监控')
        this.loadTasks()
      } catch (error) {
        console.warn('启动任务失败', error)
        this.tasks = this.tasks.map(item =>
          item.id === task.id ? { ...item, status: 'running' } : item
        )
        this.$message.info('接口未就绪，已在示例中标记为运行')
      }
    },
    async handleStop(task) {
      try {
        await stopMonitorTask(task.id)
        this.$message.success('已暂停监控')
        this.loadTasks()
      } catch (error) {
        console.warn('暂停任务失败', error)
        this.tasks = this.tasks.map(item =>
          item.id === task.id ? { ...item, status: 'paused' } : item
        )
        this.$message.info('接口未就绪，已在示例中标记为暂停')
      }
    },
    async handleRemove(task) {
      try {
        await deleteMonitorTask(task.id)
        this.$message.success('监控已移除')
        this.loadTasks()
      } catch (error) {
        console.warn('移除任务失败', error)
        this.tasks = this.tasks.filter(item => item.id !== task.id)
        this.$message.info('接口未就绪，已在示例中移除')
      }
    },
    startAll() {
      this.filteredStocks.forEach(task => {
        if (task.status !== 'running') {
          this.handleStart(task)
        }
      })
    },
    stopAll() {
      this.filteredStocks.forEach(task => {
        if (task.status === 'running') {
          this.handleStop(task)
        }
      })
    },
    clearNotifications() {
      this.notifications = []
      this.$message.success('提醒已清空（示例数据）')
    },
    getEmptyForm() {
      return {
        symbol: '',
        name: '',
        rating: '买入',
        trading_hours_only: true,
        check_interval: 15,
        entry_min: null,
        entry_max: null,
        take_profit: null,
        stop_loss: null,
        notification_enabled: true
      }
    }
  }
}
</script>

<style scoped>
.realtime-panel {
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
  gap: 10px;
  flex-wrap: wrap;
}

.page-tip {
  margin-bottom: 16px;
}

.status-block {
  margin-bottom: 16px;
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

.status-actions {
  margin-top: 12px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.realtime-tabs {
  margin-top: 16px;
}

.section-card {
  margin-bottom: 24px;
  border-radius: 12px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.task-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.task-card {
  border-radius: 12px;
}

.task-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.task-header h4 {
  margin: 0 0 4px;
}

.task-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.price-block {
  text-align: right;
}

.price-block .label {
  margin: 0;
  color: #909399;
}

.price-block .value {
  margin: 4px 0;
  font-size: 18px;
}

.price-block .extra {
  margin: 0;
  color: #c0c4cc;
  font-size: 12px;
}

.label {
  margin: 0;
  color: #909399;
}

.value {
  margin: 4px 0 0;
  font-weight: 600;
}

.task-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.range-input {
  display: flex;
  align-items: center;
  gap: 8px;
}

.range-split {
  color: #909399;
}

.form-tip {
  margin-left: 8px;
  color: #909399;
  font-size: 12px;
}

.form-actions {
  margin-top: 12px;
  text-align: right;
}
</style>
