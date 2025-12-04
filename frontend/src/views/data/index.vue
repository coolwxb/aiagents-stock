<template>
  <div class="data-management-container">
    <el-card class="box-card">
      <div slot="header" class="clearfix">
        <span class="card-title">数据管理</span>
        <span class="card-subtitle">从 xtquant 获取并同步板块和股票数据到数据库</span>
      </div>

      <el-tabs v-model="activeTab" type="border-card">
        <!-- 板块管理 Tab -->
        <el-tab-pane label="板块管理" name="sector">
          <div class="tab-content">
            <!-- 操作栏 -->
            <div class="operation-bar">
              <el-button
                type="primary"
                icon="el-icon-refresh"
                :loading="sectorLoading"
                @click="handleUpdateSectors"
              >
                更新板块
              </el-button>
              <el-button
                type="success"
                icon="el-icon-folder-add"
                :loading="sectorStocksLoading"
                @click="handleUpdateSectorStocks"
              >
                更新股票板块
              </el-button>
              <el-button
                type="info"
                icon="el-icon-search"
                @click="loadSectors"
              >
                刷新列表
              </el-button>
            </div>

            <!-- 板块列表 -->
            <el-table
              v-loading="sectorTableLoading"
              :data="sectorList"
              border
              stripe
              style="width: 100%; margin-top: 20px"
            >
              <el-table-column
                prop="sector_code"
                label="板块代码"
                width="200"
              />
              <el-table-column
                prop="sector_name"
                label="板块名称"
                width="200"
              />
              <el-table-column
                prop="category"
                label="板块类别"
                width="150"
              />
              <el-table-column
                prop="created_at"
                label="创建时间"
                width="180"
              />
              <el-table-column
                prop="updated_at"
                label="更新时间"
                width="180"
              />
            </el-table>

            <!-- 分页 -->
            <el-pagination
              v-if="sectorTotal > 0"
              background
              layout="total, sizes, prev, pager, next, jumper"
              :current-page="sectorPage"
              :page-sizes="[10, 20, 50, 100]"
              :page-size="sectorPageSize"
              :total="sectorTotal"
              style="margin-top: 20px; text-align: right"
              @size-change="handleSectorSizeChange"
              @current-change="handleSectorPageChange"
            />
          </div>
        </el-tab-pane>

        <!-- 股票管理 Tab -->
        <el-tab-pane label="股票管理" name="stock">
          <div class="tab-content">
            <!-- 操作栏 -->
            <div class="operation-bar">
              <el-button
                type="primary"
                icon="el-icon-refresh"
                :loading="stockLoading"
                @click="handleUpdateStockInfo"
              >
                更新股票基本信息
              </el-button>
              <el-button
                type="info"
                icon="el-icon-search"
                @click="loadStocks"
              >
                刷新列表
              </el-button>
            </div>

            <!-- 股票列表 -->
            <el-table
              v-loading="stockTableLoading"
              :data="stockList"
              border
              stripe
              style="width: 100%; margin-top: 20px"
            >
              <el-table-column
                prop="合约代码"
                label="合约代码"
                width="100"
                fixed="left"
              />
              <el-table-column
                prop="市场代码"
                label="市场"
                width="80"
              />
              <el-table-column
                prop="合约名称"
                label="合约名称"
                width="120"
              />
              <el-table-column
                prop="拼音简写"
                label="拼音简写"
                width="100"
              />
              <el-table-column
                prop="IPO日期"
                label="IPO日期"
                width="100"
              />
              <el-table-column
                prop="总股本"
                label="总股本"
                width="120"
                :formatter="formatNumber"
              />
              <el-table-column
                prop="流通股本"
                label="流通股本"
                width="120"
                :formatter="formatNumber"
              />
              <el-table-column
                prop="前收盘价"
                label="前收盘价"
                width="100"
              />
              <el-table-column
                prop="涨停价"
                label="涨停价"
                width="100"
              />
              <el-table-column
                prop="跌停价"
                label="跌停价"
                width="100"
              />
              <el-table-column
                prop="是否可交易"
                label="可交易"
                width="80"
              >
                <template slot-scope="scope">
                  <el-tag :type="scope.row.是否可交易 ? 'success' : 'danger'" size="small">
                    {{ scope.row.是否可交易 ? '是' : '否' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column
                prop="证券分类"
                label="证券分类"
                width="100"
              />
              <el-table-column
                prop="港股通标识"
                label="港股通"
                width="80"
              >
                <template slot-scope="scope">
                  <el-tag v-if="scope.row.港股通标识" type="success" size="small">
                    是
                  </el-tag>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column
                prop="创建时间"
                label="创建时间"
                width="160"
              />
              <el-table-column
                prop="更新时间"
                label="更新时间"
                width="160"
              />
            </el-table>

            <!-- 分页 -->
            <el-pagination
              v-if="stockTotal > 0"
              background
              layout="total, sizes, prev, pager, next, jumper"
              :current-page="stockPage"
              :page-sizes="[10, 20, 50, 100]"
              :page-size="stockPageSize"
              :total="stockTotal"
              style="margin-top: 20px; text-align: right"
              @size-change="handleStockSizeChange"
              @current-change="handleStockPageChange"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script>
import {
  updateSectors,
  updateSectorStocks,
  updateStockInfo,
  getSectors,
  getStocks
} from '@/api/data_management'

export default {
  name: 'DataManagement',
  data() {
    return {
      activeTab: 'sector',
      
      // 板块相关
      sectorLoading: false,
      sectorStocksLoading: false,
      sectorTableLoading: false,
      sectorList: [],
      sectorPage: 1,
      sectorPageSize: 20,
      sectorTotal: 0,
      
      // 股票相关
      stockLoading: false,
      stockTableLoading: false,
      stockList: [],
      stockPage: 1,
      stockPageSize: 20,
      stockTotal: 0
    }
  },
  mounted() {
    this.loadSectors()
  },
  methods: {
    // ========== 板块操作 ==========
    async handleUpdateSectors() {
      this.$confirm('此操作将从 xtquant 获取最新板块数据并保存到数据库, 是否继续?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async() => {
        this.sectorLoading = true
        try {
          const res = await updateSectors()
          if (res.code === 0) {
            const data = res.data
            this.$message({
              type: 'success',
              message: `更新成功! 新增: ${data.added}, 更新: ${data.updated}, 总数: ${data.total}`
            })
            this.loadSectors()
          } else {
            this.$message.error(res.msg || '更新失败')
          }
        } catch (error) {
          this.$message.error(error.message || '更新失败')
        } finally {
          this.sectorLoading = false
        }
      }).catch(() => {
        this.$message.info('已取消更新')
      })
    },
    
    async handleUpdateSectorStocks() {
      this.$confirm('此操作将更新所有板块的成分股, 可能需要较长时间, 是否继续?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async() => {
        this.sectorStocksLoading = true
        try {
          const res = await updateSectorStocks()
          if (res.code === 0) {
            const data = res.data
            this.$message({
              type: 'success',
              message: `更新成功! 新增: ${data.added}, 删除: ${data.removed}, 板块数: ${data.sectors_updated}`
            })
          } else {
            this.$message.error(res.msg || '更新失败')
          }
        } catch (error) {
          this.$message.error(error.message || '更新失败')
        } finally {
          this.sectorStocksLoading = false
        }
      }).catch(() => {
        this.$message.info('已取消更新')
      })
    },
    
    async loadSectors() {
      this.sectorTableLoading = true
      try {
        const res = await getSectors({
          page: this.sectorPage,
          page_size: this.sectorPageSize
        })
        if (res.code === 0 && res.data) {
          this.sectorList = res.data.data || []
          this.sectorTotal = res.data.total || 0
        }
      } catch (error) {
        console.error('加载板块列表失败:', error)
        this.$message.error('加载板块列表失败')
      } finally {
        this.sectorTableLoading = false
      }
    },
    
    handleSectorSizeChange(val) {
      this.sectorPageSize = val
      this.loadSectors()
    },
    
    handleSectorPageChange(val) {
      this.sectorPage = val
      this.loadSectors()
    },
    
    // ========== 股票操作 ==========
    async handleUpdateStockInfo() {
      this.$confirm('此操作将更新所有板块成分股的基本信息, 可能需要较长时间, 是否继续?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async() => {
        this.stockLoading = true
        try {
          const res = await updateStockInfo()
          if (res.code === 0) {
            const data = res.data
            this.$message({
              type: 'success',
              message: `更新成功! 新增: ${data.added}, 更新: ${data.updated}, 失败: ${data.failed}, 总数: ${data.total}`
            })
            this.loadStocks()
          } else {
            this.$message.error(res.msg || '更新失败')
          }
        } catch (error) {
          this.$message.error(error.message || '更新失败')
        } finally {
          this.stockLoading = false
        }
      }).catch(() => {
        this.$message.info('已取消更新')
      })
    },
    
    async loadStocks() {
      this.stockTableLoading = true
      try {
        const res = await getStocks({
          page: this.stockPage,
          page_size: this.stockPageSize
        })
        if (res.code === 0 && res.data) {
          this.stockList = res.data.data || []
          this.stockTotal = res.data.total || 0
        }
      } catch (error) {
        console.error('加载股票列表失败:', error)
        this.$message.error('加载股票列表失败')
      } finally {
        this.stockTableLoading = false
      }
    },
    
    handleStockSizeChange(val) {
      this.stockPageSize = val
      this.loadStocks()
    },
    
    handleStockPageChange(val) {
      this.stockPage = val
      this.loadStocks()
    },
    
    // 格式化数字
    formatNumber(row, column, cellValue) {
      if (cellValue === null || cellValue === undefined) {
        return '-'
      }
      return cellValue.toLocaleString()
    }
  },
  watch: {
    activeTab(newVal) {
      if (newVal === 'sector') {
        this.loadSectors()
      } else if (newVal === 'stock') {
        this.loadStocks()
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.data-management-container {
  padding: 20px;

  .box-card {
    .card-title {
      font-size: 18px;
      font-weight: bold;
      color: #303133;
    }

    .card-subtitle {
      margin-left: 15px;
      font-size: 14px;
      color: #909399;
    }
  }

  .tab-content {
    padding: 20px;

    .operation-bar {
      display: flex;
      gap: 10px;
      margin-bottom: 20px;
    }
  }
}
</style>

