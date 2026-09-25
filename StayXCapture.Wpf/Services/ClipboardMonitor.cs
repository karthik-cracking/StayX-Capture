using System;
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Interop;

namespace StayXCapture.Wpf.Services
{
    public class ClipboardMonitor
    {
        [DllImport("user32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool AddClipboardFormatListener(IntPtr hwnd);

        [DllImport("user32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool RemoveClipboardFormatListener(IntPtr hwnd);

        private const int WM_CLIPBOARDUPDATE = 0x031D;
        private Window? _window;
        private IntPtr _hwnd;
        
        public event EventHandler? ClipboardChanged;

        public void Start(Window window)
        {
            _window = window;
            _hwnd = new WindowInteropHelper(window).EnsureHandle();
            HwndSource.FromHwnd(_hwnd)?.AddHook(HwndHook);
            AddClipboardFormatListener(_hwnd);
        }

        public void Stop()
        {
            if (_hwnd != IntPtr.Zero)
            {
                RemoveClipboardFormatListener(_hwnd);
                HwndSource.FromHwnd(_hwnd)?.RemoveHook(HwndHook);
            }
        }

        private IntPtr HwndHook(IntPtr hwnd, int msg, IntPtr wParam, IntPtr lParam, ref bool handled)
        {
            if (msg == WM_CLIPBOARDUPDATE)
            {
                ClipboardChanged?.Invoke(this, EventArgs.Empty);
            }
            return IntPtr.Zero;
        }
    }
}
