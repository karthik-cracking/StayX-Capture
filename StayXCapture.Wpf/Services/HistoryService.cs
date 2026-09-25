using System;
using System.Collections.Generic;
using System.IO;
using Newtonsoft.Json;

namespace StayXCapture.Wpf.Services
{
    public class HistoryItem
    {
        public string Type { get; set; } = "image"; // image or text
        public string Data { get; set; } = ""; // Path or text content
        public string Timestamp { get; set; } = "";
        
        // For UI display
        public string Name { get; set; } = "";
        public string SizeText { get; set; } = "";
        
        public override string ToString()
        {
            return Data ?? "";
        }
    }

    public static class HistoryService
    {
        private static readonly string AppDataFolder = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "StayXCapture");
        private static readonly string HistoryPath = Path.Combine(AppDataFolder, "history.json");

        public static List<HistoryItem> CurrentHistory { get; private set; } = new List<HistoryItem>();

        public static void Load()
        {
            try
            {
                if (File.Exists(HistoryPath))
                {
                    string json = File.ReadAllText(HistoryPath);
                    var hist = JsonConvert.DeserializeObject<List<HistoryItem>>(json);
                    if (hist != null) CurrentHistory = hist;
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"History Load Error: {ex.Message}");
            }
        }

        public static void Save()
        {
            try
            {
                if (!Directory.Exists(AppDataFolder))
                    Directory.CreateDirectory(AppDataFolder);

                string json = JsonConvert.SerializeObject(CurrentHistory, Formatting.Indented);
                File.WriteAllText(HistoryPath, json);
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"History Save Error: {ex.Message}");
            }
        }

        public static void Add(HistoryItem item)
        {
            CurrentHistory.Insert(0, item);
            
            // Keep history limited to 100 items
            if (CurrentHistory.Count > 100)
            {
                CurrentHistory.RemoveAt(CurrentHistory.Count - 1);
            }
            
            Save();
        }
        
        public static void Remove(HistoryItem item)
        {
            if (CurrentHistory.Contains(item))
            {
                CurrentHistory.Remove(item);
                Save();
            }
        }
        
        public static void ClearClipboard()
        {
            CurrentHistory.RemoveAll(h => h.Type == "text");
            Save();
        }
    }
}
