# Contributing to StayX Capture

First off, thank you for considering contributing to **StayX Capture**! It is passionate developers like you who make open-source productivity utilities better for the entire Windows community.

Please read through these guidelines before submitting bug reports, feature requests, or pull requests.

---

## 🗺️ How Can I Contribute?

### 🐛 Reporting Bugs
Before filing an issue, check the [open issues](https://github.com/karthik-cracking/StayX-Capture/issues) to ensure it hasn't already been reported.
When reporting a bug, use the **Bug Report** template and include:
- A clear, descriptive summary.
- Reproduction steps.
- Your Windows version, DPI scaling, and multi-monitor setup.
- Relevant terminal or console output.

### 💡 Requesting Features
Have an idea for a tool, export format, or integration? Open a [Feature Request](https://github.com/karthik-cracking/StayX-Capture/issues/new?template=feature_request.md) describing:
- The problem your idea solves.
- How the UI or workflow should look and feel.
- Any mockups or references.

### 🛠️ Submitting Pull Requests
1. **Fork** the repository and clone your fork locally.
2. Create a feature branch: `git checkout -b feature/your-feature-name`.
3. Build and test your changes locally using Visual Studio 2022 or the .NET 8 CLI.
4. Keep commits clean, semantic, and focused.
5. Push to your fork and submit a **Pull Request** against `main`.

---

## 💻 Local Development Setup

### Prerequisites
- **Windows 10 (Build 19041+) or Windows 11**
- **[.NET 8.0 SDK](https://dotnet.microsoft.com/download/dotnet/8.0)** or higher
- **IDE**: [Visual Studio 2022](https://visualstudio.microsoft.com/) (with *.NET desktop development* workload), [JetBrains Rider](https://www.jetbrains.com/rider/), or VS Code (with C# Dev Kit).

### Clone & Build

```bash
# 1. Clone the repository
git clone https://github.com/karthik-cracking/StayX-Capture.git
cd StayX-Capture

# 2. Restore NuGet dependencies
dotnet restore StayXCapture.sln

# 3. Build the solution
dotnet build StayXCapture.sln -c Debug

# 4. Run the WPF application
dotnet run --project StayXCapture.Wpf/StayXCapture.Wpf.csproj
```

---

## 🏗️ Architecture & Coding Standards

* **Event-Driven & Low Overhead**: Never introduce `Thread.Sleep`, polling timers, or background spin loops. Utilize native Windows message hooks (`RegisterHotKey`, `AddClipboardFormatListener`).
* **Safe Unmanaged Resource Management**: Every Win32 bitmap handle (`HBITMAP`) or GDI context must be wrapped in `using` statements and freed with `DeleteObject(hBitmap)` inside `finally` blocks to guarantee zero GDI memory leaks.
* **Aggressive Memory Hygiene**: Windows that hold full-resolution captures (`EditorWindow`, `RegionSelectionWindow`, `UploadPromptWindow`) must clear visual element sources and call `MemoryHelper.MinimizeMemory()` when closing or hiding to keep idle RAM usage < 10 MB.
* **Modern Windows Aesthetic**: Maintain consistent dark mode styling, DWM immersive titlebar styling, and smooth border geometries. Avoid generic Windows chrome defaults.

---

## ⚖️ License
By contributing to StayX Capture, you agree that your contributions will be licensed under the [MIT License](LICENSE).
