# Owner设计

唯一writer=pennix-skills，branch=main。范围：collection/tmux失败回滚、unsupported host全部写入口、CCH readiness、auth只读probe、native init root指引、真实源catalog物化。

目标files为skills/pennix-workflow-lifecycle/scripts/lifecycle.py及adapters/{skills_install,tmux_static,configuration,codex_static}.py、对应tests、project-root操作指引、catalog。collection晚receipt失败退新tree到staging再还旧tree/receipt；tmux失败补偿原target/receipt；所有write共用host gate；CCH按renderer schema；auth只查size/readability；init明确cwd。Grok/Windsurf先源修后按真实commit物化，不改快照作为源码权威。

共同根因补证后确认，同组仍逐条验收。主会话唯一writer/checker。不复制Trellis schema/队列/任务协议。本owner基础提交为ad686fdd，失败只回退本次scoped修改，用户落点按native owner旧版本恢复，保留历史与无关内容。

