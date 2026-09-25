using System;
using System.IO;
using Newtonsoft.Json;

namespace StayXCapture.Wpf.Services
{
    public class Config
    {
        public string SaveFolder { get; set; } = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Pictures", "Screenshots");
        public bool AutoOrganize { get; set; } = true;
        public bool CopyClipboard { get; set; } = true;
        public bool OpenEditor { get; set; } = false;
        public bool PromptDisplaySelection { get; set; } = false;
        public bool StartMinimized { get; set; } = true;
        public bool AutoStart { get; set; } = false;
        public bool MonitorClipboard { get; set; } = true;
        public string Theme { get; set; } = "dark";
        public string HotkeyRegion { get; set; } = "Ctrl+Shift+D1";
        public string HotkeyFullscreen { get; set; } = "Ctrl+Shift+D2";
        public bool AutoUpload { get; set; } = false;
        public bool AskBeforeUpload { get; set; } = false;
        public string CustomApiEndpoint { get; set; } = "https://dmarket.space/api/upload";
        public string CustomApiKey { get; set; } = "";
        
        // Backwards compatibility for DMarketApiKey
        [JsonProperty(NullValueHandling = NullValueHandling.Ignore)]
        public string DMarketApiKey
        {
            get => CustomApiKey;
            set
            {
                if (string.IsNullOrWhiteSpace(CustomApiKey) && !string.IsNullOrWhiteSpace(value))
                {
                    CustomApiKey = value;
                }
            }
        }

        public string ImgbbApiKey { get; set; } = "";
        public string GoogleDriveApiKey { get; set; } = "";
        public bool IsDarkTheme { get; set; } = true;
    }

    public static class ConfigService
    {
        private static readonly string AppDataFolder = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "StayXCapture");
        private static readonly string ConfigPath = Path.Combine(AppDataFolder, "config.json");

        public static Config Current { get; private set; } = new Config();

        public static void Load()
        {
            try
            {
                if (!Directory.Exists(AppDataFolder))
                    Directory.CreateDirectory(AppDataFolder);

                if (File.Exists(ConfigPath))
                {
                    string json = File.ReadAllText(ConfigPath);
                    var cfg = JsonConvert.DeserializeObject<Config>(json);
                    if (cfg != null) Current = cfg;
                }
                else
                {
                    Save();
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Config Load Error: {ex.Message}");
            }
        }

        public static void Save()
        {
            try
            {
                if (!Directory.Exists(AppDataFolder))
                    Directory.CreateDirectory(AppDataFolder);

                string json = JsonConvert.SerializeObject(Current, Formatting.Indented);
                File.WriteAllText(ConfigPath, json);
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Config Save Error: {ex.Message}");
            }
        }
    }
}
