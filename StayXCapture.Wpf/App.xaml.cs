using System.Configuration;
using System.Data;
using System.Windows;
using Hardcodet.Wpf.TaskbarNotification;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Controls;
using System.Runtime.InteropServices;
using System.Diagnostics;
using System.Linq;

namespace StayXCapture.Wpf
{
    public static class MemoryHelper
    {
        [DllImport("psapi.dll")]
        static extern int EmptyWorkingSet(IntPtr hwProc);

        public static void MinimizeMemory()
        {
            GC.Collect(2, GCCollectionMode.Aggressive, true, true);
            GC.WaitForPendingFinalizers();
            GC.Collect(2, GCCollectionMode.Aggressive, true, true);
            try
            {
                EmptyWorkingSet(Process.GetCurrentProcess().Handle);
            }
            catch { }
        }
    }

    public partial class App : Application
    {
        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool AttachConsole(int dwProcessId);
        private const int ATTACH_PARENT_PROCESS = -1;

        private TaskbarIcon? _notifyIcon;
        private MainWindow? _mainWindow;
        private Mutex? _mutex;
        private EventWaitHandle? _showEvent;

        private void Application_Startup(object sender, StartupEventArgs e)
        {
            DispatcherUnhandledException += (s, ev) =>
            {
                System.Diagnostics.Debug.WriteLine($"[StayX Capture] Handled dispatcher exception: {ev.Exception}");
                ev.Handled = true;
            };

            Services.ConfigService.Load();
            Services.HistoryService.Load();
            
            ChangeTheme(Services.ConfigService.Current.IsDarkTheme);
            
            const string appName = "StayXCaptureWpfUniqueInstance";
            const string showEventName = "StayXCaptureWpfShowEvent";
            bool createdNew;

            _mutex = new Mutex(true, appName, out createdNew);

            if (!createdNew)
            {
                try
                {
                    using var existingEvent = EventWaitHandle.OpenExisting(showEventName);
                    existingEvent.Set();
                }
                catch { }

                Current.Shutdown();
                return;
            }

            try
            {
                _showEvent = new EventWaitHandle(false, EventResetMode.AutoReset, showEventName);
                ThreadPool.RegisterWaitForSingleObject(_showEvent, (state, timedOut) =>
                {
                    Current.Dispatcher.Invoke(() => ShowMainWindow());
                }, null, -1, false);
            }
            catch { }

            // Attach to calling terminal console if available
            AttachConsole(ATTACH_PARENT_PROCESS);
            Console.WriteLine("[StayX Capture] Application starting...");

            // Ensure app doesn't close when main window hides
            ShutdownMode = ShutdownMode.OnExplicitShutdown;

            int targetWidth = (int)SystemParameters.SmallIconWidth;
            int targetHeight = (int)SystemParameters.SmallIconHeight;
            if (targetWidth <= 0) targetWidth = 16;
            if (targetHeight <= 0) targetHeight = 16;

            try
            {
                _notifyIcon = (TaskbarIcon)FindResource("AppTaskbarIcon");
            }
            catch
            {
                _notifyIcon = new TaskbarIcon();
            }

            string localIco = System.IO.Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Assets", "app_icon.ico");
            if (System.IO.File.Exists(localIco))
            {
                try
                {
                    _notifyIcon.Icon = new System.Drawing.Icon(localIco, targetWidth, targetHeight);
                }
                catch { }
            }
            else
            {
                try
                {
                    var iconUri = new Uri("pack://application:,,,/StayXCapture.Wpf;component/Assets/app_icon.ico");
                    var resourceStream = Application.GetResourceStream(iconUri)?.Stream;
                    if (resourceStream != null)
                    {
                        _notifyIcon.Icon = new System.Drawing.Icon(resourceStream, targetWidth, targetHeight);
                    }
                }
                catch { }
            }

            _notifyIcon.ToolTipText = "StayX Capture";
            _notifyIcon.Visibility = Visibility.Visible;
            _notifyIcon.TrayLeftMouseDown += NotifyIcon_TrayLeftMouseDown;

            var contextMenu = new ContextMenu();
            var openMenuItem = new MenuItem { Header = "Open StayX Capture" };
            openMenuItem.Click += (s, ev) => ShowMainWindow();
            contextMenu.Items.Add(openMenuItem);
            contextMenu.Items.Add(new Separator());

            var exitMenuItem = new MenuItem { Header = "Exit" };
            exitMenuItem.Click += (s, ev) => Current.Shutdown();
            contextMenu.Items.Add(exitMenuItem);
            _notifyIcon.ContextMenu = contextMenu;

            // Initialize Hotkeys
            Services.HotkeyManager.Initialize();
            Services.HotkeyManager.RegionCaptureRequested += (s, ev) => 
            {
                Current.Dispatcher.Invoke(async () => 
                {
                    if (_mainWindow != null && _mainWindow.IsVisible)
                    {
                        _mainWindow.Hide();
                        await Task.Delay(150); // Give time for window to hide without blocking UI thread
                    }
                    
                    try
                    {
                        // Capture full screen first
                        var fullScreenBitmap = Services.CaptureService.CaptureFullScreen();
                        if (fullScreenBitmap != null)
                        {
                            var regionWindow = new Windows.RegionSelectionWindow(fullScreenBitmap);
                            regionWindow.RegionSelected += (croppedBitmap) =>
                            {
                                ProcessCapture(croppedBitmap);
                            };
                            regionWindow.Show();
                            regionWindow.Activate();
                            regionWindow.Focus();
                        }
                    }
                    catch (Exception ex)
                    {
                        System.Diagnostics.Debug.WriteLine($"Region capture error: {ex.Message}");
                    }
                });
            };

            Services.HotkeyManager.FullScreenCaptureRequested += (s, ev) => 
            {
                ExecuteFullScreenCapture();
            };

            bool startMinimized = e.Args.Any(a => a.Equals("--minimized", StringComparison.OrdinalIgnoreCase) || a.Equals("-m", StringComparison.OrdinalIgnoreCase));
            if (!startMinimized)
            {
                ShowMainWindow();
            }
            else
            {
                _notifyIcon.ShowBalloonTip("StayX Capture", "Running in background! Press your hotkey or click this icon.", Hardcodet.Wpf.TaskbarNotification.BalloonIcon.Info);
                Task.Delay(1500).ContinueWith(_ => MemoryHelper.MinimizeMemory());
            }
        }

