# AI IDE Chat Export Tool

A powerful AI IDE chat history viewing and export tool that supports unified management and export of multiple data sources.

## 🎯 Project Overview

This project is a web application specifically designed for viewing, managing, and exporting AI IDE chat records. It can extract conversation data from multiple different AI assistant data sources and provide a unified interface for viewing, searching, and exporting.

### Key Features

- **Multi-Data Source Support**: Unified management of conversation records from 5 different AI assistants
- **Modern Interface**: Dark theme design based on Material-UI, providing excellent user experience
- **Powerful Export Functions**: Supports export in HTML, JSON, and Markdown formats
- **Intelligent Data Extraction**: Automatically parses and converts chat data in different formats
- **Project Recognition**: Intelligently identifies and displays project information associated with conversations
- **Settings Management**: Visual settings page with custom data source path configuration
- **Path Validation**: Smart validation of configured paths with real-time feedback

## 🔧 Technology Stack

### Frontend Technologies

- **React 18** - Modern user interface framework
- **Material-UI (MUI)** - Professional React UI component library
- **React Router** - Single-page application routing management
- **Axios** - HTTP client library
- **React Markdown** - Markdown content rendering

### Backend Technologies

- **Flask** - Lightweight Python web framework
- **SQLite** - Database operations and queries
- **Flask-CORS** - Cross-Origin Resource Sharing support

## 📊 Supported Data Sources

### 1. Cursor Native Conversations

- **Source**: Cursor IDE's native AI chat functionality
- **Data Location**: Cursor's workspaceStorage and global storage
- **Features**: Supports complete conversation history and project context

### 2. VSCode Augment Conversations

- **Source**: Augment AI assistant plugin in VSCode
- **Data Location**: VSCode's workspaceStorage SQLite database
- **Features**: Professional code assistance conversation records

### 3. Cursor Augment Conversations

- **Source**: Augment AI assistant plugin in Cursor IDE
- **Data Location**: Cursor's workspaceStorage (compatible with VSCode format)
- **Features**: Augment conversations combined with Cursor environment

### 4. IDEA Augment Conversations

- **Source**: Augment AI assistant plugin in JetBrains IntelliJ IDEA
- **Data Location**: XML format data in IDEA's configuration directory
- **Features**: Professional code conversations for Java development environment

### 5. PyCharm Augment Conversations

- **Source**: Augment AI assistant plugin in JetBrains PyCharm
- **Data Location**: XML format data in PyCharm's configuration directory
- **Features**: Specialized code assistance conversations for Python development

## 🚀 Installation and Setup

### Requirements

- **Node.js** 16.0+
- **Python** 3.7+
- **npm** or **yarn**

### Installation Steps

1. **Clone the Project**

```bash
git clone <repository-url>
cd cursor-view
```

2. **Install Frontend Dependencies**

```bash
cd frontend
npm install
```

3. **Build Frontend Production Version**

```bash
npm run build
```

4. **Install Backend Dependencies**

```bash
cd ../backend
pip install -r ../requirements.txt
```

### Starting the Application

1. **Start Backend Server**

```bash
cd backend
python server.py
```

2. **Access the Application**
   Open your browser and visit: `http://localhost:5000`

> **Note**: Please ensure you follow the above sequence - build the frontend first, then start the backend server. The application runs on port 5000, not port 3000.

## 💡 Usage Instructions

### Data Source Switching

1. Select the data source you want to view from the data source selector at the top of the page
2. The system will automatically load chat records from the corresponding data source
3. Supports seamless switching between 5 data sources (Cursor, VSCode Augment, Cursor Augment, IDEA Augment, PyCharm Augment)

### Viewing Conversations

1. Browse all conversations in the chat list
2. Click on any conversation to enter the detailed view page
3. Supports filtering by project, time, and other information

### Export Functions

1. Click the export button on the conversation details page
2. Select export format: HTML, JSON, or Markdown
3. The system will generate a file containing the complete conversation content for download

### Settings Configuration

1. Click the settings icon in the top right corner to enter the settings page
2. Configure custom paths for each data source (optional)
3. The system will automatically validate path validity and provide feedback
4. Supports resetting to default paths or saving custom configurations

## 🎨 Feature Highlights

### Intelligent Project Recognition

- Automatically extracts project names from file paths
- Supports Git repository information recognition
- Intelligently filters user directories and system directories

### Modern UI Design

- Dark theme design for comfortable viewing
- Responsive layout supporting various screen sizes
- Smooth animations and interactive effects

### Powerful Data Processing

- Supports complex SQLite database parsing
- Intelligent JSON and XML data conversion
- Comprehensive error handling and exception recovery
- Unified processing for multiple data source formats

### Advanced Configuration Management

- Visual settings interface with custom path configuration support
- Real-time path validation and status feedback
- Configuration persistence and one-click reset functionality
- Smart default path detection and fallback mechanisms

## 🔄 Project Improvements

### Enhanced Features Compared to Original Project

