<template>
  <div class="monitor-tab">
    <el-card shadow="never" class="section-card">
      <div class="section-header">
        <h3>监控管理</h3>
        <div class="header-actions">
          <el-button
            type="success"
            size="small"
            icon="el-icon-video-play"
            :disabled="!hasPausedMonitors"
            @click="startAllMonitors"
          >
            启动全部
          </el-button>
          <el-button
            type="warning"
            size="small"
            icon="el-icon-video-pause"
            :disabled="!hasRunningMonitors"
            @click="stopAllMonitors"
          >
            暂停全部
          </el-button>
        </div>
      </div>

      <div v-if="loading" class="loading-container">
        <el-row :gutter="20" v-for="i in 4" :key="i" style="margin-bottom: 16px;">
          <el-col :span="3">
            <div class="skeleton-item" style="height: 20px;"></div>
          </el-col>
          <el-col :span="3">
            <div class="skeleton-item" style="height: 20px;"></div>
          </el-col>
          <el-col :span="4">
            <div class="skeleton-item" style="height: 20px;"></div>
          </el-col>
          <el-col :span="3">
            <div class="skeleton-item" style="height: 20px;"></div>
          </el-col>
          <el-col :span="3">
            <div class="skeleton-item" style="height: 20px;"></div>
          </el-col>
          <el-col :span="3">
            <div class="skeleton-item" style="height: 20px;"></div>
          </el-col>
          <el-col :span="3">
            <div class="skeleton-item" style="height: 20px;"></div>
          </el-col>
          <el-col :span="2">
            <div class="skeleton-item" style="height: 32px;"></div>
          </el-col>
        </el-row>
      </div>
      <div v-else-if="monitorList.length === 0" class="empty-state">
        <i class="el-icon-monitor empty-icon"></i>
        <p class="empty-text">暂无监控任务，请从股票池添加</p>
      </div>
      <el-table
        v-else
        :data="monitorList"
        border
        stripe
        style="width: 100%; margin-top: 16px"
      >
        <el-table-column prop="stock_code" label="股票代码" min-width="100" align="center" />
        <el-table-column prop="stock_name" label="股票名称" min-width="100" />
        <el-table-column prop="started_at" label="启动时间" min-width="160">
          <template slot-scope="scope">
            {{ formatTime(scope.row.started_at) }}
          </template>
        </el-table-column>
        <el-table-column label="运行时长" min-width="120">
          <template slot-scope="scope">
            <span v-if="scope.row.status === 'running'">
              {{ getRunningDuration(scope.row) }}
            </span>
            <span v-else>--</span>
          </template>
        </el-table-column>
        <el-table-column prop="execution_count" label="执行次数" min-width="100" align="center">
          <template slot-scope="scope">
            {{ scope.row.execution_count || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="interval" label="监测间隔" min-width="100" align="center">
          <template slot-scope="scope">
            {{ formatInterval(scope.row.interval) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" min-width="100" align="center">
          <template slot-scope="scope">
            <el-tag :type="scope.row.status === 'running' ? 'success' : 'info'" size="small">
              {{ scope.row.status === 'running' ? '运行中' : '已停止' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_signal" label="最后信号" min-width="100" align="center">
          <template slot-scope="scope">
            <el-tag
              v-if="scope.row.last_signal"
              :type="getSignalTagType(scope.row.last_signal)"
              size="small"
            >
              {{ scope.row.last_signal }}
            </el-tag>
            <span v-else>--</span>
          </template>
        </el-table-column>
        <el-table-column prop="pending_order_status_name" label="委托状态" min-width="100" align="center">
          <template slot-scope="scope">
            <el-tag
              v-if="scope.row.pending_order_status_name"
              :type="getOrderStatusTagType(scope.row.pending_order_status_name)"
              size="small"
            >
              {{ scope.row.pending_order_status_name }}
            </el-tag>
            <span v-else>--</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="200" align="center" fixed="right">
          <template slot-scope="scope">
            <el-button
              v-if="scope.row.status !== 'running'"
              size="mini"
              type="success"
              icon="el-icon-video-play"
              @click="handleStart(scope.row)"
            >
              启动
            </el-button>
            <el-button
              v-else
              size="mini"
              type="warning"
              icon="el-icon-video-pause"
              @click="handleStop(scope.row)"
            >
              暂停
            </el-button>
            <el-popconfirm
              title="确认移除该监控任务？"
              @onConfirm="handleRemove(scope.row)"
            >
              <el-button
                slot="reference"
                size="mini"
                type="danger"
                icon="el-icon-delete"
              >
                移除
              </el-button>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加监控对话框（从外部调用） -->
    <el-dialog
      title="配置监控参数"
      :visible.sync="addDialogVisible"
      width="400px"
      @closed="resetAddForm"
    >
      <el-form ref="addFormRef" :model="addForm" :rules="addRules" label-width="100px">
        <el-form-item label="股票">
          <span>{{ addForm.stock_code }} - {{ addForm.stock_name }}</span>
        </el-form-item>
        <el-form-item label="监测间隔" prop="interval">
          <el-select v-model="addForm.interval" placeholder="请选择监测间隔">
            <el-option label="1分钟" :value="60" />
            <el-option label="5分钟" :value="300" />
            <el-option label="10分钟" :value="600" />
            <el-option label="15分钟" :value="900" />
            <el-option label="30分钟" :value="1800" />
            <el-option label="60分钟" :value="3600" />
          </el-select>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="addLoading" @click="handleConfirmAdd">确认</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import {
  getMonitors,
  createMonitor,
  deleteMonitor,
  startMonitor,
  stopMonitor
} from '@/api/gs-strategy'

export default {
  name: 'MonitorTab',
  data() {
    return {
      loading: false,
      monitorList: [],
      durationTimer: null,
      // 添加监控对话框
      addDialogVisible: false,
      addLoading: false,
      addForm: {
        stock_id: null,
        stock_code: '',
        stock_name: '',
        interval: 300
      },
      addRules: {
        interval: [
          { required: true, message: '请选择监测间隔', trigger: 'change' }
        ]
      }
    }
  },
  computed: {
    hasRunningMonitors() {
      return this.monitorList.some(m => m.status === 'running')
    },
    hasPausedMonitors() {
      return this.monitorList.some(m => m.status !== 'running')
    }
  },
  created() {
    this.loadMonitors()
    // 每秒更新运行时长
    this.durationTimer = setInterval(() => {
      this.$forceUpdate()
    }, 1000)
  },
  beforeDestroy() {
    if (this.durationTimer) {
      clearInterval(this.durationTimer)
    }
  },
  methods: {
    async loadMonitors() {
      this.loading = true
      try {
        const res = await getMonitors()
        this.monitorList = res.data || res || []
      } catch (error) {
        console.error('加载监控列表失败', error)
        this.$message.error('加载监控列表失败')
        this.monitorList = []
      } finally {
        this.loading = false
      }
    },
    formatTime(value) {
      if (!value) return '--'
      return String(value).replace('T', ' ').substring(0, 19)
    },
    formatInterval(seconds) {
      if (!seconds) return '--'
      if (seconds < 60) return `${seconds}秒`
      return `${Math.floor(seconds / 60)}分钟`
    },
    getRunningDuration(row) {
      if (!row.started_at || row.status !== 'running') return '--'
      const startTime = new Date(row.started_at).getTime()
      const now = Date.now()
      const diff = Math.floor((now - startTime) / 1000)

      const hours = Math.floor(diff / 3600)
      const minutes = Math.floor((diff % 3600) / 60)
      const seconds = diff % 60

      if (hours > 0) {
        return `${hours}时${minutes}分${seconds}秒`
      } else if (minutes > 0) {
        return `${minutes}分${seconds}秒`
      }
      return `${seconds}秒`
    },
    getSignalTagType(signal) {
      if (signal === 'buy') return 'success'
      if (signal === 'sell') return 'danger'
      return 'info'
    },
    getOrderStatusTagType(status) {
      if (!status) return 'info'
      if (status.includes('成交') || status.includes('已成')) return 'success'
      if (status.includes('废单') || status.includes('撤单') || status.includes('失败')) return 'danger'
      if (status.includes('待') || status.includes('未成') || status.includes('部分')) return 'warning'
      return 'info'
    },
    async handleStart(row) {
      try {
        await startMonitor(row.id)
        this.$message.success('监控已启动')
        this.loadMonitors()
      } catch (error) {
        console.error('启动失败', error)
        this.$message.error('启动失败')
      }
    },
    async handleStop(row) {
      try {
        await stopMonitor(row.id)
        this.$message.success('监控已暂停')
        this.loadMonitors()
      } catch (error) {
        console.error('暂停失败', error)
        this.$message.error('暂停失败')
      }
    },
    async handleRemove(row) {
      try {
        await deleteMonitor(row.id)
        this.$message.success('监控已移除')
        this.loadMonitors()
      } catch (error) {
        console.error('移除失败', error)
        this.$message.error('移除失败')
      }
    },
    async startAllMonitors() {
      const pausedMonitors = this.monitorList.filter(m => m.status !== 'running')
      for (const monitor of pausedMonitors) {
        try {
          await startMonitor(monitor.id)
        } catch (error) {
          console.error(`启动 ${monitor.stock_code} 失败`, error)
        }
      }
      this.$message.success('已启动全部监控')
      this.loadMonitors()
    },
    async stopAllMonitors() {
      const runningMonitors = this.monitorList.filter(m => m.status === 'running')
      for (const monitor of runningMonitors) {
        try {
          await stopMonitor(monitor.id)
        } catch (error) {
          console.error(`暂停 ${monitor.stock_code} 失败`, error)
        }
      }
      this.$message.success('已暂停全部监控')
      this.loadMonitors()
    },
    // 供外部调用的方法
    openAddDialog(stock) {
      this.addForm = {
        stock_id: stock.stock_id || stock.id,
        stock_code: stock.stock_code,
        stock_name: stock.stock_name,
        interval: 300
      }
      this.addDialogVisible = true
    },
    resetAddForm() {
      this.addForm = {
        stock_id: null,
        stock_code: '',
        stock_name: '',
        interval: 300
      }
    },
    async handleConfirmAdd() {
      this.$refs.addFormRef.validate(async valid => {
        if (!valid) return
        this.addLoading = true
        try {
          const res = await createMonitor({
            stock_id: this.addForm.stock_id,
            interval: this.addForm.interval
          })
          const monitorId = res.data?.id || res?.id
          if (monitorId) {
            await startMonitor(monitorId)
          }
          this.$message.success('已加入监控并启动')
          this.addDialogVisible = false
          this.loadMonitors()
        } catch (error) {
          console.error('加入监控失败', error)
          const msg = error.response?.data?.msg || error.response?.data?.detail || '加入监控失败'
          this.$message.error(msg)
        } finally {
          this.addLoading = false
        }
      })
    },
    // 供父组件调用的刷新方法
    refresh() {
      return this.loadMonitors()
    }
  }
}
</script>

<style scoped>
.section-card {
  border-radius: 12px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.section-header h3 {
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.loading-container {
  margin-top: 16px;
}

.skeleton-item {
  background: linear-gradient(90deg, #f2f2f2 25%, #e6e6e6 50%, #f2f2f2 75%);
  background-size: 200% 100%;
  border-radius: 4px;
  animation: skeleton-loading 1.5s infinite;
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  color: #909399;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  color: #c0c4cc;
}

.empty-text {
  margin: 0;
  font-size: 14px;
}

/* 操作按钮样式 */
::v-deep .el-table .cell {
  overflow: visible;
  padding-top: 8px;
  padding-bottom: 8px;
}

::v-deep .el-table__body-wrapper {
  overflow: visible;
}

::v-deep .el-table--border td {
  border-bottom: 1px solid #ebeef5;
}

/* 操作列按钮间距 */
::v-deep .el-table td .cell .el-button {
  margin-right: 12px;
}

::v-deep .el-table td .cell .el-button:last-child {
  margin-right: 0;
}

::v-deep .el-popconfirm {
  display: inline-block;
}

::v-deep .el-popconfirm .el-button {
  margin-right: 0;
}
</style>
