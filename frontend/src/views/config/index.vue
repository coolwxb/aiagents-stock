<template>
  <div class="config-page app-container">
    <el-card shadow="hover">
      <div slot="header" class="card-header">
        <div>
          <h2>⚙️ 环境配置管理</h2>
          <p class="subtitle">
            按照 Streamlit 版本的配置体验，管理 AI、数据源、量化交易及通知相关的环境变量
          </p>
        </div>
        <div class="header-actions">
          <el-button size="mini" icon="el-icon-refresh" :loading="loading" @click="loadConfig">重新加载</el-button>
        </div>
      </div>

      <el-alert
        title="保存配置后需要重新部署/重启后端服务才会生效。"
        type="info"
        show-icon
        :closable="false"
      />

      <div class="config-content">
        <el-skeleton v-if="loading" :rows="6" animated />
        <template v-else>
          <el-tabs v-model="activeTab">
            <el-tab-pane label="基础配置" name="basic">
              <el-form :model="configForm.basic" label-width="180px" class="config-form">
                <el-form-item label="DeepSeek API Key" required>
                  <el-input
                    v-model="configForm.basic.deepseekApiKey"
                    type="password"
                    placeholder="请输入DeepSeek API Key"
                    show-password
                    autocomplete="off"
                  />
                </el-form-item>
                <el-form-item label="DeepSeek API 地址">
                  <el-input
                    v-model="configForm.basic.deepseekBaseUrl"
                    placeholder="https://api.deepseek.com/v1"
                  />
                </el-form-item>
              </el-form>
              <div class="hint-block">
                <p class="hint-title">DeepSeek 接入说明</p>
                <ul class="hint-list">
                  <li>默认地址 <code>https://api.deepseek.com/v1</code>，也可替换为硅基流动、火山引擎、阿里 DashScope 等兼容入口。</li>
                  <li>获取 API Key：访问 <a href="https://platform.deepseek.com" target="_blank" rel="noopener">DeepSeek 控制台</a> → 登录 → API Keys → 创建密钥。</li>
                  <li>修改 Key 或地址后需重启后端 / 重新部署服务才能完全生效。</li>
                </ul>
              </div>
            </el-tab-pane>

            <el-tab-pane label="数据源配置" name="data">
              <el-form :model="configForm.dataSource" label-width="200px" class="config-form">
                <el-divider content-position="left">Tushare 数据接口</el-divider>
                <el-form-item label="Tushare Token">
                  <el-input
                    v-model="configForm.dataSource.tushareToken"
                    type="password"
                    placeholder="可选：用于获取更多A股财务数据"
                    show-password
                  />
                </el-form-item>

                <el-divider content-position="left">MySQL 行情数据库</el-divider>
                <el-form-item label="启用 MySQL 数据源">
                  <el-switch v-model="configForm.dataSource.mysqlEnabled" />
                  <span class="form-tip">开启后将从自建 MySQL 库读取行情数据</span>
                </el-form-item>
                <el-form-item label="MySQL 地址">
                  <el-input
                    v-model="configForm.dataSource.mysqlHost"
                    :disabled="!configForm.dataSource.mysqlEnabled"
                    placeholder="127.0.0.1"
                  />
                </el-form-item>
                <el-form-item label="MySQL 端口">
                  <el-input
                    v-model="configForm.dataSource.mysqlPort"
                    :disabled="!configForm.dataSource.mysqlEnabled"
                    placeholder="3306"
                  />
                </el-form-item>
                <el-form-item label="用户名">
                  <el-input
                    v-model="configForm.dataSource.mysqlUser"
                    :disabled="!configForm.dataSource.mysqlEnabled"
                    placeholder="root"
                  />
                </el-form-item>
                <el-form-item label="密码">
                  <el-input
                    v-model="configForm.dataSource.mysqlPassword"
                    type="password"
                    show-password
                    :disabled="!configForm.dataSource.mysqlEnabled"
                  />
                </el-form-item>
                <el-form-item label="数据库名称">
                  <el-input
                    v-model="configForm.dataSource.mysqlDatabase"
                    :disabled="!configForm.dataSource.mysqlEnabled"
                    placeholder="choose_stock"
                  />
                </el-form-item>
                <el-form-item label="行情表名称">
                  <el-input
                    v-model="configForm.dataSource.mysqlStockTable"
                    :disabled="!configForm.dataSource.mysqlEnabled"
                    placeholder="stock_history"
                  />
                </el-form-item>
              </el-form>
              <div class="hint-block">
                <p class="hint-title">数据源配置说明</p>
                <ul class="hint-list">
                  <li>Tushare Token 可选，配置后可让后端获取更全面的 A 股财务与行业数据。</li>
                  <li>MySQL 数据源面向自建行情库，启用后需确保主机/端口/库表信息与实际数据库一致。</li>
                  <li>建议行情表包含股票代码、交易日期、开高低收和成交量等字段，方便分析与量化策略复用。</li>
                </ul>
              </div>
            </el-tab-pane>

            <el-tab-pane label="量化交易配置" name="trading">
              <el-form :model="configForm.trading" label-width="200px" class="config-form">
                <el-form-item label="启用 MiniQMT 量化交易">
                  <el-switch v-model="configForm.trading.miniqmtEnabled" />
                  <span class="form-tip">开启后可接入 MiniQMT，实现自动策略交易</span>
                </el-form-item>
                <el-form-item label="账户">
                  <el-input
                    v-model="configForm.trading.miniqmtAccountId"
                    :disabled="!configForm.trading.miniqmtEnabled"
                  />
                </el-form-item>
                <el-form-item label="账户类型">
                  <el-select
                    v-model="configForm.trading.miniqmtAccountType"
                    :disabled="!configForm.trading.miniqmtEnabled"
                    placeholder="请选择账户类型"
                  >
                    <el-option label="股票账户（STOCK）" value="STOCK" />
                    <el-option label="信用账户（CREDIT）" value="CREDIT" />
                  </el-select>
                </el-form-item>
                <el-form-item label="用户数据地址">
                  <el-input
                    v-model="configForm.trading.miniqmtUserdataPath"
                    :disabled="!configForm.trading.miniqmtEnabled"
                    placeholder="E:\\zhongjin_qmt\\userdata_mini"
                  />
                </el-form-item>
                <el-alert
                  title="量化交易涉及真实资金操作，请谨慎启用。"
                  type="warning"
                  show-icon
                  :closable="false"
                />
              </el-form>
              <div class="hint-block">
                <p class="hint-title">MiniQMT 使用提醒</p>
                <ul class="hint-list">
                  <li>确保 MiniQMT 客户端已启动，账户 ID、账户类型与客户端保持一致。</li>
                  <li>用户数据目录一般位于 MiniQMT 安装路径下的 <code>userdata_mini</code> 目录，请填写绝对路径。</li>
                  <li>量化交易会直接影响真实资金，建议在沙盒或小额账户中充分验证策略后再启用。</li>
                </ul>
              </div>
            </el-tab-pane>

            <el-tab-pane label="通知配置" name="notification">
              <el-form :model="configForm.notification" label-width="220px" class="config-form">
                <el-divider content-position="left">邮件通知</el-divider>
                <el-form-item label="启用邮件通知">
                  <el-switch v-model="configForm.notification.emailEnabled" />
                </el-form-item>
                <el-form-item label="SMTP 服务器">
                  <el-input
                    v-model="configForm.notification.smtpServer"
                    :disabled="!configForm.notification.emailEnabled"
                    placeholder="smtp.qq.com"
                  />
                </el-form-item>
                <el-form-item label="SMTP 端口">
                  <el-input
                    v-model="configForm.notification.smtpPort"
                    :disabled="!configForm.notification.emailEnabled"
                    placeholder="587 或 465"
                  />
                </el-form-item>
                <el-form-item label="发件人邮箱">
                  <el-input
                    v-model="configForm.notification.emailFrom"
                    :disabled="!configForm.notification.emailEnabled"
                    placeholder="your-email@qq.com"
                  />
                </el-form-item>
                <el-form-item label="邮箱授权码">
                  <el-input
                    v-model="configForm.notification.emailPassword"
                    type="password"
                    show-password
                    :disabled="!configForm.notification.emailEnabled"
                  />
                </el-form-item>
                <el-form-item label="收件人邮箱">
                  <el-input
                    v-model="configForm.notification.emailTo"
                    :disabled="!configForm.notification.emailEnabled"
                    placeholder="receiver@qq.com"
                  />
                </el-form-item>

                <el-divider content-position="left">Webhook 通知</el-divider>
                <el-form-item label="启用 Webhook">
                  <el-switch v-model="configForm.notification.webhookEnabled" />
                </el-form-item>
                <el-form-item label="Webhook 类型">
                  <el-select
                    v-model="configForm.notification.webhookType"
                    :disabled="!configForm.notification.webhookEnabled"
                    placeholder="请选择"
                  >
                    <el-option label="钉钉" value="dingtalk" />
                    <el-option label="飞书" value="feishu" />
                  </el-select>
                </el-form-item>
                <el-form-item label="Webhook 地址">
                  <el-input
                    v-model="configForm.notification.webhookUrl"
                    :disabled="!configForm.notification.webhookEnabled"
                    placeholder="https://oapi.dingtalk.com/robot/send?access_token=..."
                  />
                </el-form-item>
                <el-form-item label="关键词（钉钉）">
                  <el-input
                    v-model="configForm.notification.webhookKeyword"
                    :disabled="!configForm.notification.webhookEnabled || configForm.notification.webhookType !== 'dingtalk'"
                    placeholder="aiagents通知"
                  />
                </el-form-item>
              </el-form>
              <div class="hint-block">
                <p class="hint-title">通知配置说明</p>
                <ul class="hint-list">
                  <li>QQ 邮箱授权码：设置 → 账户 → POP3/IMAP/SMTP → 生成授权码。</li>
                  <li>钉钉：群设置 → 智能群助手 → 自定义机器人，复制 Webhook 并在安全设置配置关键词。</li>
                  <li>飞书：群设置 → 群机器人 → 自定义机器人，复制 Webhook 即可，无需关键词。</li>
                  <li>配置完成后建议在盯盘/智策定时模块中发送测试消息确认通知是否可达。</li>
                </ul>
              </div>
            </el-tab-pane>
          </el-tabs>

          <div class="config-actions">
            <el-button icon="el-icon-finished" :loading="validating" @click="handleValidate">校验配置</el-button>
            <el-button icon="el-icon-refresh-left" @click="handleReset">重置</el-button>
            <el-button type="primary" icon="el-icon-check" :loading="saving" @click="handleSave">保存配置</el-button>
          </div>

          <el-alert
            class="section-alert"
            title="操作说明"
            type="info"
            show-icon
            :closable="false"
            description="保存：写入后端 .env，需要重启后端或重新部署服务；重置：恢复为最近一次加载/保存的配置；校验：调用后端校验器检查必填项与格式。"
          />

          <el-divider />

          <div class="env-preview-card">
            <div class="preview-header">
              <h3>当前 .env 预览</h3>
              <span>保存后将写入到后端 .env 文件中</span>
            </div>
            <el-input
              type="textarea"
              :rows="12"
              :value="envPreview"
              readonly
              class="env-textarea"
            />
          </div>
        </template>
      </div>
    </el-card>
  </div>
