using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Windows.Media.Imaging;
using System.Windows;
using System.Windows.Interop;
using System.Runtime.InteropServices;

namespace StayXCapture.Wpf.Services
{
    public class ScreenInfo
    {
        public int Index { get; set; }
        public string DeviceName { get; set; } = "";
        public int X { get; set; }
        public int Y { get; set; }
        public int Width { get; set; }
        public int Height { get; set; }
        public bool IsPrimary { get; set; }

        public string Title => IsPrimary ? $"Display {Index} (Primary)" : $"Display {Index}";
        public string ResolutionText => $"{Width} × {Height}";
    }

    public class CaptureService
    {
        [DllImport("gdi32.dll")]
        [return: MarshalAs(UnmanagedType.Bool)]
        internal static extern bool DeleteObject(IntPtr hObject);

        [StructLayout(LayoutKind.Sequential)]
        public struct RECT { public int Left, Top, Right, Bottom; }

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
        public class MONITORINFOEX
        {
            public int cbSize = Marshal.SizeOf(typeof(MONITORINFOEX));
            public RECT rcMonitor;
            public RECT rcWork;
            public int dwFlags;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)]
            public string szDevice = "";
        }

        private delegate bool MonitorEnumProc(IntPtr hMonitor, IntPtr hdcMonitor, ref RECT lprcMonitor, IntPtr dwData);

        [DllImport("user32.dll")]
        private static extern bool EnumDisplayMonitors(IntPtr hdc, IntPtr lprcClip, MonitorEnumProc lpfnEnum, IntPtr dwData);

        [DllImport("user32.dll", CharSet = CharSet.Auto)]
        private static extern bool GetMonitorInfo(IntPtr hMonitor, [In, Out] MONITORINFOEX lpmi);

        public static List<ScreenInfo> GetScreens()
        {
            var screens = new List<ScreenInfo>();
            int index = 1;
            EnumDisplayMonitors(IntPtr.Zero, IntPtr.Zero, (IntPtr hMon, IntPtr hdc, ref RECT rc, IntPtr data) =>
            {
                var mi = new MONITORINFOEX();
                if (GetMonitorInfo(hMon, mi))
                {
                    screens.Add(new ScreenInfo
                    {
                        Index = index++,
                        DeviceName = mi.szDevice,
                        X = mi.rcMonitor.Left,
                        Y = mi.rcMonitor.Top,
                        Width = mi.rcMonitor.Right - mi.rcMonitor.Left,
                        Height = mi.rcMonitor.Bottom - mi.rcMonitor.Top,
                        IsPrimary = (mi.dwFlags & 1) != 0
                    });
                }
                return true;
            }, IntPtr.Zero);

            return screens;
        }

        public static BitmapSource CaptureRegion(int x, int y, int width, int height)
        {
            using var bitmap = new Bitmap(width, height, PixelFormat.Format32bppArgb);
            using var graphics = Graphics.FromImage(bitmap);
            graphics.CopyFromScreen(x, y, 0, 0, new System.Drawing.Size(width, height), CopyPixelOperation.SourceCopy);
            
            IntPtr hBitmap = bitmap.GetHbitmap();
            try
            {
                return Imaging.CreateBitmapSourceFromHBitmap(
                    hBitmap,
                    IntPtr.Zero,
                    Int32Rect.Empty,
                    BitmapSizeOptions.FromEmptyOptions());
            }
            finally
            {
                DeleteObject(hBitmap);
            }
        }

        public static BitmapSource CaptureScreen(ScreenInfo screen)
        {
            return CaptureRegion(screen.X, screen.Y, screen.Width, screen.Height);
        }

        public static BitmapSource CaptureFullScreen()
        {
            int width = (int)SystemParameters.VirtualScreenWidth;
            int height = (int)SystemParameters.VirtualScreenHeight;
            int left = (int)SystemParameters.VirtualScreenLeft;
            int top = (int)SystemParameters.VirtualScreenTop;
            
            return CaptureRegion(left, top, width, height);
        }
        
        public static void SaveToClipboard(BitmapSource bitmapSource)
        {
            Clipboard.SetImage(bitmapSource);
        }
    }
}
