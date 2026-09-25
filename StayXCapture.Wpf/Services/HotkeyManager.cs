using System;
using System.Windows.Input;
using NHotkey;
using NHotkey.Wpf;

namespace StayXCapture.Wpf.Services
{
    public class HotkeyManager
    {
        public static event EventHandler? RegionCaptureRequested;
        public static event EventHandler? FullScreenCaptureRequested;

        public static void Initialize()
        {
            try
            {
                var config = ConfigService.Current;
                
                RegisterShortcut("RegionCapture", config.HotkeyRegion, OnRegionCapture);
                RegisterShortcut("FullScreenCapture", config.HotkeyFullscreen, OnFullScreenCapture);
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Failed to register hotkeys: {ex.Message}");
            }
        }

        public static void ReloadHotkeys()
        {
            Initialize();
        }
        
        private static void RegisterShortcut(string name, string hotkeyStr, EventHandler<HotkeyEventArgs> handler)
        {
            if (string.IsNullOrWhiteSpace(hotkeyStr)) return;
            
            if (TryParseHotkey(hotkeyStr, out var key, out var modifiers))
            {
                try
                {
                    NHotkey.Wpf.HotkeyManager.Current.AddOrReplace(name, key, modifiers, handler);
                    System.Diagnostics.Debug.WriteLine($"Registered hotkey '{name}': {modifiers}+{key}");
                }
                catch (Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine($"Failed to register hotkey '{name}' ({hotkeyStr}): {ex.Message}");
                }
            }
            else
            {
                System.Diagnostics.Debug.WriteLine($"Could not parse hotkey '{name}': {hotkeyStr}");
            }
        }

        public static bool TryParseHotkey(string hotkeyStr, out Key key, out ModifierKeys modifiers)
        {
            key = Key.None;
            modifiers = ModifierKeys.None;
            if (string.IsNullOrWhiteSpace(hotkeyStr)) return false;

            var parts = hotkeyStr.Split('+');
            for (int i = 0; i < parts.Length; i++)
            {
                var part = parts[i].Trim();
                if (string.IsNullOrEmpty(part)) continue;

                if (part.Equals("Ctrl", StringComparison.OrdinalIgnoreCase) || 
                    part.Equals("Control", StringComparison.OrdinalIgnoreCase))
                {
                    modifiers |= ModifierKeys.Control;
                }
                else if (part.Equals("Shift", StringComparison.OrdinalIgnoreCase))
                {
                    modifiers |= ModifierKeys.Shift;
                }
                else if (part.Equals("Alt", StringComparison.OrdinalIgnoreCase))
                {
                    modifiers |= ModifierKeys.Alt;
                }
                else if (part.Equals("Win", StringComparison.OrdinalIgnoreCase) || 
                         part.Equals("Windows", StringComparison.OrdinalIgnoreCase))
                {
                    modifiers |= ModifierKeys.Windows;
                }
                else
                {
                    var parsedKey = ParseKeyPart(part);
                    if (parsedKey != Key.None)
                    {
                        key = parsedKey;
                    }
                }
            }

            return key != Key.None;
        }

        public static Key ParseKeyPart(string part)
        {
            return part.Trim().ToUpperInvariant() switch
            {
                "]" or "OEM6" or "OEMCLOSEBRACKETS" or "CLOSEBRACKET" => Key.Oem6,
                "[" or "OEMOPENBRACKETS" or "OPENBRACKET" => Key.OemOpenBrackets,
                "/" or "?" or "OEMQUESTION" or "SLASH" => Key.OemQuestion,
                ";" or ":" or "OEM1" or "SEMICOLON" => Key.Oem1,
                "+" or "=" or "OEMPLUS" or "PLUS" => Key.OemPlus,
                "-" or "_" or "OEMMINUS" or "MINUS" => Key.OemMinus,
                "'" or "\"" or "OEMQUOTES" or "QUOTE" => Key.OemQuotes,
                "\\" or "|" or "OEM5" or "BACKSLASH" => Key.Oem5,
                "," or "<" or "OEMCOMMA" or "COMMA" => Key.OemComma,
                "." or ">" or "OEMPERIOD" or "PERIOD" or "DOT" => Key.OemPeriod,
                "`" or "~" or "OEMTILDE" or "TILDE" or "GRAVE" => Key.OemTilde,
                "0" => Key.D0,
                "1" => Key.D1,
                "2" => Key.D2,
                "3" => Key.D3,
                "4" => Key.D4,
                "5" => Key.D5,
                "6" => Key.D6,
                "7" => Key.D7,
                "8" => Key.D8,
                "9" => Key.D9,
                _ => Enum.TryParse<Key>(part.Trim(), true, out var k) ? k : Key.None
            };
        }

        private static void OnRegionCapture(object? sender, HotkeyEventArgs e)
        {
            e.Handled = true;
            RegionCaptureRequested?.Invoke(null, EventArgs.Empty);
        }

        private static void OnFullScreenCapture(object? sender, HotkeyEventArgs e)
        {
            e.Handled = true;
            FullScreenCaptureRequested?.Invoke(null, EventArgs.Empty);
        }
    }
}
