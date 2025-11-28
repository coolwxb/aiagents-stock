<template>
  <div class="monitor-page app-container">
    <el-card shadow="hover" class="monitor-panel">
      <div slot="header" class="card-header">
        <div>
          <h2>🤖 AI 盯盘中心</h2>
          <p class="subtitle">参考 Streamlit 版本的智能盯盘体验，集中管理监控任务、通知与量化状态</p>
        </div>
        <div class="header-actions">
          <el-button icon="el-icon-refresh" :loading="tasksLoading" @click="loadAllData">刷新数据</el-button>
          <el-button type="primary" icon="el-icon-plus" @click="setActiveTab('create')">快速添加监控</el-button>
        </div>
      </div>

      <el-alert
        title="智能盯盘会定时检查关键价格区间，并通过邮件 / Webhook / MiniQMT 触发通知或交易。"
        type="info"
        show-icon
        class="page-tip"
        :closable="false"
      />

      <section class="section-block status-section">
        <el-row :gutter="16">
          <el-col v-for="card in statusCards" :key="card.label" :xs="12" :sm="6" :md="6">
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
            :disabled="!hasPausedTask"
            @click="startAllTasks"
          >启动全部任务</el-button>
          <el-button
            type="warning"
            icon="el-icon-video-pause"
            :disabled="!hasRunningTask"
            @click="stopAllTasks"
          >暂停全部任务</el-button>
          <el-button icon="el-icon-refresh-right" @click="loadTasks">刷新任务</el-button>
        </div>
      </section>

      <el-tabs v-model="activeTab" class="monitor-tabs">
        <el-tab-pane label="📋 任务概览" name="tasks">
          <el-card shadow="never" class="section-card">
            <div class="section-header">
              <h3>监控任务列表</h3>
              <div class="header-actions">
                <el-input
                  v-model="filters.keyword"
                  placeholder="搜索股票代码 / 名称"
                  size="small"
                  clearable
                  @clear="handleFilterChange"
                  @keyup.enter.native="handleFilterChange"
                >
                  <el-button slot="append" icon="el-icon-search" @click="handleFilterChange" />
                </el-input>
                <el-select v-model="filters.rating" size="small" placeholder="评级筛选" @change="handleFilterChange">
                  <el-option label="全部评级" value="all" />
                  <el-option label="买入" value="买入" />
                  <el-option label="持有" value="持有" />
                  <el-option label="卖出" value="卖出" />
                </el-select>
                <el-select v-model="filters.status" size="small" placeholder="状态筛选" @change="handleFilterChange">
                  <el-option label="全部状态" value="all" />
                  <el-option label="运行中" value="running" />
                  <el-option label="暂停中" value="paused" />
                </el-select>
              </div>
            </div>
            <el-empty v-if="!tasksLoading && filteredTasks.length === 0" description="暂无监控任务" />
            <el-skeleton v-else-if="tasksLoading" :rows="4" animated />
            <div v-else class="task-grid">
              <el-card
                v-for="task in filteredTasks"
                :key="task.id"
                shadow="always"
                class="task-card"
              >
                <div class="task-header">
                  <div>
                    <h4>{{ task.symbol }} · {{ task.name || '未命名' }}</h4>
                    <div class="task-tags">
                      <el-tag :type="ratingTagType(task.rating)" size="mini">{{ task.rating }}</el-tag>
                      <el-tag
                        :type="task.status === 'running' ? 'success' : 'info'"
                        size="mini"
                      >{{ statusText(task.status) }}</el-tag>
                      <el-tag v-if="task.quant_enabled" type="warning" size="mini">MiniQMT</el-tag>
                    </div>
                  </div>
                  <div class="price-block">
                    <p class="label">当前价格</p>
                    <p class="value">{{ formatCurrency(task.current_price) }}</p>
                    <p class="extra">{{ formatTime(task.last_checked) }}</p>
                  </div>
                </div>
                <el-row :gutter="12" class="task-grid-row">
                  <el-col :sm="6" :xs="12">
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
                  <el-col :sm="6" :xs="12">
                    <p class="label">通知 / 频率</p>
                    <p class="value">
                      {{ task.notification_enabled ? '已启用' : '未启用' }}
                      · {{ task.check_interval }} 分钟
                    </p>
                  </el-col>
                </el-row>
                <div class="task-actions">
                  <el-button
                    size="mini"
                    type="success"
                    :disabled="task.status === 'running'"
                    icon="el-icon-video-play"
                    @click="handleStartTask(task)"
                  >
                    启动
                  </el-button>
                  <el-button
                    size="mini"
                    type="warning"
                    :disabled="task.status !== 'running'"
                    icon="el-icon-video-pause"
                    @click="handleStopTask(task)"
                  >
                    暂停
                  </el-button>
                  <el-button size="mini" icon="el-icon-edit" @click="openEditDialog(task)">编辑</el-button>
                  <el-popconfirm
                    title="删除后无法恢复，确认删除？"
                    @confirm="handleDeleteTask(task)"
                  >
                    <el-button slot="reference" size="mini" type="danger" icon="el-icon-delete">删除</el-button>
                  </el-popconfirm>
                </div>
              </el-card>
            </div>
          </el-card>
        </el-tab-pane>

        <el-tab-pane label="➕ 添加监控" name="create">
          <el-card shadow="never" class="section-card">
            <div class="section-header">
              <h3>添加监控任务</h3>
            </div>
            <el-form
              ref="createFormRef"
              :model="createForm"
              :rules="createRules"
              label-width="120px"
              class="create-form"
            >
              <el-row :gutter="16">
                <el-col :xs="24" :md="12">
                  <el-form-item label="股票代码" prop="symbol">
                    <el-input v-model="createForm.symbol" placeholder="如 600519 / AAPL" clearable />
                  </el-form-item>
                  <el-form-item label="股票名称">
                    <el-input v-model="createForm.name" placeholder="可选，留空自动获取" clearable />
                  </el-form-item>
                  <el-form-item label="投资评级">
                    <el-select v-model="createForm.rating" placeholder="请选择">
                      <el-option label="买入" value="买入" />
                      <el-option label="持有" value="持有" />
                      <el-option label="卖出" value="卖出" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="监测间隔">
                    <el-slider
                      v-model="createForm.check_interval"
                      :min="5"
                      :max="120"
                      :step="5"
                      show-input
                      input-size="small"
                      :format-tooltip="formatIntervalTooltip"
                    />
                  </el-form-item>
                  <el-form-item label="启用通知">
                    <el-switch v-model="createForm.notification_enabled" />
                    <span class="form-tip">开启后触发关键位置会推送到邮件 / Webhook</span>
                  </el-form-item>
                </el-col>

                <el-col :xs="24" :md="12">
                  <el-form-item label="进场区间" required>
                    <div class="range-input">
                      <el-input-number
                        v-model="createForm.entry_min"
                        :min="0"
                        :precision="2"
                        :step="0.1"
                        controls-position="right"
                      />
                      <span class="range-split">~</span>
                      <el-input-number
                        v-model="createForm.entry_max"
                        :min="0"
                        :precision="2"
                        :step="0.1"
                        controls-position="right"
                      />
                    </div>
                  </el-form-item>
                  <el-form-item label="止盈价位">
                    <el-input-number
                      v-model="createForm.take_profit"
                      :min="0"
                      :precision="2"
                      :step="0.1"
                      controls-position="right"
                    />
                  </el-form-item>
                  <el-form-item label="止损价位">
                    <el-input-number
                      v-model="createForm.stop_loss"
                      :min="0"
                      :precision="2"
                      :step="0.1"
                      controls-position="right"
                    />
                  </el-form-item>
                  <el-form-item label="MiniQMT 量化">
                    <el-switch v-model="createForm.quant_enabled" />
                    <span class="form-tip">需要在环境配置中启用 MiniQMT</span>
                  </el-form-item>
                  <transition name="fade">
                    <div v-if="createForm.quant_enabled" class="quant-box">
                      <el-form-item label="最大仓位(%)">
                        <el-slider
                          v-model="createForm.quant_config.max_position_pct"
                          :min="5"
                          :max="50"
                          :step="5"
                          show-input
                          input-size="small"
                        />
                      </el-form-item>
                      <el-form-item label="自动止盈">
                        <el-switch v-model="createForm.quant_config.auto_take_profit" />
                      </el-form-item>
                      <el-form-item label="自动止损">
                        <el-switch v-model="createForm.quant_config.auto_stop_loss" />
                      </el-form-item>
                    </div>
                  </transition>
                </el-col>
              </el-row>
              <div class="form-actions">
                <el-button @click="resetCreateForm">重置</el-button>
                <el-button type="primary" :loading="creatingTask" @click="handleCreateTask">添加监控</el-button>
              </div>
            </el-form>
          </el-card>
        </el-tab-pane>

        <el-tab-pane label="🔔 通知与量化" name="notifications">
          <el-row :gutter="16">
            <el-col :xs="24" :md="12">
              <el-card shadow="never" class="section-card">
                <div class="section-header">
                  <h3>通知概况</h3>
                </div>
                <el-alert
                  type="info"
                  :closable="false"
                  show-icon
                  title="邮件 / Webhook 配置需在「环境配置」页面写入 .env 后重启后端。"
                />
                <el-timeline style="margin-top: 12px">
                  <el-timeline-item
                    v-for="item in notificationList"
                    :key="item.id"
                    :timestamp="item.time"
                    :color="itemColor(item.type)"
                  >
                    {{ item.message }} · {{ item.status }}
                  </el-timeline-item>
                </el-timeline>
              </el-card>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-card shadow="never" class="section-card">
                <div class="section-header">
                  <h3>MiniQMT 状态</h3>
                </div>
                <div class="stat-grid">
                  <div class="stat-item">
                    <p class="label">已启用量化</p>
                    <p class="value">{{ quantSummary.enabled }}/{{ tasks.length }}</p>
                    <p class="desc">任务中启用了 MiniQMT 的数量</p>
                  </div>
                  <div class="stat-item">
                    <p class="label">模拟持仓</p>
                    <p class="value">{{ positions.length }}</p>
                    <p class="desc">从 API / 示例数据读取</p>
                  </div>
                </div>
                <el-table
                  v-if="positions.length"
                  :data="positions"
                  border
                  size="small"
                  class="positions-table"
                >
                  <el-table-column prop="symbol" label="股票" width="100" />
                  <el-table-column prop="quantity" label="数量" width="100" />
                  <el-table-column prop="cost_price" label="成本" />
                  <el-table-column prop="pnl" label="盈亏" />
                </el-table>
                <el-empty v-else description="暂无持仓数据" />
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>

        <el-tab-pane label="📜 决策历史" name="history">
          <el-card shadow="never" class="section-card">
            <div class="section-header">
              <h3>决策历史</h3>
            </div>
            <el-skeleton v-if="historyLoading" :rows="4" animated />
            <el-empty v-else-if="historyList.length === 0" description="暂无历史记录" />
            <el-timeline v-else>
              <el-timeline-item
                v-for="item in historyList"
                :key="item.id"
                :timestamp="formatTime(item.time)"
                :color="ratingColor(item.rating)"
              >
                <div class="history-item">
                  <strong>{{ item.symbol }} · {{ item.rating }}</strong>
                  <p>{{ item.summary }}</p>
                </div>
              </el-timeline-item>
            </el-timeline>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog
      title="编辑监控任务"
      :visible.sync="editDialogVisible"
      width="560px"
      @closed="resetEditForm"
    >
      <el-form ref="editFormRef" :model="editForm" :rules="createRules" label-width="120px">
        <el-form-item label="股票代码" prop="symbol">
          <el-input v-model="editForm.symbol" disabled />
        </el-form-item>
        <el-form-item label="股票名称">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="评级">
          <el-select v-model="editForm.rating">
            <el-option label="买入" value="买入" />
            <el-option label="持有" value="持有" />
            <el-option label="卖出" value="卖出" />
          </el-select>
        </el-form-item>
        <el-form-item label="监测间隔">
          <el-input-number v-model="editForm.check_interval" :min="5" :max="120" :step="5" />
        </el-form-item>
        <el-form-item label="进场区间">
          <div class="range-input">
            <el-input-number v-model="editForm.entry_min" :min="0" :precision="2" :step="0.1" />
            <span class="range-split">~</span>
            <el-input-number v-model="editForm.entry_max" :min="0" :precision="2" :step="0.1" />
          </div>
        </el-form-item>
        <el-form-item label="止盈 / 止损">
          <div class="range-input">
            <el-input-number v-model="editForm.take_profit" :min="0" :precision="2" :step="0.1" />
            <span class="range-split">/</span>
            <el-input-number v-model="editForm.stop_loss" :min="0" :precision="2" :step="0.1" />
          </div>
        </el-form-item>
        <el-form-item label="启用通知">
          <el-switch v-model="editForm.notification_enabled" />
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="updatingTask" @click="handleEditSubmit">保存</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import {
  getMonitorTasks,
  createMonitorTask,
  updateMonitorTask,
  deleteMonitorTask,
  startMonitorTask,
  stopMonitorTask,
  getMonitorHistory,
  getMonitorPositions
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
    check_interval: 15,
    notification_enabled: true,
    quant_enabled: true,
    quant_config: {
      max_position_pct: 20,
      auto_stop_loss: true,
      auto_take_profit: true
    },
    current_price: 1895.2,
    last_checked: '2024-11-28 09:35',
    created_at: '2024-10-01 10:00'
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
    check_interval: 20,
    notification_enabled: true,
    quant_enabled: false,
    current_price: 191.4,
    last_checked: '2024-11-27 22:15',
    created_at: '2024-10-10 09:20'
  }
]