        public void ExecuteFullScreenCapture()
        {
            Current.Dispatcher.Invoke(async () => 
            {
                if (_mainWindow != null && _mainWindow.IsVisible)
                {
                    _mainWindow.Hide();
                    await Task.Delay(150);
                }

                try
                {
                    var config = Services.ConfigService.Current;
                    var screens = Services.CaptureService.GetScreens();

                    if (config.PromptDisplaySelection && screens.Count > 1)
                    {
                        var selectWindow = new Windows.DisplaySelectionWindow(screens);
                        selectWindow.DisplaySelected += (selectedScreen) =>
                        {
                            System.Windows.Media.Imaging.BitmapSource? capturedBmp;
                            if (selectedScreen != null)
                            {
                                capturedBmp = Services.CaptureService.CaptureScreen(selectedScreen);
                            }
                            else
                            {
                                capturedBmp = Services.CaptureService.CaptureFullScreen();
                            }

                            if (capturedBmp != null)
                            {
                                ProcessCapture(capturedBmp);
                            }
                        };
                        selectWindow.Show();
                        selectWindow.Activate();
                        selectWindow.Focus();
                    }
                    else
                    {
                        var bitmap = Services.CaptureService.CaptureFullScreen();
                        if (bitmap != null)
                        {
                            ProcessCapture(bitmap);
                        }
                    }
                }
                catch (Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine($"Fullscreen capture error: {ex.Message}");
                }
            });
        }