This project is based on [cursor-view](https://github.com/saharmor/cursor-view) with secondary development. Main enhancements include:

1. **Multi-Data Source Support**: Extended from single Cursor data source to five data sources
2. **Unified Export Functions**: Supports standardized export in multiple formats
3. **Modern Interface**: Brand new Material-UI design and dark theme
4. **Intelligent Data Extraction**: More powerful data parsing and conversion capabilities
5. **Optimized Project Recognition**: More accurate project name recognition algorithms
6. **Enhanced Error Handling**: More comprehensive exception handling and user feedback
7. **Settings Management System**: Visual configuration interface and path management
8. **JetBrains IDE Support**: Added IDEA and PyCharm Augment data source support

### Acknowledgments

Thanks to the [saharmor/cursor-view](https://github.com/saharmor/cursor-view) project for providing the foundational architecture and inspiration. This project has undergone extensive functional expansion and user experience optimization based on it.

## 📁 Project Structure

```
cursor-view/
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── components/      # React components
│   │   │   ├── ChatDetail.js      # Chat detail page
│   │   │   ├── ChatList.js        # Chat list page
│   │   │   ├── Header.js          # Page header component
│   │   │   ├── PathConfigCard.js  # Path configuration card
│   │   │   └── SettingsPage.js    # Settings page
│   │   ├── constants/       # Configuration constants
│   │   │   └── dataSourceConfig.js # Data source configuration
│   │   └── ...
│   ├── build/               # Build output directory
│   └── package.json
├── backend/                 # Python backend service
│   ├── server.py           # Flask main server
│   ├── config_manager.py   # Configuration manager
│   ├── path_validator.py   # Path validator
│   ├── augment_extractor.py # Augment data extractor
│   ├── cursor_augment_extractor.py # Cursor Augment extractor
│   ├── idea_augment_extractor.py   # IDEA Augment extractor
│   ├── pycharm_augment_extractor.py # PyCharm Augment extractor
│   ├── conversation_parser.py      # Conversation parser
│   ├── output_formatter.py        # Output formatter
│   └── ...
├── config.json             # Application configuration file
├── requirements.txt        # Python dependencies
├── README.md              # Chinese documentation
└── README_EN.md           # English documentation
```

## 🤝 Contributing

Welcome to submit Issues and Pull Requests to improve the project!

### Code Standards

- Frontend: Follow React and JavaScript best practices
- Backend: Follow PEP 8 Python code standards
- Commit messages: Use clear commit messages to describe changes
- **Branch Management**: Please submit all code contributions to the `dev` branch, not the `main` branch

## 📄 License

This project is licensed under the [Apache License 2.0](LICENSE).

## ⚙️ Environment Configuration

### Optional Environment Variables

```bash
# Enable Cursor chat diagnostics mode (for debugging)
export CURSOR_CHAT_DIAGNOSTICS=1

# Custom server port (default 5000)
export PORT=5000
```

### Data Storage Locations

Data storage locations for different operating systems:

**Windows**:

- Cursor: `%APPDATA%\Cursor\User\workspaceStorage`
- VSCode: `%APPDATA%\Code\User\workspaceStorage`
- IDEA: `%APPDATA%\JetBrains\IntelliJIdea[version]\options`
- PyCharm: `%APPDATA%\JetBrains\PyCharm[version]\options`

**macOS**:

- Cursor: `~/Library/Application Support/Cursor/User/workspaceStorage`
- VSCode: `~/Library/Application Support/Code/User/workspaceStorage`
- IDEA: `~/Library/Application Support/JetBrains/IntelliJIdea[version]/options`
- PyCharm: `~/Library/Application Support/JetBrains/PyCharm[version]/options`

**Linux**:

- Cursor: `~/.config/Cursor/User/workspaceStorage`
- VSCode: `~/.config/Code/User/workspaceStorage`
- IDEA: `~/.config/JetBrains/IntelliJIdea[version]/options`
- PyCharm: `~/.config/JetBrains/PyCharm[version]/options`

## 🔧 Troubleshooting

### Common Issues

**Q: Cannot access localhost:5000 after startup**
A: Please ensure:

1. Backend server has started correctly without error messages
2. Port 5000 is not occupied by other programs
3. Firewall is not blocking the port

**Q: Cannot find chat data**
A: Please check:

1. Whether the corresponding IDE is installed and has used AI features
2. Whether the data source selection is correct
3. Whether related plugins are installed (such as Augment plugin)
4. Check data source path configuration in the settings page
5. Ensure path validation status shows as valid

**Q: Export function not working**
A: Please confirm:

1. Browser allows file downloads
2. Sufficient disk space available
3. Conversation data is not empty

**Q: Frontend build fails**
A: Try:

1. Delete `node_modules` folder and run `npm install` again
2. Check if Node.js version meets requirements
3. Clear npm cache: `npm cache clean --force`

### Development Mode

For development, you can start frontend and backend separately:

```bash
# Start frontend development server (port 3000)
cd frontend
npm start

# Start backend server (port 5000)
cd backend
python server.py
```

---

**Thank you for using AI IDE Chat Export Tool!** 🚀

