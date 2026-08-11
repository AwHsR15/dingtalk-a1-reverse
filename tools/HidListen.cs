// 被动监听 HID Input 报告 —— 只读,不向设备写入任何数据
using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Win32.SafeHandles;

class HidListen
{
    const uint GENERIC_READ = 0x80000000;
    const uint FILE_SHARE_READ = 1, FILE_SHARE_WRITE = 2, OPEN_EXISTING = 3;
    const uint FILE_FLAG_OVERLAPPED = 0x40000000;

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    static extern SafeFileHandle CreateFile(string name, uint access, uint share, IntPtr sec, uint disp, uint flags, IntPtr tmpl);

    static string Hex(byte[] b, int n)
    {
        var sb = new System.Text.StringBuilder();
        for (int i = 0; i < n; i++)
        {
            sb.Append(b[i].ToString("X2"));
            sb.Append((i % 16 == 15) ? "\n         " : " ");
        }
        return sb.ToString();
    }

    static string Ascii(byte[] b, int n)
    {
        var sb = new System.Text.StringBuilder();
        for (int i = 0; i < n; i++) sb.Append(b[i] >= 0x20 && b[i] < 0x7F ? (char)b[i] : '.');
        return sb.ToString();
    }

    static int Main(string[] args)
    {
        if (args.Length < 1) { Console.Error.WriteLine("usage: HidListen <devicePath> [seconds] [reportLen]"); return 1; }
        string path = args[0];
        int secs = args.Length > 1 ? int.Parse(args[1]) : 20;
        int len = args.Length > 2 ? int.Parse(args[2]) : 129;

        var h = CreateFile(path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, IntPtr.Zero, OPEN_EXISTING, FILE_FLAG_OVERLAPPED, IntPtr.Zero);
        if (h.IsInvalid) { Console.Error.WriteLine("open failed: " + Marshal.GetLastWin32Error()); return 2; }

        Console.WriteLine("listening " + secs + "s on " + path);
        Console.WriteLine("(read-only, nothing is written to the device)\n");

        var fs = new FileStream(h, FileAccess.Read, len, true);
        var cts = new CancellationTokenSource(TimeSpan.FromSeconds(secs));
        var buf = new byte[len];
        int count = 0;
        var t0 = DateTime.Now;

        try
        {
            while (!cts.IsCancellationRequested)
            {
                var task = fs.ReadAsync(buf, 0, len, cts.Token);
                int n = task.GetAwaiter().GetResult();
                if (n <= 0) continue;
                count++;
                int last = n; while (last > 1 && buf[last - 1] == 0) last--;
                Console.WriteLine(string.Format("[{0,7:F3}s] #{1}  reportId=0x{2:X2}  len={3} (nonzero to {4})",
                    (DateTime.Now - t0).TotalSeconds, count, buf[0], n, last));
                Console.WriteLine("  hex:   " + Hex(buf, Math.Min(last + 8, n)));
                Console.WriteLine("  ascii: " + Ascii(buf, Math.Min(last + 8, n)));
                Console.WriteLine();
            }
        }
        catch (OperationCanceledException) { }
        catch (Exception e) { Console.Error.WriteLine("read error: " + e.Message); }

        Console.WriteLine("done. " + count + " report(s) received in " + secs + "s.");
        return 0;
    }
}
