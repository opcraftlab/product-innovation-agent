# GitHub发布

解压项目。GitHub仓库根目录应该直接包含 README.md、pyproject.toml、agents/、innovation_agent/ 等；不要只上传ZIP。

先运行：

```bash
python -m unittest discover -s tests -v
python scripts/check_release.py
```

创建一个空仓库后，将下面地址替换为实际地址，在项目根目录执行：

```bash
git init
git add README.md README.en.md AGENT.md LICENSE CHANGELOG.md CONTRIBUTING.md pyproject.toml .gitignore .github agents innovation_agent docs schemas examples tests scripts
git status --short
git commit -m "Release three product innovation task agents alpha"
git branch -M main
git remote add origin https://github.com/YOUR_ACCOUNT/YOUR_REPOSITORY.git
git push -u origin main
```

本项目已于2026-10-06发布至 [opcraftlab/product-innovation-agent](https://github.com/opcraftlab/product-innovation-agent)，通过网页创建仓库及授权连接批量提交。GitHub Actions 的 Python 3.10／3.12 检查均通过。上述命令供维护者发布自己的副本时参考。版本标记为 v0.2.0a1 prerelease；Release说明工具交付内容与实际测试范围；终端投入和市场结果由项目团队执行，不作为源码发布门槛。

一个仓库分别链接三个Agent，无需用户走完整流程。README推荐从方向验证开始。后续确有独立依赖或发布节奏时再拆仓库。

GitHub保存代码和协作记录，不会因为上传代码就提供托管推理服务；用户通过已有AI对话或自己的API环境运行。

实际业务输入、个人信息、商业秘密和API密钥由使用者保存在自己的工作区。即使有.gitignore，也在commit前核对 git status；只提交计划公开的文件。
