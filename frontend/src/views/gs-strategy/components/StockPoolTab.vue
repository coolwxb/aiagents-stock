<template>
  <div class="stock-pool-tab">
    <el-card shadow="never" class="section-card">
      <div class="section-header">
        <h3>股票池管理</h3>
        <div class="header-actions">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索股票代码或名称"
            size="small"
            clearable
            style="width: 200px"
            @clear="handleSearch"
            @keyup.enter.native="handleSearch"
          >
            <el-button slot="append" icon="el-icon-search" @click="handleSearch" />
          </el-input>
          <el-button type="primary" size="small" icon="el-icon-plus" @click="openAddDialog">
            添加股票
          </el-button>
        </div>
      </div>

      <div v-if="loading" class="loading-container">
        <el-row :gutter="20" v-for="i in 4" :key="i" style="margin-bottom: 16px;">
          <el-col :span="4">
            <div class="skeleton-item" style="height: 20px;"></div>
          </el-col>
          <el-col :span="4">
            <div class="skeleton-item" style="height: 20px;"></div>
          </el-col>
          <el-col :span="6">
            <div class="skeleton-item" style="height: 20px;"></div>
          </el-col>
          <el-col :span="10">
            <div class="skeleton-item" style="height: 32px;"></div>
          </el-col>
        </el-row>
      </div>
      <div v-else-if="stockList.length === 0" class="empty-state">
        <i class="el-icon-folder-opened empty-icon"></i>
        <p class="empty-text">暂无股票，点击上方按钮添加</p>
      </div>
      <el-table
        v-else
        :data="stockList"
        border
        stripe
        style="width: 100%; margin-top: 16px"
      >
        <el-table-column prop="stock_code" label="股票代码" min-width="120" align="center" />
        <el-table-column prop="stock_name" label="股票名称" min-width="120" />
        <el-table-column prop="created_at" label="添加时间" min-width="160">
          <template slot-scope="scope">
            {{ formatTime(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="200" align="center" fixed="right">
          <template slot-scope="scope">
            <div class="action-buttons">
              <el-button
                size="mini"
                type="primary"
                icon="el-icon-monitor"
                @click="handleAddToMonitor(scope.row)"
              >
                加入监控
              </el-button>
              <el-button
                size="mini"
                type="danger"
                icon="el-icon-delete"
                @click="confirmRemove(scope.row)"
              >
                移除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加股票对话框 -->
    <el-dialog
      title="添加股票到股票池"
      :visible.sync="addDialogVisible"
      width="400px"
      @closed="resetAddForm"
    >
      <el-form ref="addFormRef" :model="addForm" :rules="addRules" label-width="80px">
        <el-form-item label="股票代码" prop="stock_code">
          <el-input 
            v-model="addForm.stock_code" 
            placeholder="如 600519、000001" 
            clearable
          />
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="addLoading" @click="handleAddStock">确定</el-button>
      </div>
    </el-dialog>

    <!-- 加入监控对话框 -->
    <el-dialog
      title="配置监控参数"
      :visible.sync="monitorDialogVisible"
      width="400px"
      @closed="resetMonitorForm"
    >
      <el-form ref="monitorFormRef" :model="monitorForm" :rules="monitorRules" label-width="100px">
        <el-form-item label="股票">
          <span>{{ monitorForm.stock_code }} - {{ monitorForm.stock_name }}</span>
        </el-form-item>
        <el-form-item label="监测间隔" prop="interval">
          <el-select v-model="monitorForm.interval" placeholder="请选择监测间隔">
            <el-option label="1分钟" :value="60" />
            <el-option label="5分钟" :value="300" />
            <el-option label="10分钟" :value="600" />
            <el-option label="15分钟" :value="900" />
            <el-option label="30分钟" :value="1800" />
            <el-option label="60分钟" :value="3600" />
          </el-select>
          <p class="form-tip">GS策略将按此间隔执行分析</p>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="monitorDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="monitorLoading" @click="handleConfirmMonitor">
          确认加入监控
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import {
  getStockPool,
  addToStockPool,
  removeFromStockPool,
  searchStockPool,
  createMonitor,
  startMonitor
} from '@/api/gs-strategy'

export default {
  name: 'StockPoolTab',
  data() {
    return {
      loading: false,
      stockList: [],
      searchKeyword: '',
      // 添加股票对话框
      addDialogVisible: false,
      addLoading: false,
      addForm: {
        stock_code: ''
      },
      addRules: {
        stock_code: [
          { required: true, message: '请输入股票代码', trigger: 'blur' },
          { pattern: /^[0-9]{6}$/, message: '请输入6位数字股票代码', trigger: 'blur' }
        ]
      },
      // 加入监控对话框
      monitorDialogVisible: false,
      monitorLoading: false,
      monitorForm: {
        stock_id: null,
        stock_code: '',
        stock_name: '',
        interval: 300
      },
      monitorRules: {
        interval: [
          { required: true, message: '请选择监测间隔', trigger: 'change' }
        ]
      }
    }
  },
  created() {
    this.loadStockPool()
  },
  methods: {
    async loadStockPool() {
      this.loading = true
      try {
        const res = await getStockPool()
        this.stockList = res.data || res || []
      } catch (error) {
        console.error('加载股票池失败', error)
        this.$message.error('加载股票池失败')
        this.stockList = []
      } finally {
        this.loading = false
      }
    },
    async handleSearch() {
      if (!this.searchKeyword.trim()) {
        this.loadStockPool()
        return
      }
      this.loading = true
      try {
        const res = await searchStockPool(this.searchKeyword)
        this.stockList = res.data || res || []
      } catch (error) {
        console.error('搜索失败', error)
        this.$message.error('搜索失败')
      } finally {
        this.loading = false
      }
    },
    formatTime(value) {
      if (!value) return '--'
      return String(value).replace('T', ' ').substring(0, 19)
    },
    openAddDialog() {
      this.addDialogVisible = true
    },
    resetAddForm() {
      this.addForm = { stock_code: '' }
      this.$nextTick(() => {
        if (this.$refs.addFormRef) {
          this.$refs.addFormRef.clearValidate()
        }
      })
    },
    handleAddStock() {
      this.$refs.addFormRef.validate(async valid => {
        if (!valid) return
        this.addLoading = true
        try {
          await addToStockPool({ stock_code: this.addForm.stock_code.trim() })
          this.$message.success('添加成功')
          this.addDialogVisible = false
          this.loadStockPool()
        } catch (error) {
          console.error('添加失败', error)
          const msg = error.response?.data?.msg || error.response?.data?.detail || '添加失败'
          this.$message.error(msg)
        } finally {
          this.addLoading = false
        }
      })
    },
    confirmRemove(row) {
      this.$confirm(`确认从股票池中移除 ${row.stock_code} - ${row.stock_name}？`, '提示', {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.handleRemove(row)
      }).catch(() => {})
    },
    async handleRemove(row) {
      try {
        await removeFromStockPool(row.id)
        this.$message.success('移除成功')
        await this.loadStockPool()
      } catch (error) {
        console.error('移除失败', error)
        const msg = error.response?.data?.message || error.response?.data?.detail || '移除失败'
        this.$message.error(msg)
      }
    },
    handleAddToMonitor(row) {
      this.monitorForm = {
        stock_id: row.id,
        stock_code: row.stock_code,
        stock_name: row.stock_name,
        interval: 300
      }
      this.monitorDialogVisible = true
    },
    resetMonitorForm() {
      this.monitorForm = {
        stock_id: null,
        stock_code: '',
        stock_name: '',
        interval: 300
      }
    },
    handleConfirmMonitor() {
      this.$refs.monitorFormRef.validate(valid => {
        if (!valid) return
        this.doConfirmMonitor()
      })
    },
    async doConfirmMonitor() {
      this.monitorLoading = true
      try {
        // 创建监控任务
        const res = await createMonitor({
          stock_id: this.monitorForm.stock_id,
          interval: this.monitorForm.interval
        })
        // 自动启动监控
        const monitorId = res.data?.id || res?.id
        if (monitorId) {
          await startMonitor(monitorId)
        }
        this.$message.success('已加入监控并启动')
        this.monitorDialogVisible = false
        // 通知父组件切换到监控Tab
        this.$emit('add-to-monitor', this.monitorForm)
      } catch (error) {
        console.error('加入监控失败', error)
        const msg = error.response?.data?.msg || error.response?.data?.detail || '加入监控失败'
        this.$message.error(msg)
      } finally {
        this.monitorLoading = false
      }
    },
    // 供父组件调用的刷新方法
    refresh() {
      return this.loadStockPool()
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

.form-tip {
  margin: 4px 0 0;
  color: #909399;
  font-size: 12px;
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

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 8px;
}
</style>
