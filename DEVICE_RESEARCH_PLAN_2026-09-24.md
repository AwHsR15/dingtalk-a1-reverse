# A1 按键测试、固件接口与能力边界

## 证据范围

官方Android 8.5.8.3与日版A1的历史测试。结果按命令、主动事件、状态、异常恢复和持久性分别判定，不将客户端接口清单视为固件完整实现。

## 真机证据：1001

官方客户端下发 `0x0100`、`aikey_option=1001`，12:01:01 UTC 收到 code=200。

第一次长按测试右侧语音键后：

- 12:02:23.582 UTC，设备主动发送 type=0x13、cmd=0x0100、seq=123，`{fid,action:"start"}`。
- 官方 App 回 type=0x31、同 cmd/seq、`{code:200}`。
- 0x0116 声明 `stream_type=3,fsync=true,aes=0,alg_mode=0,incognitomode=0,sid=0`；音频属性为 `audio@opus@16000@84@1@16@32000@4`。
- 松手后音频持续传输，首份快照中有 2937 个 0x0117 帧，跨度约 58.7 秒。
- 第二次长按测试后，12:03:49.239 UTC，设备主动发送 type=0x13、cmd=0x0100、seq=58，`{action:"stop"}`，官方回复同序号 ACK。
- 紧随其后的 0x0132 应答为 idle；0x0110 文件列表的两次返回均包含此次录音 fid，证明卡内生成了列表项。尚未下载该项做文件完整性与可播放验证。
- 12:06:16 UTC 已将设置恢复为 1000，并收到 code=200。

原始证据在被忽略的 `capture/official_mode1001_start.log`、`official_mode1001_stop.log` 和 `official_mode_restored_protocol.log`。

**更正：不能把“主动录音事件只使用 seq=0/type=0x31”当通则。** 旧快照中确有该形式，本次官方客户端出现的是 type=0x13、非零序号、需要确认的形式。此前客户端和初始化设置也不同；需要同官方客户端的 1000 对照，才能把协议差异归因于按键模式。1001 的两次长按切换开始/停止已有实测。

## 固件获取路径已定位

官方 8.5.8.3 静态代码：

1. `DingerInterfaceImpl.java:4304` 读取 H5 的 `deviceId` 和 `firmwareVersion`。
2. `defpackage/o98.java:149` 构造 `QueryDeviceUpgradeVersionRequestModel`：`requestId/accountType/accountId/deviceId/currentFirmwareVersion`。
3. `queryDeviceUpgradeVersion` 返回版本信息；这一步不等于取得包地址。
4. `defpackage/ga8.java:513` 调用 `createUpgradeVersionTask`：`accountType/accountId/requestId/deviceId/forceUpgrade/upgradeVersion`。
5. `OTAUpgradeManage.java:528` 的成功回调读取 `UpgradeVersionTaskDTO.packageDownloadUrl`，更新任务状态并继续下载。
6. `OTAUpgradeManage.java:593` 将文件下载为 `<version>.zip`，目录来自 `syg.c().a()`。
7. `syg.java:41` 表明目录为 App 私有 `files/DingerRecord`；本次只读检查没有残留 ZIP。
8. `OTAUpgradeManage.java:853` 将 `attrs:"ota@bin"/cur_version/new_version/offset/verify_code/filePath/mtu` 交给 `DingerAudioTools.StartOta`；Wi-Fi 路径额外带 `net/ip/port`。`verify_code` 的算法尚未核实。

因此，应研究运行时修改**上报的卡片固件版本**，无需先重打包 APK 或修改 APK 的 versionName。仅修改显示字符串未必改变服务器请求；仅修改 APK 版本不等于修改卡片版本。

以上仅定位到客户端查询和下载链路；没有取得固件镜像，也未执行版本替换、创建升级任务或发送OTA。

## 当前能做、待验证与受限项

| 项目 | 现有条件下的获取方法 | 限制或验收缺口 |
|---|---|---|
| 官方命令/参数完整清单 | APK Java、JNI 导出、原生反汇编、官方动作抓包交叉核对 | 参数边界、错误码、隐藏分支未全部实测 |
| 两个按键与录音状态机 | 单动作对照，固定模式/客户端/同步状态 | 左键、短按、掉线/离线、断电持久化还不完整 |
| 0x000C 设备日志 | 新 SDK 保留 DingerUtReport 各 Parse*Event 导出，可反汇编提取事件分类和枚举 | 尚未将全部分类与抓包字段对应 |
| 卡片定时任务 | 已知 0x011A 格式；分析能力等级与固件实现，再做短任务执行/取消/断线对照 | 当前 cap_schedule=1，官方门槛>=2；这只证明 UI 有门槛，不能证明协议绝对不支持 |
| 固件镜像 | OTA 查询与包地址路径、缓存、官方同型号包 | 当前没有镜像；服务端策略、整包/差分包、加密均未知 |
| USB 与调试入口 | 继续解析 USB 描述符与只读端点，找官方工具或固件中的协议实现 | NuttX Composite/HID 已见，卡片 ADB offline；平板 root 不等于卡片 root |
| 固件任意修改/刷入 | 先获得镜像、分区、备份恢复机制，再研究校验/启动流程 | Secure Boot、签名校验、读保护、UART/JTAG 可用性未知，当前无法承诺 |
| 官方云端全部内部规则 | 自己账号的调用/响应和客户端逻辑 | 不能从 APK 还原服务端源码、灰度数据库或所有区域策略 |

## 穷举策略

可以对已确认只读的命令、从代码提取的候选参数和返回格式做受控枚举：限速、逐次记录、错误即停、比较前后状态。对可逆设置还必须回读并验证实际行为与恢复。

不直接扫描全部 16 位命令号，也不把某个 key 的所有整数挨个写入。已知 0x0004 与解绑/复位相关、0x0113 删除文件；未知命令可能有类似副作用。code=200 也不足以证明某个新数值有独立功能。
