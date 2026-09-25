using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;

namespace StayXCapture.Wpf
{
    public partial class MainWindow : Window
    {
        private bool _isInitializing = true;
        private Services.ClipboardMonitor _clipboardMonitor = new Services.ClipboardMonitor();

        public MainWindow()
        {
            InitializeComponent();
            LoadSettings();
            
            // Start clipboard monitoring if enabled
            if (Services.ConfigService.Current.MonitorClipboard)
            {
                this.Loaded += (s, e) => _clipboardMonitor.Start(this);
            }
            
            _clipboardMonitor.ClipboardChanged += ClipboardMonitor_ClipboardChanged;
            
            this.IsVisibleChanged += (s, e) => 
            {
                if (this.IsVisible)
                {
                    RefreshHistory();
                }
            };
            
            RefreshHistory();
        }

        private async void ClipboardMonitor_ClipboardChanged(object? sender, EventArgs e)
        {
            try
            {
                string? text = null;
                for (int i = 0; i < 5; i++)
                {
                    try
                    {
                        if (System.Windows.Clipboard.ContainsText())
                        {
                            text = System.Windows.Clipboard.GetText();
                            break;
                        }
                        else
                        {
                            break;
                        }
                    }
                    catch (System.Runtime.InteropServices.COMException)
                    {
                        await System.Threading.Tasks.Task.Delay(50);
                    }
                    catch
                    {
                        break;
                    }
                }

                if (!string.IsNullOrWhiteSpace(text))
                {
                    string preview = text.Length > 50 ? text.Substring(0, 47) + "..." : text;
                    var last = Services.HistoryService.CurrentHistory.FirstOrDefault(h => h.Type == "text");
                    if (last == null || last.Data != preview)
                    {
                        Services.HistoryService.Add(new Services.HistoryItem
                        {
                            Type = "text",
                            Data = preview,
                            Timestamp = DateTime.Now.ToString("g")
                        });
                        RefreshHistory();
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Clipboard monitoring error: {ex.Message}");
            }
        }

        private void RefreshHistory()
        {
            // Populate clipboard text history to Home Tab list
            ClipboardList.ItemsSource = Services.HistoryService.CurrentHistory.Where(h => h.Type == "text").ToList();
            
            // Dynamically scan for recent captures in the save directory for History Tab list
            var imageList = new List<Services.HistoryItem>();
            try
            {
                var folder = new System.IO.DirectoryInfo(Services.ConfigService.Current.SaveFolder);
                if (folder.Exists)
                {
                    // Use EnumerateFiles with top directory, then safely get directories
                    var files = SafeEnumerateFiles(folder.FullName, "*.png").OrderByDescending(f => f.CreationTime).Take(50);
                                      
                    foreach (var f in files)
                    {
                        imageList.Add(new Services.HistoryItem
                        {
                            Type = "image",
                            Data = f.FullName,
                            Name = f.Name,
                            SizeText = f.Length < 1048576 ? $"{f.Length / 1024} KB" : $"{f.Length / 1048576.0:F1} MB",
                            Timestamp = f.CreationTime.ToString("g")
                        });
                    }
                }
            }
            catch (Exception ex) 
            { 
                StatusText.Text = "History load error: " + ex.Message;
            }
            
            HistoryList.ItemsSource = imageList;
        }

        private IEnumerable<System.IO.FileInfo> SafeEnumerateFiles(string path, string searchPattern)
        {
            var files = new List<System.IO.FileInfo>();
            try
            {
                var dir = new System.IO.DirectoryInfo(path);
                files.AddRange(dir.GetFiles(searchPattern));
                
                foreach (var subDir in dir.GetDirectories())
                {
                    files.AddRange(SafeEnumerateFiles(subDir.FullName, searchPattern));
                }
            }
            catch { }
            return files;
        }

        private void LoadSettings()
        {
            var config = Services.ConfigService.Current;
            ChkThemeToggle.IsChecked = !config.IsDarkTheme;
            ChkAutoOrganize.IsChecked = config.AutoOrganize;
            ChkCopyClipboard.IsChecked = config.CopyClipboard;
            ChkOpenEditor.IsChecked = config.OpenEditor;
            ChkPromptDisplaySelection.IsChecked = config.PromptDisplaySelection;
            ChkStartMinimized.IsChecked = config.StartMinimized;
            ChkAutoStart.IsChecked = config.AutoStart;
            ChkMonitorClipboard.IsChecked = config.MonitorClipboard;
            TxtSaveFolder.Text = config.SaveFolder;
            TxtHotkeyRegion.Text = GetFriendlyHotkeyString(config.HotkeyRegion);
            TxtHotkeyFullscreen.Text = GetFriendlyHotkeyString(config.HotkeyFullscreen);
            LblHotkeyRegion.Text = $"({GetFriendlyHotkeyString(config.HotkeyRegion)})";
            LblHotkeyFullscreen.Text = $"({GetFriendlyHotkeyString(config.HotkeyFullscreen)})";
            
            ChkAutoUpload.IsChecked = config.AutoUpload;
            ChkAskBeforeUpload.IsChecked = config.AskBeforeUpload;
            TxtApiEndpoint.Text = string.IsNullOrWhiteSpace(config.CustomApiEndpoint) 
                ? "https://dmarket.space/api/upload" 
                : config.CustomApiEndpoint;
            TxtCustomApiKey.Text = !string.IsNullOrWhiteSpace(config.CustomApiKey) 
                ? config.CustomApiKey 
                : config.DMarketApiKey;
            TxtImgbbApiKey.Text = config.ImgbbApiKey;
            TxtGoogleDriveApiKey.Text = config.GoogleDriveApiKey;
            
            _isInitializing = false;
        }

        private void Setting_Changed(object sender, RoutedEventArgs e)
        {
            if (_isInitializing) return;

            // When "Ask to upload" is toggled ON, toggle OFF "Auto-upload" (and vice-versa)
            if (sender == ChkAskBeforeUpload && ChkAskBeforeUpload.IsChecked == true)
            {
                ChkAutoUpload.IsChecked = false;
            }
            else if (sender == ChkAutoUpload && ChkAutoUpload.IsChecked == true)
            {
                ChkAskBeforeUpload.IsChecked = false;
            }

            var config = Services.ConfigService.Current;
            config.AutoOrganize = ChkAutoOrganize.IsChecked ?? false;
            config.CopyClipboard = ChkCopyClipboard.IsChecked ?? false;
            config.OpenEditor = ChkOpenEditor.IsChecked ?? false;
            config.PromptDisplaySelection = ChkPromptDisplaySelection.IsChecked ?? false;
            config.StartMinimized = ChkStartMinimized.IsChecked ?? false;
            config.AutoStart = ChkAutoStart.IsChecked ?? false;
            config.MonitorClipboard = ChkMonitorClipboard.IsChecked ?? false;
            
            config.AutoUpload = ChkAutoUpload.IsChecked ?? false;
            config.AskBeforeUpload = ChkAskBeforeUpload.IsChecked ?? false;
            config.CustomApiEndpoint = string.IsNullOrWhiteSpace(TxtApiEndpoint.Text) 
                ? "https://dmarket.space/api/upload" 
                : TxtApiEndpoint.Text.Trim();
            config.CustomApiKey = TxtCustomApiKey.Text.Trim();
            config.ImgbbApiKey = TxtImgbbApiKey.Text.Trim();
            config.GoogleDriveApiKey = TxtGoogleDriveApiKey.Text.Trim();
            
            Services.ConfigService.Save();

            // Handle AutoStart Registry logic (omitted for brevity, can be added)
        }

        private string GetFriendlyKeyName(System.Windows.Input.Key key)
        {
            return key switch
            {
                System.Windows.Input.Key.OemOpenBrackets => "[",
                System.Windows.Input.Key.Oem6 => "]",
                System.Windows.Input.Key.OemQuestion => "/",
                System.Windows.Input.Key.OemQuotes => "'",
                System.Windows.Input.Key.OemPlus => "+",
                System.Windows.Input.Key.OemMinus => "-",
                System.Windows.Input.Key.Oem5 => "\\",
                System.Windows.Input.Key.Oem1 => ";",
                System.Windows.Input.Key.OemTilde => "`",
                System.Windows.Input.Key.OemComma => ",",
                System.Windows.Input.Key.OemPeriod => ".",
                System.Windows.Input.Key.D0 => "0",
                System.Windows.Input.Key.D1 => "1",
                System.Windows.Input.Key.D2 => "2",
                System.Windows.Input.Key.D3 => "3",
                System.Windows.Input.Key.D4 => "4",
                System.Windows.Input.Key.D5 => "5",
                System.Windows.Input.Key.D6 => "6",
                System.Windows.Input.Key.D7 => "7",
                System.Windows.Input.Key.D8 => "8",
                System.Windows.Input.Key.D9 => "9",
                _ => key.ToString()
            };
        }

        private string GetFriendlyHotkeyString(string rawHotkey)
        {
            if (string.IsNullOrEmpty(rawHotkey)) return "";
            var parts = rawHotkey.Split('+');
            if (parts.Length == 0) return rawHotkey;
            
            string keyPart = parts[parts.Length - 1].Trim();
            var parsedKey = Services.HotkeyManager.ParseKeyPart(keyPart);
            if (parsedKey != System.Windows.Input.Key.None)
            {
                parts[parts.Length - 1] = GetFriendlyKeyName(parsedKey);
                return string.Join("+", parts);
            }
            return rawHotkey;
        }

        private void TxtHotkey_KeyDown(object sender, System.Windows.Input.KeyEventArgs e)
        {
            if (sender is TextBox txt)
            {
                e.Handled = true;
                
                var actualKey = e.Key == System.Windows.Input.Key.System ? e.SystemKey : e.Key;
                if (actualKey == System.Windows.Input.Key.ImeProcessed) actualKey = e.ImeProcessedKey;

                // Ignore modifier keys by themselves
                if (actualKey == System.Windows.Input.Key.LeftCtrl || actualKey == System.Windows.Input.Key.RightCtrl ||
                    actualKey == System.Windows.Input.Key.LeftShift || actualKey == System.Windows.Input.Key.RightShift ||
                    actualKey == System.Windows.Input.Key.LeftAlt || actualKey == System.Windows.Input.Key.RightAlt ||
                    actualKey == System.Windows.Input.Key.LWin || actualKey == System.Windows.Input.Key.RWin)
                {
                    return;
                }

                var modifiers = System.Windows.Input.Keyboard.Modifiers;

                string rawHotkeyStr = "";
                if (modifiers.HasFlag(System.Windows.Input.ModifierKeys.Control)) rawHotkeyStr += "Ctrl+";
                if (modifiers.HasFlag(System.Windows.Input.ModifierKeys.Shift)) rawHotkeyStr += "Shift+";
                if (modifiers.HasFlag(System.Windows.Input.ModifierKeys.Alt)) rawHotkeyStr += "Alt+";
                rawHotkeyStr += actualKey.ToString();

                string displayHotkeyStr = GetFriendlyHotkeyString(rawHotkeyStr);

                txt.Text = displayHotkeyStr;

                if (txt == TxtHotkeyRegion)
                {
                    Services.ConfigService.Current.HotkeyRegion = rawHotkeyStr;
                    LblHotkeyRegion.Text = $"({displayHotkeyStr})";
                }
                if (txt == TxtHotkeyFullscreen)
                {
                    Services.ConfigService.Current.HotkeyFullscreen = rawHotkeyStr;
                    LblHotkeyFullscreen.Text = $"({displayHotkeyStr})";
                }

                Services.ConfigService.Save();
                
                // Immediately apply new hotkeys dynamically!
                Services.HotkeyManager.ReloadHotkeys();
                
                System.Windows.Input.Keyboard.ClearFocus();
                TabSettings.Focus();
            }
        }

        private void TxtHotkey_GotFocus(object sender, RoutedEventArgs e)
        {
            if (sender is TextBox txt)
            {
                txt.Text = "Listening for keybind...";
            }
        }

        private void TxtHotkey_LostFocus(object sender, RoutedEventArgs e)
        {
            if (sender is TextBox txt)
            {
                var config = Services.ConfigService.Current;
                if (txt == TxtHotkeyRegion) txt.Text = GetFriendlyHotkeyString(config.HotkeyRegion);
                if (txt == TxtHotkeyFullscreen) txt.Text = GetFriendlyHotkeyString(config.HotkeyFullscreen);
            }
        }
        
        private void BrowseFolder_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new Microsoft.Win32.OpenFolderDialog();
            if (dialog.ShowDialog() == true)
            {
                TxtSaveFolder.Text = dialog.FolderName;
                Services.ConfigService.Current.SaveFolder = dialog.FolderName;
                Services.ConfigService.Save();
            }
        }

        private void HideAndTrimMemory()
        {
            this.Hide();
            System.Threading.Tasks.Task.Delay(200).ContinueWith(_ => MemoryHelper.MinimizeMemory());
        }

        private void Window_Deactivated(object sender, EventArgs e)
        {
            HideAndTrimMemory();
        }

        private void Header_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ButtonState == MouseButtonState.Pressed)
            {
                this.DragMove();
            }
        }

