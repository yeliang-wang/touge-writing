# 配置与验收范围 · v2.4

capabilities.json 是原辅助场景目录；新版写作原子能力的版本目录在 capabilities/registry.json，二者职责不同。acceptance.json 保留 v2.0 私人迁移检查，acceptance-v2.1.json 保留 A01–A13；acceptance-v2.2.json 保留历史 B01–B10；acceptance-v2.3.json 保留 C01–C10 的原范围及版本。

这些配置没有加入全局 workspace 定位。新版 Skill 和文档显式传 --workspace，旧 CLI 默认相对当前终端目录保持兼容。语料和服务配置示例只说明格式，不含账号凭据，也不自动创建连接。

报告是否通过以实际执行结果为准。沿用历史腾讯文档回执须说明时间和范围，微信公众号真实账号与操作仍排除在本版验收之外。

[原子方法](../capabilities/README.md) · [验收](../docs/testing.md) · [外部扩展](../docs/external-services/adding-service.md)

v2.3.1 发行时沿用 C01–C10 范围，配置版本与当时 VERSION 一致；报告分别写入 acceptance-v2.3.1 和 work/acceptance-public-v2.3.1，不覆盖旧报告。更名补丁复核 v2.3.0 保存的腾讯读取与历史写入证据，不称为重新实测。

v2.4 使用独立 acceptance-v2.4.json 和 D01–D06 目标，包含规则行为、旧行为回归、独立 Skill 演练、私人规则依赖及发行证据。原 C01–C10 保留其历史身份，不能将旧通过结果直接改标为本次通过。
