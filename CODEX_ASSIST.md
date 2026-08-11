# Codex 协作记录

日期: 2026-08-11  
范围: 离线分析工具与研究结论校验；未连接设备、未发送 BLE/HID 命令、未改 APK/反编译产物。

## 我接手时看到的进度

Claude Code 已完成设备 USB/GATT 识别、主要命令表、实时 Opus 帧格式、鉴权链与
SDK/JNI 架构分析。`FINDINGS.md` 同时明确记录了一个工具缺口：507 字节续片会被
误判成随机命令。

## 我补的工作

1. `tools/protocol_analyze.py`
   - 将 A1 头部修正为 `type(1) + cmd_be16(2) + seq(1) + len_be32(4)`。
   - 在 HCI/L2CAP 重组之后增加 A1 应用层重组，按 32 位长度合并跨 ATT 续片。
   - L2CAP 状态改为按 `(connection, direction)` 隔离，避免双向交错覆盖。
   - 输出完整 16 位命令 ID、重组统计及孤立/未完成片段计数。

2. `tools/test_protocol_reassembly.py`
   - 新增 5 个纯离线回归测试：普通消息、507 字节续片、双 handle 交错、同 ATT
     多消息、孤立续片恢复。

3. `tools/compare_enc.py`
   - 增加完整 payload SHA-256 指纹比较。
   - 高熵只标注为“压缩音频/密文均可能”，避免把 Opus 高熵直接等同于 AES。
   - 检测到两份 bugreport 的三条 `0x0115` 文件数据逐字节相同后给出明确警告。

4. `FINDINGS.md`
   - 标记续片重组缺口已修复。
   - 收紧加密结论：`0x0117` 实时流可确认仍为明文 Opus；`0x0115` 文件下载
     因样本来自累计 btsnoop，仍待独立实验确认。

## 验证痕迹

修复前，`bugreport3_enc.zip` 被解析为 2941 个“报文”，出现大量随机伪命令，
长度字段 146 条不吻合。

修复后同一真实抓包：

- 2942 个 ATT 片段 -> 2804 条完整 A1 消息；
- 长度字段 2804/2804 全部吻合；
- `0x0115` 正确还原为 3 条消息，payload 分别为 14124、14972、41944 字节；
- 大量 `0x0022`、`0x00D5`、`0x0060` 等随机伪命令消失；
- `python -m unittest tools\\test_protocol_reassembly.py -v`: 5/5 通过；
- `audio_check.py` 与 `compare_enc.py` 均在真实抓包上运行成功。

两轮 `0x0115` 指纹（前 16 hex）完全相同：

- 14124 B: `16189b7beba4ea2e`
- 14972 B: `57df86243c721aad`
- 41944 B: `dc12e813224ce306`

## 推荐下一步

开启 App 加密后新建一条能通过 fid 唯一识别的录音，清空或截断旧 btsnoop，单独
下载这条新文件，再运行 `compare_enc.py`。在取得这组独立样本前，不应把
“文件下载始终明文”写进第三方客户端的设计假设。
