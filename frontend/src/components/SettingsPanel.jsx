import React, { useState, useEffect } from 'react'
import { API_BASE } from '../utils/api';
import { Settings, MessageCircle, CheckCircle, AlertCircle, RefreshCw, HelpCircle, ExternalLink } from 'lucide-react'

export default function SettingsPanel() {
  const [webhookUrl, setWebhookUrl] = useState('')
  const [mention, setMention] = useState('')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)
  const [showHelp, setShowHelp] = useState(false)

  useEffect(() => {
    fetchConfig()
  }, [])

  const fetchConfig = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/wechat/config`)
      const data = await res.json()
      setWebhookUrl(data.webhook_url || '')
      setMention(data.mention || '')
    } catch (e) {
      console.error(e)
    }
  }

  const saveConfig = async () => {
    setSaving(true)
    setMessage(null)
    try {
      const formData = new FormData()
      formData.append('webhook_url', webhookUrl)
      formData.append('mention', mention)
      
      const res = await fetch(`${API_BASE}/api/wechat/config`, {
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      setMessage({ type: 'success', text: '保存成功' })
    } catch (e) {
      setMessage({ type: 'error', text: e.message })
    }
    setSaving(false)
  }

  const testWebhook = async () => {
    setMessage(null)
    try {
      const formData = new FormData()
      formData.append('content', '### 🎯 乐友量化系统\n\n测试消息发送成功！')
      
      const res = await fetch(`${API_BASE}/api/wechat/send`, {
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      if (data.status === 'ok') {
        setMessage({ type: 'success', text: '测试消息发送成功' })
      } else {
        setMessage({ type: 'error', text: data.message })
      }
    } catch (e) {
      setMessage({ type: 'error', text: e.message })
    }
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
              <MessageCircle className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <h2 className="text-lg font-bold">微信通知设置</h2>
              <p className="text-sm text-gray-400">配置企业微信机器人 webhook</p>
            </div>
          </div>
          <button
            onClick={() => setShowHelp(!showHelp)}
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-400 hover:text-white transition"
          >
            <HelpCircle className="w-4 h-4" />
            如何获取？
          </button>
        </div>

        {/* 帮助说明 */}
        {showHelp && (
          <div className="mb-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
            <h3 className="font-medium text-blue-400 mb-3 flex items-center gap-2">
              <HelpCircle className="w-4 h-4" />
              获取企业微信机器人 Webhook 地址
            </h3>
            
            <div className="space-y-4 text-sm">
              <div className="flex gap-3">
                <div className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold shrink-0">1</div>
                <div>
                  <p className="text-gray-300">打开企业微信群聊</p>
                  <p className="text-gray-500 mt-1">在手机或电脑上打开企业微信，进入你想要接收通知的群聊</p>
                </div>
              </div>
              
              <div className="flex gap-3">
                <div className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold shrink-0">2</div>
                <div>
                  <p className="text-gray-300">点击群设置 → 群机器人</p>
                  <p className="text-gray-500 mt-1">点击右上角「···」→ 选择「群机器人」</p>
                </div>
              </div>
              
              <div className="flex gap-3">
                <div className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold shrink-0">3</div>
                <div>
                  <p className="text-gray-300">添加机器人</p>
                  <p className="text-gray-500 mt-1">点击「添加机器人」→ 输入机器人名称（如：乐友量化）</p>
                </div>
              </div>
              
              <div className="flex gap-3">
                <div className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold shrink-0">4</div>
                <div>
                  <p className="text-gray-300">复制 Webhook 地址</p>
                  <p className="text-gray-500 mt-1">添加成功后，点击「复制」获取 Webhook 地址</p>
                </div>
              </div>
              
              <div className="mt-4 p-3 bg-dark-200 rounded-lg">
                <p className="text-gray-400 mb-2">示例格式：</p>
                <code className="text-xs text-green-400 break-all">
                  https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
                </code>
              </div>
              
              <div className="flex items-start gap-2 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                <AlertCircle className="w-4 h-4 text-yellow-400 shrink-0 mt-0.5" />
                <p className="text-yellow-200 text-xs">
                  注意：Webhook 地址包含密钥，请勿泄露给他人。如果泄露，请在群机器人设置中重新生成。
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              Webhook URL
              <span className="text-red-400 ml-1">*</span>
            </label>
            <input
              type="text"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..."
              className="w-full px-4 py-3 bg-dark-200 rounded-lg border border-gray-700 focus:border-primary focus:outline-none text-gray-200 text-sm"
            />
            <p className="text-xs text-gray-500 mt-2">
              在企业微信群中添加机器人，复制 webhook 地址粘贴到此处
            </p>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">@ 提醒人 (可选)</label>
            <input
              type="text"
              value={mention}
              onChange={(e) => setMention(e.target.value)}
              placeholder="填写手机号或用户ID"
              className="w-full px-4 py-3 bg-dark-200 rounded-lg border border-gray-700 focus:border-primary focus:outline-none text-gray-200 text-sm"
            />
            <p className="text-xs text-gray-500 mt-2">
              推送消息时会 @ 此人，填写企业微信绑定的手机号
            </p>
          </div>

          {message && (
            <div className={`flex items-center gap-2 p-3 rounded-lg ${
              message.type === 'success' ? 'bg-green-400/10 text-green-400' : 'bg-red-400/10 text-red-400'
            }`}>
              {message.type === 'success' ? <CheckCircle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
              {message.text}
            </div>
          )}

          <div className="flex gap-3">
            <button
              onClick={saveConfig}
              disabled={saving || !webhookUrl}
              className="flex-1 px-4 py-3 bg-primary text-dark-300 font-medium rounded-lg hover:bg-primary/90 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? '保存中...' : '保存配置'}
            </button>
            <button
              onClick={testWebhook}
              disabled={!webhookUrl}
              className="px-4 py-3 bg-dark-200 border border-gray-700 rounded-lg hover:bg-dark-300 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              测试发送
            </button>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
            <Settings className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h2 className="text-lg font-bold">系统信息</h2>
            <p className="text-sm text-gray-400">乐友量化投资系统 v1.0</p>
          </div>
        </div>

        <div className="space-y-3 text-sm">
          <div className="flex justify-between py-2 border-b border-gray-800">
            <span className="text-gray-400">版本</span>
            <span>v1.0.0</span>
          </div>
          <div className="flex justify-between py-2 border-b border-gray-800">
            <span className="text-gray-400">后端</span>
            <span>FastAPI</span>
          </div>
          <div className="flex justify-between py-2 border-b border-gray-800">
            <span className="text-gray-400">前端</span>
            <span>React + Vite + Tailwind</span>
          </div>
          <div className="flex justify-between py-2">
            <span className="text-gray-400">评分模型</span>
            <span>7因子多因子量化模型</span>
          </div>
        </div>
      </div>

      <div className="card border-yellow-400/30">
        <h3 className="font-medium mb-3">⚠️ 风险提示</h3>
        <ul className="text-sm text-gray-400 space-y-2">
          <li>• 所有交易信号仅供参考，不构成投资建议</li>
          <li>• 投资有风险，入市需谨慎</li>
          <li>• 请根据自身风险承受能力做出投资决策</li>
          <li>• 建议保留至少 10% 的现金储备</li>
        </ul>
      </div>

      {/* 版权声明 */}
      <div className="text-center text-xs text-gray-600 mt-6 pb-4">
        <p>© 2025 杭州市上城区乐友信息服务工作室</p>
        <p className="mt-1">版权所有 · 未经授权不得复制或分发</p>
      </div>
    </div>
  )
}