</template>

<script>
import { getConfig, updateConfig, validateConfig } from '@/api/config'

const defaultFlatConfig = () => ({
  DEEPSEEK_API_KEY: '',
  DEEPSEEK_BASE_URL: 'https://api.deepseek.com/v1',
  TUSHARE_TOKEN: '',
  MYSQL_ENABLED: 'false',
  MYSQL_HOST: '127.0.0.1',
  MYSQL_PORT: '3306',
  MYSQL_USER: 'root',
  MYSQL_PASSWORD: '',
  MYSQL_DATABASE: 'choose_stock',
  MYSQL_STOCK_TABLE: 'stock_history',
  MINIQMT_ENABLED: 'false',
  MINIQMT_ACCOUNT_ID: '',
  MINIQMT_ACCOUNT_TYPE: 'STOCK',
  MINIQMT_USERDATA_PATH: 'E:\\zhongjin_qmt\\userdata_mini',
  EMAIL_ENABLED: 'false',
  SMTP_SERVER: '',
  SMTP_PORT: '587',
  EMAIL_FROM: '',
  EMAIL_PASSWORD: '',
  EMAIL_TO: '',
  WEBHOOK_ENABLED: 'false',
  WEBHOOK_TYPE: 'dingtalk',
  WEBHOOK_URL: '',
  WEBHOOK_KEYWORD: 'aiagents通知'
})