        public async void ProcessCapture(System.Windows.Media.Imaging.BitmapSource bitmap)
        {
            var config = Services.ConfigService.Current;
            
            string filePath = "";
            if (config.AutoOrganize)
            {
                string folder = System.IO.Path.Combine(config.SaveFolder, DateTime.Now.ToString("yyyy-MM-dd"));
                System.IO.Directory.CreateDirectory(folder);
                filePath = System.IO.Path.Combine(folder, $"Capture_{DateTime.Now:HH-mm-ss}.png");
            }
            else
            {
                System.IO.Directory.CreateDirectory(config.SaveFolder);
                filePath = System.IO.Path.Combine(config.SaveFolder, $"Capture_{DateTime.Now:yyyy-MM-dd_HH-mm-ss}.png");
            }

            // Save to disk
            using (var fileStream = new System.IO.FileStream(filePath, System.IO.FileMode.Create))
            {
                var encoder = new System.Windows.Media.Imaging.PngBitmapEncoder();
                encoder.Frames.Add(System.Windows.Media.Imaging.BitmapFrame.Create(bitmap));
                encoder.Save(fileStream);
            }

            // Add to history
            Services.HistoryService.Add(new Services.HistoryItem 
            { 
                Type = "image", 
                Data = filePath, 
                Timestamp = DateTime.Now.ToString("g") 
            });

            if (config.CopyClipboard)
            {
                Services.CaptureService.SaveToClipboard(bitmap);
            }

            if (config.OpenEditor)
            {
                var editor = new Windows.EditorWindow(bitmap);
                editor.Show();
                editor.Activate();
            }

            bool shouldUpload = false;

            if (config.AskBeforeUpload)
            {
                // Smooth delay after overlay closes before displaying popup dialog
                await Task.Delay(280);
                var prompt = new Windows.UploadPromptWindow(bitmap);
                prompt.ShowDialog();
                shouldUpload = prompt.ShouldUpload;
            }
            else if (config.AutoUpload)
            {
                shouldUpload = true;
            }

            if (shouldUpload)
            {
                _notifyIcon?.ShowBalloonTip("StayX Capture", "Screenshot saved! Uploading...", Hardcodet.Wpf.TaskbarNotification.BalloonIcon.Info);

                _ = Task.Run(async () =>
                {
                    string? uploadedUrl = null;
                    string apiKey = !string.IsNullOrWhiteSpace(config.CustomApiKey) ? config.CustomApiKey : config.DMarketApiKey;
                    string endpoint = !string.IsNullOrWhiteSpace(config.CustomApiEndpoint) ? config.CustomApiEndpoint : "https://dmarket.space/api/upload";

                    if (!string.IsNullOrWhiteSpace(apiKey))
                    {
                        uploadedUrl = await Services.ApiService.UploadToCustomApiAsync(filePath, endpoint, apiKey);
                    }
                    else if (!string.IsNullOrWhiteSpace(config.ImgbbApiKey))
                    {
                        uploadedUrl = await Services.ApiService.UploadToImgBBAsync(filePath, config.ImgbbApiKey);
                    }

                    Application.Current.Dispatcher.Invoke(() =>
                    {
                        if (!string.IsNullOrWhiteSpace(uploadedUrl))
                        {
                            System.Windows.Clipboard.SetText(uploadedUrl);
                            if (_notifyIcon != null)
                            {
                                _notifyIcon.ShowBalloonTip("StayX Capture", $"Uploaded to API! URL copied:\n{uploadedUrl}", Hardcodet.Wpf.TaskbarNotification.BalloonIcon.Info);
                            }
                        }
                        else
                        {
                            if (_notifyIcon != null)
                            {
                                _notifyIcon.ShowBalloonTip("StayX Capture", "Screenshot saved locally (API upload did not return URL).", Hardcodet.Wpf.TaskbarNotification.BalloonIcon.Warning);
                            }
                        }
                        MemoryHelper.MinimizeMemory();
                    });
                });
            }
            else
            {
                if (!config.OpenEditor && _notifyIcon != null)
                {
                    _notifyIcon.ShowBalloonTip("StayX Capture", "Screenshot saved successfully.", Hardcodet.Wpf.TaskbarNotification.BalloonIcon.Info);
                }
                if (!config.OpenEditor)
                {
                    MemoryHelper.MinimizeMemory();
                }
            }
        }

        public void ShowMainWindow()
        {
            if (_mainWindow == null)
            {
                _mainWindow = new MainWindow();
                _mainWindow.Closing += (s, ev) => 
                {
                    ev.Cancel = true;
                    _mainWindow.Hide();
                    Task.Delay(300).ContinueWith(_ => MemoryHelper.MinimizeMemory());
                };
            }

            var desktopWorkingArea = SystemParameters.WorkArea;
            _mainWindow.Left = desktopWorkingArea.Right - _mainWindow.Width - 10;
            _mainWindow.Top = desktopWorkingArea.Bottom - _mainWindow.Height - 10;

            if (_mainWindow.WindowState == WindowState.Minimized)
            {
                _mainWindow.WindowState = WindowState.Normal;
            }

            _mainWindow.Show();
            _mainWindow.Activate();
            _mainWindow.Focus();
        }

        private void NotifyIcon_TrayLeftMouseDown(object sender, RoutedEventArgs e)
        {
            if (_mainWindow != null && _mainWindow.IsVisible)
            {
                _mainWindow.Hide();
                Task.Delay(300).ContinueWith(_ => MemoryHelper.MinimizeMemory());
            }
            else
            {
                ShowMainWindow();
            }
        }

        private void Application_Exit(object sender, ExitEventArgs e)
        {
            _showEvent?.Dispose();
            _showEvent = null;

            if (_mutex != null)
            {
                try { _mutex.ReleaseMutex(); } catch { }
                _mutex.Dispose();
                _mutex = null;
            }

            if (_notifyIcon != null)
            {
                _notifyIcon.Dispose();
                _notifyIcon = null;
            }
        }

        public void ChangeTheme(bool isDark)
        {
            var dict = new ResourceDictionary
            {
                Source = new Uri(isDark ? "Themes/DarkTheme.xaml" : "Themes/LightTheme.xaml", UriKind.Relative)
            };
            Current.Resources.MergedDictionaries.Clear();
            Current.Resources.MergedDictionaries.Add(dict);
        }
    }
}
