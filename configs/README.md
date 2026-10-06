# 配置与验收范围 · v2.3.1

capabilities.json 是原辅助场景目录；新版写作原子能力的版本目录在 capabilities/registry.json，二者职责不同。acceptance.json 保留 v2.0 私人迁移检查，acceptance-v2.1.json 保留 A01–A13；acceptance-v2.2.json 保留历史 B01–B10。acceptance-v2.3.json 定义本版 C01–C10：公共 C01–C07，完整 C08–C10 另含实际私有迁移、云端来源读取证据核对、私有远端和克隆证据。

这些配置没有加入全局 workspace 定位。新版 Skill 和文档显式传 --workspace，旧 CLI 默认相对当前终端目录保持兼容。语料和服务配置示例只说明格式，不含账号凭据，也不自动创建连接。

报告是否通过以实际执行结果为准。沿用历史腾讯文档回执须说明时间和范围，微信公众号真实账号与操作仍排除在本版验收之外。

[原子方法](../capabilities/README.md) · [验收](../docs/testing.md) · [外部扩展](../docs/external-services/adding-service.md)

v2.3.1 沿用 C01–C10 范围，配置版本与 VERSION 一致；报告分别写入 acceptance-v2.3.1 和 work/acceptance-public-v2.3.1，不覆盖旧报告。更名补丁复核 v2.3.0 保存的腾讯读取与历史写入证据，不称为重新实测。