export default {
  name: 'ConfigIndex',
  data() {
    return {
      loading: false,
      saving: false,
      validating: false,
      activeTab: 'basic',
      configForm: this.createEmptyForm(),
      originalFlatConfig: {},
      envPreview: ''
    }
  },
  watch: {
    configForm: {
      handler() {
        this.updateEnvPreview()
      },
      deep: true
    }
  },
  created() {
    this.loadConfig()
  },
  methods: {
    createEmptyForm() {
      return {
        basic: {
          deepseekApiKey: '',
          deepseekBaseUrl: 'https://api.deepseek.com/v1'
        },
        dataSource: {
          tushareToken: '',
          mysqlEnabled: false,
          mysqlHost: '127.0.0.1',
          mysqlPort: '3306',
          mysqlUser: 'root',
          mysqlPassword: '',
          mysqlDatabase: 'choose_stock',
          mysqlStockTable: 'stock_history'
        },
        trading: {
          miniqmtEnabled: false,
          miniqmtAccountId: '',
          miniqmtAccountType: 'STOCK',
          miniqmtUserdataPath: 'E:\\zhongjin_qmt\\userdata_mini'
        },
        notification: {
          emailEnabled: false,
          smtpServer: '',
          smtpPort: '587',
          emailFrom: '',
          emailPassword: '',
          emailTo: '',
          webhookEnabled: false,
          webhookType: 'dingtalk',
          webhookUrl: '',
          webhookKeyword: 'aiagents通知'
        }
      }
    },
    async loadConfig() {
      this.loading = true
      try {
        const response = await getConfig()
        const merged = Object.assign(defaultFlatConfig(), response || {})
        this.originalFlatConfig = { ...merged }
        this.configForm = this.mapFlatToForm(merged)
      } catch (error) {
        console.warn('Failed to load config, fallback to defaults', error)
        const defaults = defaultFlatConfig()
        this.originalFlatConfig = { ...defaults }
        this.configForm = this.mapFlatToForm(defaults)
        this.$message.warning('未连接配置接口，已加载默认配置')
      } finally {
        this.loading = false
        this.updateEnvPreview()
      }
    },
    mapFlatToForm(flat) {
      return {
        basic: {
          deepseekApiKey: flat.DEEPSEEK_API_KEY || '',
          deepseekBaseUrl: flat.DEEPSEEK_BASE_URL || 'https://api.deepseek.com/v1'
        },
        dataSource: {
          tushareToken: flat.TUSHARE_TOKEN || '',
          mysqlEnabled: this.boolFromString(flat.MYSQL_ENABLED),
          mysqlHost: flat.MYSQL_HOST || '127.0.0.1',
          mysqlPort: flat.MYSQL_PORT || '3306',
          mysqlUser: flat.MYSQL_USER || 'root',
          mysqlPassword: flat.MYSQL_PASSWORD || '',
          mysqlDatabase: flat.MYSQL_DATABASE || 'choose_stock',
          mysqlStockTable: flat.MYSQL_STOCK_TABLE || 'stock_history'
        },
        trading: {
          miniqmtEnabled: this.boolFromString(flat.MINIQMT_ENABLED),
          miniqmtAccountId: flat.MINIQMT_ACCOUNT_ID || '',
          miniqmtAccountType: flat.MINIQMT_ACCOUNT_TYPE || 'STOCK',
          miniqmtUserdataPath: flat.MINIQMT_USERDATA_PATH || 'E:\\zhongjin_qmt\\userdata_mini'
        },
        notification: {
          emailEnabled: this.boolFromString(flat.EMAIL_ENABLED),
          smtpServer: flat.SMTP_SERVER || '',
          smtpPort: flat.SMTP_PORT || '587',
          emailFrom: flat.EMAIL_FROM || '',
          emailPassword: flat.EMAIL_PASSWORD || '',
          emailTo: flat.EMAIL_TO || '',
          webhookEnabled: this.boolFromString(flat.WEBHOOK_ENABLED),
          webhookType: flat.WEBHOOK_TYPE || 'dingtalk',
          webhookUrl: flat.WEBHOOK_URL || '',
          webhookKeyword: flat.WEBHOOK_KEYWORD || 'aiagents通知'
        }
      }
    },
    mapFormToFlat(form) {
      return {
        DEEPSEEK_API_KEY: form.basic.deepseekApiKey || '',
        DEEPSEEK_BASE_URL: form.basic.deepseekBaseUrl || 'https://api.deepseek.com/v1',
        TUSHARE_TOKEN: form.dataSource.tushareToken || '',
        MYSQL_ENABLED: this.boolToString(form.dataSource.mysqlEnabled),
        MYSQL_HOST: form.dataSource.mysqlHost || '127.0.0.1',
        MYSQL_PORT: form.dataSource.mysqlPort || '3306',
        MYSQL_USER: form.dataSource.mysqlUser || 'root',
        MYSQL_PASSWORD: form.dataSource.mysqlPassword || '',
        MYSQL_DATABASE: form.dataSource.mysqlDatabase || 'choose_stock',
        MYSQL_STOCK_TABLE: form.dataSource.mysqlStockTable || 'stock_history',
        MINIQMT_ENABLED: this.boolToString(form.trading.miniqmtEnabled),
        MINIQMT_ACCOUNT_ID: form.trading.miniqmtAccountId || '',
        MINIQMT_ACCOUNT_TYPE: form.trading.miniqmtAccountType || 'STOCK',
        MINIQMT_USERDATA_PATH: form.trading.miniqmtUserdataPath || 'E:\\zhongjin_qmt\\userdata_mini',
        EMAIL_ENABLED: this.boolToString(form.notification.emailEnabled),
        SMTP_SERVER: form.notification.smtpServer || '',
        SMTP_PORT: form.notification.smtpPort || '587',
        EMAIL_FROM: form.notification.emailFrom || '',
        EMAIL_PASSWORD: form.notification.emailPassword || '',
        EMAIL_TO: form.notification.emailTo || '',
        WEBHOOK_ENABLED: this.boolToString(form.notification.webhookEnabled),
        WEBHOOK_TYPE: form.notification.webhookType || 'dingtalk',
        WEBHOOK_URL: form.notification.webhookUrl || '',
        WEBHOOK_KEYWORD: form.notification.webhookKeyword || 'aiagents通知'
      }
    },
    boolFromString(value) {
      if (typeof value === 'boolean') return value
      return String(value).toLowerCase() === 'true'
    },
    boolToString(value) {
      return value ? 'true' : 'false'
    },
    async handleSave() {
      this.saving = true
      const payload = this.mapFormToFlat(this.configForm)
      try {
        await updateConfig(payload)
        this.originalFlatConfig = { ...payload }
        this.$message.success('配置保存成功')
      } catch (error) {
        console.error(error)
        this.$message.error('保存配置失败，请检查后端服务是否已实现')
      } finally {
        this.saving = false
      }
    },
    async handleValidate() {
      this.validating = true
      const payload = this.mapFormToFlat(this.configForm)
      try {
        const res = await validateConfig(payload)
        this.$message.success(res?.message || '配置验证通过')
      } catch (error) {
        this.$message.error(error?.message || '配置验证失败')
      } finally {
        this.validating = false
      }
    },
    handleReset() {
      this.configForm = this.mapFlatToForm({ ...this.originalFlatConfig })
      this.$message.success('已恢复为上次加载的配置')
    },
    updateEnvPreview() {
      const flat = this.mapFormToFlat(this.configForm)
      const lines = [
        '# AI股票分析系统环境配置',
        '# 该预览用于直观查看当前配置',
        '',
        '# ========== DeepSeek API配置 ==========',
        `DEEPSEEK_API_KEY="${flat.DEEPSEEK_API_KEY}"`,
        `DEEPSEEK_BASE_URL="${flat.DEEPSEEK_BASE_URL}"`,
        '',
        '# ========== Tushare数据接口（可选）==========',
        `TUSHARE_TOKEN="${flat.TUSHARE_TOKEN}"`,
        '',
        '# ========== MySQL行情数据库配置（可选）==========',
        `MYSQL_ENABLED="${flat.MYSQL_ENABLED}"`,
        `MYSQL_HOST="${flat.MYSQL_HOST}"`,
        `MYSQL_PORT="${flat.MYSQL_PORT}"`,
        `MYSQL_USER="${flat.MYSQL_USER}"`,
        `MYSQL_PASSWORD="${flat.MYSQL_PASSWORD}"`,
        `MYSQL_DATABASE="${flat.MYSQL_DATABASE}"`,
        `MYSQL_STOCK_TABLE="${flat.MYSQL_STOCK_TABLE}"`,
        '',
        '# ========== MiniQMT量化交易配置（可选）==========',
        `MINIQMT_ENABLED="${flat.MINIQMT_ENABLED}"`,
        `MINIQMT_ACCOUNT_ID="${flat.MINIQMT_ACCOUNT_ID}"`,
        `MINIQMT_ACCOUNT_TYPE="${flat.MINIQMT_ACCOUNT_TYPE}"`,
        `MINIQMT_USERDATA_PATH="${flat.MINIQMT_USERDATA_PATH}"`,
        '',
        '# ========== 邮件通知配置（可选）==========',
        `EMAIL_ENABLED="${flat.EMAIL_ENABLED}"`,
        `SMTP_SERVER="${flat.SMTP_SERVER}"`,
        `SMTP_PORT="${flat.SMTP_PORT}"`,
        `EMAIL_FROM="${flat.EMAIL_FROM}"`,
        `EMAIL_PASSWORD="${flat.EMAIL_PASSWORD}"`,
        `EMAIL_TO="${flat.EMAIL_TO}"`,
        '',
        '# ========== Webhook通知配置（可选）==========',
        `WEBHOOK_ENABLED="${flat.WEBHOOK_ENABLED}"`,
        `WEBHOOK_TYPE="${flat.WEBHOOK_TYPE}"`,
        `WEBHOOK_URL="${flat.WEBHOOK_URL}"`,
        `WEBHOOK_KEYWORD="${flat.WEBHOOK_KEYWORD}"`
      ]
      this.envPreview = lines.join('\n')
    }
  }
}
</script>

<style scoped>
.config-page .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.config-page .subtitle {
  margin: 4px 0 0;
  color: #909399;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.config-content {
  margin-top: 16px;
}

.config-form {
  max-width: 720px;
}

.config-actions {
  margin-top: 16px;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.env-preview-card {
  margin-top: 16px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 8px;
}

.env-textarea >>> textarea {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
  color: #606266;
}

.form-tip {
  margin-left: 12px;
  color: #909399;
  font-size: 12px;
}

.hint-block {
  margin-top: 12px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
  border-left: 3px solid #409EFF;
}

.hint-title {
  font-weight: 600;
  margin-bottom: 4px;
  color: #303133;
}

.hint-list {
  padding-left: 18px;
  margin: 0;
  color: #606266;
  line-height: 1.6;
}

.hint-list li {
  margin-bottom: 4px;
}

.section-alert {
  margin-top: 16px;
}
</style>
