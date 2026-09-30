# v2.0 入口元数据

[openai.yaml](openai.yaml) 描述根 Skill 的显示名称、简介和默认提示。两个主 Skill 各自的 agents/openai.yaml 位于 `.agents/skills/<名称>/`。

interface 用于入口展示，真正的任务边界由对应 SKILL.md 与项目指令约定。根文件中的 integration 是本项目保留的描述性元数据，指向上下文构建器和集成说明；它不会注册在线服务或自动执行连接。

修改名称和描述时与[能力清单](../configs/capabilities.json)保持一致，不把某一本书设置成所有用户的默认内容任务。
