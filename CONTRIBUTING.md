# Contributing to StayX Capture

First off, thank you for considering contributing to StayX Capture! It is people like you who make open-source tools better for everyone.

Please read through these guidelines to understand how you can participate in the development of this project.

---

## 🗺️ How Can I Contribute?

### 🐛 Reporting Bugs
Before creating a bug report, please check the [Issues list](https://github.com/yourusername/StayXCapture/issues) to ensure the bug hasn't already been reported.

If you find a new bug, please open an issue and include:
* A clear, descriptive title.
* Step-by-step instructions to reproduce the issue.
* Expected vs. actual behavior.
* Details about your environment (Windows version, Python version, monitor setup/scaling).
* Any relevant error logs or screenshots.

### 💡 Suggesting Enhancements
We welcome feature suggestions! To request a new feature:
* Search the existing issues to see if the feature has already been proposed.
* Explain the problem your suggestion solves and how it benefits users.
* Describe the desired behavior in detail.

### 🛠️ Submitting Pull Requests
1. Fork the repository and create your branch from `main`.
2. Install development requirements (see **Development Setup** below).
3. If you've added code that should be tested, add tests or describe how you verified it.
4. Ensure your code compiles and conforms to formatting guidelines.
5. Open a Pull Request with a clear description of your changes and reference any related issues.

---

## 💻 Development Setup

To set up a local development environment:

1. **Fork and Clone the Repository:**
   ```bash
    git clone https://github.com/yourusername/StayXCapture.git
    cd "StayX Capture"
   ```

2. **Set Up a Virtual Environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application:**
   ```bash
   python Capture.py
   ```

---

## 🎨 Coding Standards

* **PEP 8**: Follow standard Python style guidelines (PEP 8) for code formatting.
* **Keep imports clean**: Import library modules in alphabetical groups (standard library, third-party, local).
* **Write clear comments**: Document complex logic, especially custom painting logic in `Capture.py`.
* **Testing**: Manually test screenshot capture and tray menu behavior after making modifications.