        private void BtnMinimize_Click(object sender, RoutedEventArgs e)
        {
            HideAndTrimMemory();
        }

        private void BtnClose_Click(object sender, RoutedEventArgs e)
        {
            HideAndTrimMemory();
        }

        private void NavHome_Click(object sender, RoutedEventArgs e)
        {
            TabHome.Visibility = Visibility.Visible;
            TabHistory.Visibility = Visibility.Collapsed;
            TabSettings.Visibility = Visibility.Collapsed;
            TabApi.Visibility = Visibility.Collapsed;
            RefreshHistory();
        }

        private void NavHistory_Click(object sender, RoutedEventArgs e)
        {
            TabHome.Visibility = Visibility.Collapsed;
            TabHistory.Visibility = Visibility.Visible;
            TabSettings.Visibility = Visibility.Collapsed;
            TabApi.Visibility = Visibility.Collapsed;
            RefreshHistory();
        }

        private void NavApi_Click(object sender, RoutedEventArgs e)
        {
            TabHome.Visibility = Visibility.Collapsed;
            TabHistory.Visibility = Visibility.Collapsed;
            TabApi.Visibility = Visibility.Visible;
            TabSettings.Visibility = Visibility.Collapsed;
        }

        private void NavSettings_Click(object sender, RoutedEventArgs e)
        {
            TabHome.Visibility = Visibility.Collapsed;
            TabHistory.Visibility = Visibility.Collapsed;
            TabApi.Visibility = Visibility.Collapsed;
            TabSettings.Visibility = Visibility.Visible;
        }



