# VASP Skills

VASP Skills 是一个面向 Agent 的 VASP 计算技能包，用于自动化完成以下流程：

- 生成输入文件（INCAR/POSCAR/KPOINTS/POTCAR）
- 执行与串联多步计算工作流
- 校验输入并进行常见报错诊断
- 解析输出并导出/可视化结果

---

## 1) 适用场景

- 材料计算自动化（DFT 高通量任务）
- LLM Agent 需要“可调用、可验证、可恢复”的 VASP 工具能力
- 需要将 VASP 任务封装成标准化技能组件

---

## 2) Agent Skill 元数据

本仓库提供技能元数据文件：

- `agent_skill.yaml`：技能声明、能力列表、输入输出契约、失败策略

Agent 可据此做：

- 能力发现（capability discovery）
- 参数校验（argument validation）
- 结果解释（result interpretation）
- 错误恢复（error recovery）

---

## 3) 安装

### 生产安装

```bash
pip install -e .
```

### 开发安装

```bash
pip install -e .[dev]
```

---

## 4) 快速开始

### 4.1 生成计算输入

```bash
vasp-skills generate relax -p POSCAR -d relax_job
```

### 4.2 校验输入

```bash
vasp-skills validate -d relax_job
```

### 4.3 检查错误

```bash
vasp-skills check -d relax_job
```

### 4.4 解析结果

```bash
vasp-skills parse energy -d relax_job
vasp-skills parse forces -d relax_job
vasp-skills parse gap -d relax_job
```

### 4.5 运行工作流

```bash
vasp-skills workflow bandstructure -p POSCAR -d band_workflow --write-only
```

---

## 5) 输入/输出契约（Skill Contract）

### 输入约束

- 结构输入默认来自 POSCAR（也支持部分场景从 CIF 转换）
- 目录中至少应包含：`POSCAR`（生成时）
- 校验阶段要求：`INCAR/POSCAR/KPOINTS/POTCAR`

### 输出约束

- 生成类命令输出 VASP 输入文件
- 解析类命令输出结构化物理量（能量、力、带隙等）
- 导出类命令输出 CSV/JSON

### 失败语义

- 参数错误：命令行直接失败并返回非零退出码
- 输入文件缺失：校验模块返回 error 列表
- 常见 VASP 报错：ErrorHandler 给出可执行修复建议

---

## 6) 质量保障

- `tests/` 提供基础单元测试
- `.github/workflows/ci.yml` 提供最小 CI（安装 + 测试）
- `pyproject.toml` 提供统一构建与测试配置入口

运行测试：

```bash
pytest -q
```

---

## 7) 目录结构

```text
vasp_skills/
	calculation/   # 各类 VASP 计算模板与执行逻辑
	core/          # INCAR/POSCAR/KPOINTS/POTCAR 基础能力
	workflow/      # 多步工作流、校验、错误处理
	postprocess/   # 解析、导出、绘图
```

---

## 8) 注意事项

- 本项目不包含 VASP 本体；需用户已具备 VASP 可执行环境与授权。
- 默认 POTCAR 路径与运行命令可在 `config.yaml` 中配置。
- HPC 环境建议根据集群策略修改 `vasp_cmd` 与并行参数。
