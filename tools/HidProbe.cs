using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

class HidProbe
{
    const int DIGCF_PRESENT = 0x02, DIGCF_DEVICEINTERFACE = 0x10;
    const uint GENERIC_READ = 0x80000000, GENERIC_WRITE = 0x40000000;
    const uint FILE_SHARE_READ = 1, FILE_SHARE_WRITE = 2, OPEN_EXISTING = 3;

    [StructLayout(LayoutKind.Sequential)]
    struct SP_DEVICE_INTERFACE_DATA { public int cbSize; public Guid InterfaceClassGuid; public int Flags; public IntPtr Reserved; }

    [StructLayout(LayoutKind.Sequential)]
    struct HIDD_ATTRIBUTES { public int Size; public ushort VendorID; public ushort ProductID; public ushort VersionNumber; }

    [StructLayout(LayoutKind.Sequential)]
    struct HIDP_CAPS
    {
        public ushort Usage, UsagePage;
        public ushort InputReportByteLength, OutputReportByteLength, FeatureReportByteLength;
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 17)] public ushort[] Reserved;
        public ushort NumberLinkCollectionNodes;
        public ushort NumberInputButtonCaps, NumberInputValueCaps, NumberInputDataIndices;
        public ushort NumberOutputButtonCaps, NumberOutputValueCaps, NumberOutputDataIndices;
        public ushort NumberFeatureButtonCaps, NumberFeatureValueCaps, NumberFeatureDataIndices;
    }

    [DllImport("hid.dll")] static extern void HidD_GetHidGuid(out Guid g);
    [DllImport("hid.dll")] static extern bool HidD_GetAttributes(IntPtr h, ref HIDD_ATTRIBUTES a);
    [DllImport("hid.dll", CharSet = CharSet.Unicode)] static extern bool HidD_GetManufacturerString(IntPtr h, StringBuilder b, int len);
    [DllImport("hid.dll", CharSet = CharSet.Unicode)] static extern bool HidD_GetProductString(IntPtr h, StringBuilder b, int len);
    [DllImport("hid.dll", CharSet = CharSet.Unicode)] static extern bool HidD_GetSerialNumberString(IntPtr h, StringBuilder b, int len);
    [DllImport("hid.dll")] static extern bool HidD_GetPreparsedData(IntPtr h, out IntPtr pp);
    [DllImport("hid.dll")] static extern bool HidD_FreePreparsedData(IntPtr pp);
    [DllImport("hid.dll")] static extern int HidP_GetCaps(IntPtr pp, ref HIDP_CAPS caps);

    [DllImport("setupapi.dll", CharSet = CharSet.Unicode)]
    static extern IntPtr SetupDiGetClassDevs(ref Guid g, IntPtr enumerator, IntPtr hwnd, int flags);
    [DllImport("setupapi.dll")]
    static extern bool SetupDiEnumDeviceInterfaces(IntPtr set, IntPtr devInfo, ref Guid g, int i, ref SP_DEVICE_INTERFACE_DATA d);
    [DllImport("setupapi.dll", CharSet = CharSet.Unicode)]
    static extern bool SetupDiGetDeviceInterfaceDetail(IntPtr set, ref SP_DEVICE_INTERFACE_DATA d, IntPtr detail, int size, ref int required, IntPtr devInfo);
    [DllImport("setupapi.dll")] static extern bool SetupDiDestroyDeviceInfoList(IntPtr set);

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode)]
    static extern IntPtr CreateFile(string name, uint access, uint share, IntPtr sec, uint disp, uint flags, IntPtr tmpl);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);

    static string Str(Func<IntPtr, StringBuilder, int, bool> fn, IntPtr h)
    {
        var sb = new StringBuilder(512);
        try { return fn(h, sb, sb.Capacity * 2) ? sb.ToString() : "<n/a>"; }
        catch { return "<err>"; }
    }

    static void Main(string[] args)
    {
        ushort? filterVid = null;
        if (args.Length > 0) filterVid = Convert.ToUInt16(args[0], 16);

        Guid hidGuid; HidD_GetHidGuid(out hidGuid);
        IntPtr set = SetupDiGetClassDevs(ref hidGuid, IntPtr.Zero, IntPtr.Zero, DIGCF_PRESENT | DIGCF_DEVICEINTERFACE);

        var did = new SP_DEVICE_INTERFACE_DATA();
        did.cbSize = Marshal.SizeOf(did);

        for (int i = 0; SetupDiEnumDeviceInterfaces(set, IntPtr.Zero, ref hidGuid, i, ref did); i++)
        {
            int need = 0;
            SetupDiGetDeviceInterfaceDetail(set, ref did, IntPtr.Zero, 0, ref need, IntPtr.Zero);
            IntPtr buf = Marshal.AllocHGlobal(need);
            Marshal.WriteInt32(buf, IntPtr.Size == 8 ? 8 : 6);
            string path = null;
            if (SetupDiGetDeviceInterfaceDetail(set, ref did, buf, need, ref need, IntPtr.Zero))
                path = Marshal.PtrToStringUni(new IntPtr(buf.ToInt64() + 4));
            Marshal.FreeHGlobal(buf);
            if (path == null) continue;

            IntPtr h = CreateFile(path, GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE, IntPtr.Zero, OPEN_EXISTING, 0, IntPtr.Zero);
            if (h == new IntPtr(-1))
                h = CreateFile(path, 0, FILE_SHARE_READ | FILE_SHARE_WRITE, IntPtr.Zero, OPEN_EXISTING, 0, IntPtr.Zero);
            if (h == new IntPtr(-1)) continue;

            var attr = new HIDD_ATTRIBUTES(); attr.Size = Marshal.SizeOf(attr);
            if (HidD_GetAttributes(h, ref attr) && (filterVid == null || attr.VendorID == filterVid.Value))
            {
                Console.WriteLine("=========================================================");
                Console.WriteLine("Path   : " + path);
                Console.WriteLine(string.Format("VID/PID: {0:X4}:{1:X4}  rev {2:X4}", attr.VendorID, attr.ProductID, attr.VersionNumber));
                Console.WriteLine("Mfr    : " + Str(HidD_GetManufacturerString, h));
                Console.WriteLine("Product: " + Str(HidD_GetProductString, h));
                Console.WriteLine("Serial : " + Str(HidD_GetSerialNumberString, h));

                IntPtr pp;
                if (HidD_GetPreparsedData(h, out pp))
                {
                    var caps = new HIDP_CAPS();
                    if (HidP_GetCaps(pp, ref caps) == 0x110000)
                    {
                        Console.WriteLine(string.Format("UsagePage/Usage: {0:X4}/{1:X4}", caps.UsagePage, caps.Usage));
                        Console.WriteLine(string.Format("Report len  In={0} Out={1} Feature={2}",
                            caps.InputReportByteLength, caps.OutputReportByteLength, caps.FeatureReportByteLength));
                    }
                    HidD_FreePreparsedData(pp);
                }
            }
            CloseHandle(h);
        }
        SetupDiDestroyDeviceInfoList(set);
    }
}