        private void BtnRegion_Click(object sender, RoutedEventArgs e)
        {
            this.Hide();
            System.Threading.Thread.Sleep(200); // Give time for window to hide
            
            // Capture full screen first
            var fullScreenBitmap = Services.CaptureService.CaptureFullScreen();
            
            var regionWindow = new Windows.RegionSelectionWindow(fullScreenBitmap);
            regionWindow.RegionSelected += (croppedBitmap) =>
            {
                if (Application.Current is App app)
                {
                    app.ProcessCapture(croppedBitmap);
                }
                else
                {
                    Services.CaptureService.SaveToClipboard(croppedBitmap);
                }
                
                RefreshHistory();
                StatusText.Text = "Region captured";
                this.Show();
            };
            regionWindow.Show();
        }
        
        // --- Context Menu Handlers ---
        
        private void CtxClipboardCopy_Click(object sender, RoutedEventArgs e)
        {
            if (ClipboardList.SelectedItem is Services.HistoryItem item)
            {
                System.Windows.Clipboard.SetText(item.Data);
                StatusText.Text = "Text copied to clipboard";
            }
        }

        private void CtxClipboardDelete_Click(object sender, RoutedEventArgs e)
        {
            if (ClipboardList.SelectedItem is Services.HistoryItem item)
            {
                Services.HistoryService.Remove(item);
                RefreshHistory();
            }
        }

