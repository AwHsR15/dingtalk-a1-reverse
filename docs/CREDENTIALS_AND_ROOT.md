# 凭据获取、root与无root运行

## 三项配置是什么

| 设置 | 来源与作用 |
| --- | --- |
| deviceSecret / 设备密钥 | 官方DeviceModel中的设备凭据；用于本地挑战应答，不能用手机的蓝牙配对码替代 |
| corpId / 企业ID | 同一设备资料的组织/租户字段；个人账号也应读取实际值，不自行猜数字 |
| did / 登录设备ID | 官方AuthService.getDeviceId()返回的手机客户端标识；不是卡的deviceId、SN或MAC |

`x78.f(deviceId)`读取corpId，`x78.p(deviceId)`读取deviceSecret；`lj2.k()`加入AuthService的did。独立客户端拿到凭据后无需root即可计算token。root用于读取官方App的私有缓存，不是蓝牙运行条件。

## 1. 在自己的root Android设备上取得缓存

准备：安装并登录官方App，打开自己账号的A1页面使设备列表加载。无需为了导出再次解绑或恢复出厂。以下国际版包名为`com.alibaba.dingtalk.global`；其他版本先用`adb shell pm list packages`确认，不照搬包名。

确认ADB和root，`SERIAL`替换为自己的设备序列号：

```powershell
adb devices -l
adb -s SERIAL shell su -c id
adb -s SERIAL shell "su -c 'find /data/user/0/com.alibaba.dingtalk.global/shared_prefs -name PreferenceUtils.xml'"
```

`uid=0`才表明su成功。有些工程系统支持`adb root`，普通量产系统通常不支持；不要把`run-as`当作读取非debug官方App的通用方案。ADB用法见[Android官方文档](https://developer.android.com/tools/adb)。

将确认存在的那个文件保存到本仓库被忽略的`extract/`目录。用Python二进制写出，避免旧PowerShell重定向改变编码。下例在仓库根目录运行；按上一步真实结果修改路径：

```python
from pathlib import Path
import subprocess

serial = "SERIAL"
remote = "/data/user/0/com.alibaba.dingtalk.global/shared_prefs/PreferenceUtils.xml"
out = Path("extract/PreferenceUtils.xml")
out.parent.mkdir(exist_ok=True)
result = subprocess.run(
    ["adb", "-s", serial, "exec-out", "su", "-c", "cat " + remote],
    check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
with out.open("xb") as f:
    f.write(result.stdout)
print("已保存到本地私有目录；未打印内容")
```

不覆盖已有导出。若文件不存在、缓存字段变更或尚未加载设备列表，应停止按旧格式解析，核对版本；不要遍历并上传整个App数据目录。

## 2. 只解析设备列表字段

历史记录的SharedPreferences键是`device_list_id`，值为JSON设备列表。下面的离线示例输出到本地文件，不打印密钥；不是远程接口调用：

```python
import json
from pathlib import Path
import xml.etree.ElementTree as ET

root = ET.parse("extract/PreferenceUtils.xml").getroot()
values = [e.text for e in root.findall("string")
          if e.get("name") == "device_list_id"]
if len(values) != 1:
    raise SystemExit("未找到唯一device_list_id；请核对官方版本和缓存结构")
devices = json.loads(values[0])
if not isinstance(devices, list):
    raise SystemExit("设备列表结构已变化，停止")
items = []
for d in devices:
    if not isinstance(d, dict) or not d.get("deviceSecret"):
        continue
    items.append({k: d.get(k) for k in
                  ("deviceId", "deviceSecret", "corpId", "deviceSn", "devServId")})
if not items:
    raise SystemExit("没有带凭据的设备条目；不能用空密钥继续")
with Path("extract/owned-device-credentials.json").open("x", encoding="utf-8") as f:
    json.dump(items, f, ensure_ascii=False, indent=2)
print("仅在本地生成凭据文件，条目数：", len(items))
```

设备SN/服务字段名可能随模型变化，不要据空字段推断没有该设备。按自己设备的ID确认条目后，将相应密钥和corpId填入自己的客户端。不要把所有条目自动套给附近蓝牙设备。

## 3. did如何取得

旧版客户端需要手填：从自己官方App的A1连接HCI记录中查找0x0008或0x0133请求的`did`字段；这是手机客户端标识。也可在自己的受控研究环境观察`AuthService.getDeviceId()`返回值。

后来的客户端实现会本地生成并持久化did，但本仓库不保证所有固件均接受任意标识。复现历史连接时先沿用自己已经成功的配置，再单独验证是否可替换。did/corpId不参与已知AES的key计算，不代表设备完全不检查它们。

## 4. 无root设备怎么用

- 已取得这张卡的凭据：将凭据通过自己控制的方式导入另一台手机，即可进行本地鉴权；目标手机运行阶段不要求root。
- 尚无凭据：本仓库没有验证通用的“无root首次自动取密钥”方案。
- [外部PC工具项目](https://github.com/Shawn-TKD/dingtalk-a1-pc-tools)介绍了使用带root能力的Android模拟器登录并读取自己账号设备缓存的方法。它可能避免给日常手机root，但**本项目未验证日版账号/当前App在该环境的兼容性**。
- 蓝牙HCI日志有时可通过系统bugreport取得，无需root；但抓到random/token不等于得到deviceSecret，也不能靠它反推出密钥。

## 5. 抓包与本地验证

Android开发者选项开启蓝牙HCI侦听日志，按系统要求重启蓝牙后执行少量可识别动作，随后：

```powershell
adb -s SERIAL bugreport extract/own-bugreport.zip
python tools/btsnoop_gatt.py --help
python tools/protocol_analyze.py extract/own-bugreport.zip
python tools/verify_auth.py extract/verify_pairs.json
```

不同系统可能不把HCI日志放进bugreport，实际以导出内容为准。`verify_pairs.json`格式见`tools/verify_pairs.example.json`，只填写自己捕获的材料。上述工具可能输出原始标识/应答，不直接把终端全文发到issue。bugreport还可能含其他App和网络信息。

本仓库不包含真实密钥、完整凭据、原始bugreport、录音或登录Cookie。更换账号、解绑、复位后密钥是否轮换仍未验证，保留原始凭据不等于承诺永久有效。