const FALLBACK_NOTIFICATIONS = [
  { id: 1, symbol: '600519', type: 'entry', status: '待发送', message: '接近进场区间 1790', time: '2024-11-28 09:40' },
  { id: 2, symbol: 'AAPL', type: 'take_profit', status: '已发送', message: '触发止盈提醒 220', time: '2024-11-27 22:20' },
  { id: 3, symbol: '00700', type: 'quant_trade', status: '已发送', message: 'MiniQMT 自动减仓 20%', time: '2024-11-27 15:05' }
]

const FALLBACK_POSITIONS = [
  { symbol: '600519', quantity: 200, cost_price: '¥1,820.00', pnl: '+¥14,000' },
  { symbol: 'AAPL', quantity: 120, cost_price: '$185.00', pnl: '+$780' }
]

const FALLBACK_HISTORY = [
  { id: 1, symbol: '600519', rating: '买入', summary: '突破箱体上沿，建议逢低加仓', time: '2024-11-27 15:05' },
  { id: 2, symbol: 'AAPL', rating: '持有', summary: '宏观面承压，维持观望', time: '2024-11-26 22:30' }
]

export default {
  name: 'MonitorLayout',
  data() {
    return {
      activeTab: 'tasks',
      tasksLoading: false,
      tasksFallback: false,
      tasks: [],
      filters: {
        keyword: '',
        rating: 'all',
        status: 'all'
      },
      creatingTask: false,
      updatingTask: false,
      createForm: this.getEmptyTaskForm(),
      createRules: {
        symbol: [{ required: true, message: '请输入股票代码', trigger: 'blur' }]
      },
      editDialogVisible: false,
      editForm: {},
      notificationList: [],
      historyList: [],
      historyLoading: false,
      positions: [],
      quantSummary: {
        enabled: 0
      }
    }
  },
  computed: {
    filteredTasks() {
      return this.tasks.filter(task => {
        const matchKeyword =
          !this.filters.keyword ||
          task.symbol.toLowerCase().includes(this.filters.keyword.toLowerCase()) ||
          (task.name || '').toLowerCase().includes(this.filters.keyword.toLowerCase())
        const matchRating = this.filters.rating === 'all' || task.rating === this.filters.rating
        const matchStatus = this.filters.status === 'all' || task.status === this.filters.status
        return matchKeyword && matchRating && matchStatus
      })
    },
    statusCards() {
      const running = this.tasks.filter(task => task.status === 'running').length
      const paused = this.tasks.length - running
      const quantEnabled = this.tasks.filter(task => task.quant_enabled).length
      return [
        { label: '监控任务', value: this.tasks.length, desc: '已配置的盯盘股票' },
        { label: '运行中', value: running, desc: '实时监控任务' },
        { label: '暂停中', value: paused, desc: '待启动或暂停' },
        { label: '启用量化', value: quantEnabled, desc: '关联 MiniQMT 的任务' }
      ]
    },
    hasRunningTask() {
      return this.tasks.some(task => task.status === 'running')
    },
    hasPausedTask() {
      return this.tasks.some(task => task.status !== 'running')
    }
  },
  created() {
    this.loadAllData()
  },
  methods: {
    loadAllData() {
      this.loadTasks()
      this.loadHistory()
      this.loadPositions()
      this.notificationList = FALLBACK_NOTIFICATIONS
    },
    async loadTasks() {
      this.tasksLoading = true
      this.tasksFallback = false
      try {
        const res = await getMonitorTasks()
        const items = Array.isArray(res?.items) ? res.items : Array.isArray(res) ? res : []
        this.tasks = items
      } catch (error) {
        console.warn('Failed to load monitor tasks, fallback to demo data', error)
        this.tasks = FALLBACK_TASKS
        this.tasksFallback = true
        this.$message.info('监控任务接口暂不可用，使用示例数据')
      } finally {
        this.tasksLoading = false
        this.computeQuantSummary()
      }
    },
    async loadHistory() {
      this.historyLoading = true
      try {
        const res = await getMonitorHistory({ page: 1, page_size: 10 })
        const items = Array.isArray(res?.items) ? res.items : Array.isArray(res) ? res : []
        this.historyList = items
      } catch (error) {
        console.warn('Failed to load monitor history, fallback to demo data', error)
        this.historyList = FALLBACK_HISTORY
        this.$message.info('历史接口暂不可用，展示示例记录')
      } finally {
        this.historyLoading = false
      }
    },
    async loadPositions() {
      try {
        const res = await getMonitorPositions()
        const items = Array.isArray(res?.items) ? res.items : Array.isArray(res) ? res : []
        this.positions = items
      } catch (error) {
        console.warn('Failed to load positions, fallback to demo data', error)
        this.positions = FALLBACK_POSITIONS
      } finally {
        this.computeQuantSummary()
      }
    },
    computeQuantSummary() {
      this.quantSummary.enabled = this.tasks.filter(task => task.quant_enabled).length
    },
    getEmptyTaskForm() {
      return {
        symbol: '',
        name: '',
        rating: '买入',
        status: 'running',
        entry_min: null,
        entry_max: null,
        take_profit: null,
        stop_loss: null,
        check_interval: 15,
        notification_enabled: true,
        quant_enabled: false,
        quant_config: {
          max_position_pct: 20,
          auto_stop_loss: true,
          auto_take_profit: true
        }
      }
    },
    resetCreateForm() {
      this.createForm = this.getEmptyTaskForm()
      this.$nextTick(() => {
        if (this.$refs.createFormRef) {
          this.$refs.createFormRef.clearValidate()
        }
      })
    },
    setActiveTab(tab) {
      this.activeTab = tab
    },
    formatIntervalTooltip(val) {
      return `${val} 分钟`
    },
    handleFilterChange() {
      // computed handles filtering; method exists for watchers/triggers
    },
    formatRange(min, max) {
      if (min === null || max === null || min === undefined || max === undefined) return '--'
      return `${this.formatCurrency(min)} ~ ${this.formatCurrency(max)}`
    },
    formatCurrency(value) {
      if (value === null || value === undefined || value === '') return '--'
      const num = Number(value)
      if (Number.isNaN(num)) return value
      return num >= 1000 ? `¥${num.toFixed(2)}` : `${num.toFixed(2)}`
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
    ratingColor(rating) {
      if (rating === '买入') return '#67C23A'
      if (rating === '卖出') return '#F56C6C'
      if (rating === '持有') return '#E6A23C'
      return '#909399'
    },
    statusText(status) {
      return status === 'running' ? '运行中' : '暂停中'
    },
    itemColor(type) {
      const map = {
        entry: '#67C23A',
        take_profit: '#E6A23C',
        stop_loss: '#F56C6C',
        quant_trade: '#409EFF'
      }
      return map[type] || '#909399'
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
    handleCreateTask() {
      this.$refs.createFormRef.validate(async valid => {
        if (!valid || !this.validateRange(this.createForm)) return
        this.creatingTask = true
        try {
          const payload = { ...this.createForm }
          await createMonitorTask(payload)
          this.$message.success('监控任务已创建')
          this.resetCreateForm()
          this.loadTasks()
        } catch (error) {
          console.warn('create task failed, fallback append', error)
          if (this.tasksFallback) {
            const fakeId = Date.now()
            this.tasks.unshift({ ...this.createForm, id: fakeId })
            this.$message.success('已在示例数据中添加任务')
            this.resetCreateForm()
          } else {
            this.$message.error('创建任务失败，请稍后重试')
          }
        } finally {
          this.creatingTask = false
        }
      })
    },
    openEditDialog(task) {
      this.editForm = { ...task }
      this.editDialogVisible = true
      this.$nextTick(() => {
        if (this.$refs.editFormRef) {
          this.$refs.editFormRef.clearValidate()
        }
      })
    },
    resetEditForm() {
      this.editForm = {}
    },
    handleEditSubmit() {
      this.$refs.editFormRef.validate(async valid => {
        if (!valid || !this.validateRange(this.editForm)) return
        this.updatingTask = true
        try {
          await updateMonitorTask(this.editForm.id, this.editForm)
          this.$message.success('监控任务已更新')
          this.editDialogVisible = false
          this.loadTasks()
        } catch (error) {
          console.warn('update task failed', error)
          if (this.tasksFallback) {
            this.tasks = this.tasks.map(task =>
              task.id === this.editForm.id ? { ...task, ...this.editForm } : task
            )
            this.$message.success('示例任务已更新')
            this.editDialogVisible = false
          } else {
            this.$message.error('更新失败，请稍后重试')
          }
        } finally {
          this.updatingTask = false
        }
      })
    },
    async handleDeleteTask(task) {
      try {
        await deleteMonitorTask(task.id)
        this.$message.success('任务已删除')
        this.loadTasks()
      } catch (error) {
        console.warn('delete task failed', error)
        if (this.tasksFallback) {
          this.tasks = this.tasks.filter(item => item.id !== task.id)
          this.$message.success('示例任务已删除')
        } else {
          this.$message.error('删除失败，请稍后再试')
        }
      }
    },
    async handleStartTask(task) {
      try {
        await startMonitorTask(task.id)
        this.$message.success('任务已启动')
        this.loadTasks()
      } catch (error) {
        console.warn('start task failed', error)
        if (this.tasksFallback) {
          this.tasks = this.tasks.map(item =>
            item.id === task.id ? { ...item, status: 'running' } : item
          )
          this.$message.success('示例任务已设置为运行')
        } else {
          this.$message.error('启动失败')
        }
      }
    },
    async handleStopTask(task) {
      try {
        await stopMonitorTask(task.id)
        this.$message.success('任务已暂停')
        this.loadTasks()
      } catch (error) {
        console.warn('stop task failed', error)
        if (this.tasksFallback) {
          this.tasks = this.tasks.map(item =>
            item.id === task.id ? { ...item, status: 'paused' } : item
          )
          this.$message.success('示例任务已暂停')
        } else {
          this.$message.error('暂停失败')
        }
      }
    },
    startAllTasks() {
      this.filteredTasks.forEach(task => {
        if (task.status !== 'running') {
          this.handleStartTask(task)
        }
      })
    },
    stopAllTasks() {
      this.filteredTasks.forEach(task => {
        if (task.status === 'running') {
          this.handleStopTask(task)
        }
      })
    }
  }
}
</script>

<style scoped>
.monitor-panel {
  border-radius: 14px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
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

.section-block {
  margin-bottom: 24px;
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

.section-card {
  margin-bottom: 24px;
  border-radius: 12px;
}

.monitor-tabs {
  margin-top: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.section-header h3 {
  margin: 0;
}

.header-actions .el-input {
  width: 220px;
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

.quant-box {
  border: 1px dashed #dcdfe6;
  border-radius: 10px;
  padding: 12px;
  background: #f6f9ff;
}

.form-actions {
  margin-top: 12px;
  text-align: right;
}

.task-grid-row {
  margin-top: 8px;
}

.stat-grid {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.stat-item {
  flex: 1;
  padding: 12px;
  background: #f7f9fc;
  border-radius: 10px;
  text-align: center;
}

.stat-item .desc {
  margin: 0;
  color: #909399;
  font-size: 12px;
}

.positions-table {
  margin-top: 12px;
}

.history-item p {
  margin: 4px 0 0;
  color: #606266;
}

.task-grid .el-card__body {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.task-grid .task-actions {
  margin-top: auto;
}

.dialog-footer {
  text-align: right;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter,
.fade-leave-to {
  opacity: 0;
}
</style>