        private void BtnSaveSettings_Click(object sender, RoutedEventArgs e)
        {
            Services.ConfigService.Save();
            Services.HotkeyManager.Initialize();
            
            ShowStatus("Settings saved");
        }

        private async void ShowStatus(string message)
        {
            StatusText.Text = message;
            await System.Threading.Tasks.Task.Delay(3000);
            if (StatusText.Text == message)
            {
                StatusText.Text = "Ready";
            }
        }

        private void BtnBrowse_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new System.Windows.Forms.FolderBrowserDialog();
            if (dialog.ShowDialog() == System.Windows.Forms.DialogResult.OK)
            {
                TxtSaveFolder.Text = dialog.SelectedPath;
                Services.ConfigService.Current.SaveFolder = dialog.SelectedPath;
                Services.ConfigService.Save();
            }
        }

        private void ChkThemeToggle_Checked(object sender, RoutedEventArgs e)
        {
            if (_isInitializing) return;
            UpdateTheme(false); // Light Mode
        }

        private void ChkThemeToggle_Unchecked(object sender, RoutedEventArgs e)
        {
            if (_isInitializing) return;
            UpdateTheme(true); // Dark Mode
        }

        private void UpdateTheme(bool isDark)
        {
            if (Application.Current is App app)
            {
                app.ChangeTheme(isDark);
            }
            Services.ConfigService.Current.IsDarkTheme = isDark;
            Services.ConfigService.Save();
        }

        private void CtxClipboardClearAll_Click(object sender, RoutedEventArgs e)
        {
            Services.HistoryService.ClearClipboard();
            RefreshHistory();
        }

        private void CtxHistoryCopy_Click(object sender, RoutedEventArgs e)
        {
            if (HistoryList.SelectedItem is Services.HistoryItem item && System.IO.File.Exists(item.Data))
            {
                var bitmap = new System.Windows.Media.Imaging.BitmapImage(new Uri(item.Data));
                System.Windows.Clipboard.SetImage(bitmap);
                StatusText.Text = "Image copied to clipboard";
            }
        }

        private void CtxHistoryExplorer_Click(object sender, RoutedEventArgs e)
        {
            if (HistoryList.SelectedItem is Services.HistoryItem item && System.IO.File.Exists(item.Data))
            {
                System.Diagnostics.Process.Start("explorer.exe", $"/select,\"{item.Data}\"");
            }
        }

        private void CtxHistoryEditor_Click(object sender, RoutedEventArgs e)
        {
            if (HistoryList.SelectedItem is Services.HistoryItem item && System.IO.File.Exists(item.Data))
            {
                var bitmap = new System.Windows.Media.Imaging.BitmapImage(new Uri(item.Data));
                var editor = new Windows.EditorWindow(bitmap);
                editor.Show();
            }
        }

        private void CtxHistoryDelete_Click(object sender, RoutedEventArgs e)
        {
            if (HistoryList.SelectedItem is Services.HistoryItem item)
            {
                Services.HistoryService.Remove(item);
                if (System.IO.File.Exists(item.Data))
                {
                    try { System.IO.File.Delete(item.Data); } catch { }
                }
                RefreshHistory();
            }
        }

        private void HistoryList_MouseDoubleClick(object sender, System.Windows.Input.MouseButtonEventArgs e)
        {
            if (HistoryList.SelectedItem is Services.HistoryItem item && System.IO.File.Exists(item.Data))
            {
                var bitmap = new System.Windows.Media.Imaging.BitmapImage(new Uri(item.Data));
                var editor = new Windows.EditorWindow(bitmap);
                editor.Show();
            }
        }

        private void BtnFullScreen_Click(object sender, RoutedEventArgs e)
        {
            this.Hide();
            if (Application.Current is App app)
            {
                app.ExecuteFullScreenCapture();
            }
            else
            {
                var bitmap = Services.CaptureService.CaptureFullScreen();
                Services.CaptureService.SaveToClipboard(bitmap);
                RefreshHistory();
                StatusText.Text = "Fullscreen captured";
                this.Show();
            }
        }
    }
}