# DingTalk / TALIX A1 录音卡开发工具与协议研究

让 A1 录音卡接入自己的客户端、语音服务和自动化工作流。

## 项目是什么

这是一个面向 **DingTalk A1 / TALIX & DingTalk A1** 的互操作研究与开发资料库，包含蓝牙协议、设备鉴权、音频和文件格式、官方后台模块、调用接口以及接入指南。

项目提供两类材料：可独立使用的协议分析工具，以及从官方 Android App 提取的设备/音频后台组件。开发者可以编写自己的界面和业务功能，复用后台处理，不必重写每个音频算法。**不包含官方前端，也不是已完成全部验收的成品客户端。**

当前主要研究版本为官方 Android **8.5.8.3**、日本销售版 A1。其他地区、型号和固件需分别验证。

## 能做什么

- **理解并实现 BLE 通信**：服务与特征、消息头、分片重组、命令和主动事件。
- **使用已有设备凭据离线鉴权**：不需要每次连接都查询官方账号服务；运行客户端的手机无需 root。
- **读取设备状态、文件列表并下载录音**：已有独立客户端历史实测记录。
- **研究和处理音频**：BABA/DTYJ 容器、加密标志、帧结构、实时流与多帧消息。
- **复用官方后台**：提供 ARM64 原生库、配套 JNI 接口及核心 JAR，用于文件同步、音频解码、转换、导出、合并和裁剪等。
- **接管音频的后续用途**：使用自己的 ASR、翻译、总结、保存或自动化逻辑。
- **查阅官方机制**：设备绑定、密钥查询、按键模式、定时任务、云文件与转写任务的调用关系。

## 不能做什么 / 当前限制

- **不能无凭据连接任意录音卡**。同一卡的凭据可迁移到不同手机；不同卡应分别取得凭据。
- **尚未解决完全离线的首次绑定，以及通用的无 root 首次取密钥**。已有凭据后的离线运行是另一回事。
- **不提供任意按键脚本**。右键已有1000/1001模式证据；未发现官方左键自定义接口。
- **尚未验证本研究设备的卡内离线定时**。官方能力门槛与历史设备报告值不一致。
- **不宣称完整支持 Wi-Fi 快传、固件提取/刷写或所有新音频通道**。
- **不附带官方云账号权限、付费转写权益或离线识别模型**。接口清单不能替代服务授权。
- **新版 SDK 尚未完成独立客户端全套实机验收**。提取、接口核对和编译成功不等于运行与断线恢复已全部通过。

## 可以用来做什么

- 开发自己的 Android 录音卡客户端和本地录音资料库。
- 将设备录音送入本地或自选的语音识别、翻译、纪要系统。
- 基于设备事件和音频结果实现备忘、语音助手或个人工作流。
- 分析自己的 BLE 抓包、定位分片/丢包问题、验证容器格式。
- 研究官方后台的输入输出和调用方式，减少重复实现。

## 大致方法与结果

采用 **APK 静态分析 → JNI/原生接口核对 → HCI 抓包交叉验证 → 独立客户端测试 → 离线回归** 的方式研究。不同证据层分别记录，不将静态代码存在视为实机功能已通过。

| 研究范围 | 主要结果 |
| --- | --- |
| 蓝牙协议 | FE3C服务、FE1C写、FE1B通知；8字节应用头与跨ATT重组 |
| 连接鉴权 | 0x0008随机挑战 → 本地AES应答 → 0x0133；历史实测鉴权和文件下载通过 |
| 官方后台 | 2个原生库、15个顶层Java文件、42个native入口；9个核心源可编译为JNI JAR |
| 音频可靠性 | 已识别单消息多帧；分析了SDK补包和文件处理路径，仍需新版接入验收 |
| 云业务契约 | 静态索引覆盖11个相关服务、90个非升级方法、185个关联模型 |
| 离线工具 | 21项合成测试通过，覆盖重组、容器和遥测解析 |

**主要结论：已有凭据后，设备通信和音频处理可以在本地进行；首次凭据取得与云账号授权仍需单独处理。官方后台核心可以被复用，但宿主必须正确提供蓝牙、目录、配置、凭据和回调。**

## 文档与下载

| 内容 | 入口 |
| --- | --- |
| 完整研究成果与证据边界 | [研究总览](docs/RESEARCH_SUMMARY.md) |
| root提取自己的凭据、无root手机使用 | [凭据获取指南](docs/CREDENTIALS_AND_ROOT.md) |
| 利用官方后台开发自己的软件 | [SDK接入指南](docs/SDK_INTEGRATION.md) |
| 已提取的官方后台文件 | [8.5.8.3 ARM64组件](vendor/dinger-sdk/8.5.8.3/) |
| 文件与模块的对应关系 | [模块映射](A1_BACKEND_MODULE_MAP_2026-09-25.md) · [接口索引](A1_BACKEND_INTERFACE_INDEX_2026-09-25.json) |
| 绑定、密钥与本地化 | [绑定机制](A1_BINDING_KEY_FLOW_2026-09-25.md) · [本地配对可行性](A1_LOCAL_ONLY_PAIRING_FEASIBILITY_2026-09-25.md) |
| 业务调用和云接口 | [综合研究](A1_REPLACEMENT_RESEARCH_SYNTHESIS_2026-09-25.md) · [云契约](CLOUD_CONTRACT_ROUTES_8.5.8.3_2026-09-25.md) |
| 详细协议和历史实验 | [协议笔记](FINDINGS.md) · [原生流程](NATIVE_CLIENT_FLOW_2026-09-24.md) |

旧研究记录中的阶段性结论以[当前总览](docs/RESEARCH_SUMMARY.md)和新版专题修订为准。证据索引中的本地文件引用用于复现定位，不表示原始私人样本随仓库公开。

## 使用离线工具

Python 3.11或更新版本，在仓库根目录运行：

```sh
python -m unittest discover -s tools -p "test_*.py" -v
```

鉴权计算工具额外需要 `pycryptodome`，输入格式见[示例](tools/verify_pairs.example.json)：

```sh
python -m pip install pycryptodome
python tools/verify_auth.py extract/verify_pairs.json
```

仅将自己的凭据和抓包保存在本地。原始录音、账号缓存、HCI/bugreport不随仓库发布。`native_event_names.py`还需要`pyelftools`和`unicorn`，用于离线原生事件枚举。

## 来源与许可证

原创研究说明和自写工具采用 [MIT](LICENSE)。`vendor/`中的官方/第三方提取件**不在该授权范围内**，来源、哈希和权利边界见 [NOTICE](NOTICE.md)。公开下载不代表这些组件获得了本项目的MIT授权。

相关项目：[Shawn-TKD/dingtalk-a1-pc-tools](https://github.com/Shawn-TKD/dingtalk-a1-pc-tools)。该项目基于本仓库的公开线索实现了PC工具，并提供包括跨卡鉴权失败在内的实测记录；引用时区分外部结果与本项目测试。

## English

Interoperability research and developer resources for DingTalk / TALIX A1 recorders: BLE framing and authentication, audio/file formats, official Android backend components, and integration guides.

Existing device credentials allow local authentication on another host without root. Fully offline first-time onboarding is not established. Extracted SDK components have static/compile verification, not complete runtime acceptance. Original tools and research are MIT; extracted third-party components are excluded from that license. No official frontend, real credentials, recordings or raw captures are included.
