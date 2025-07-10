import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";

import ChatList from "./components/ChatList";
import ChatDetail from "./components/ChatDetail";
import Header from "./components/Header";
import SettingsPage from "./components/SettingsPage";
import { getDataSourceConfig } from "./constants/dataSourceConfig";

// Define our color palette centrally - using rich, modern colors
const colors = {
  primary: {
    main: "#00bbff", // Rich purple
    light: "#66d6ff", // Light purple
    dark: "#005e80", // Dark purple
  },
  secondary: {
    main: "#FF6B35", // Vibrant orange
    light: "#FF8F5E", // Light orange
    dark: "#E04F1D", // Dark orange
  },
  tertiary: {
    main: "#3EBD64", // Vibrant green
    light: "#5FD583", // Light green
    dark: "#2A9E4A", // Dark green
  },
  highlightColor: "#0cbcff8f", // New bright blue with transparency
  background: {
    default: "#121212", // Dark background
    paper: "#1E1E1E", // Slightly lighter dark for cards/elements
    gradient: "linear-gradient(135deg, #6E2CF4 0%, #FF6B35 50%, #3EBD64 100%)", // Gradient from purple to orange to green
  },
  text: {
    primary: "#FFFFFF", // White text
    secondary: "#B3B3B3", // Lighter gray for secondary text
  },
  info: {
    main: "#39C0F7", // Bright blue
  },
  success: {
    main: "#3EBD64", // Green
  },
  warning: {
    main: "#FAAD14", // Amber
  },
  error: {
    main: "#F5222D", // Red
  },
};

// Create a modern, sophisticated dark theme for the app
const modernTheme = createTheme({
  palette: {
    mode: "dark",
    primary: colors.primary,
    secondary: colors.secondary,
    background: colors.background,
    text: colors.text,
    info: colors.info,
    success: colors.success,
    warning: colors.warning,
    error: colors.error,
    highlight: {
      main: colors.highlightColor,
    },
  },
  typography: {
    fontFamily: "'Inter', 'Roboto', 'Helvetica', 'Arial', sans-serif",
    h4: {
      fontWeight: 700,
    },
    h5: {
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 10,
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          boxShadow: `0 4px 10px ${colors.highlightColor}`,
          backgroundColor: colors.background.paper,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          backgroundColor: colors.background.paper,
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          background: colors.background.gradient,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          "& .MuiOutlinedInput-root": {
            backgroundColor: "transparent",
            "&:hover": {
              backgroundColor: "transparent",
            },
            "&.Mui-focused": {
              backgroundColor: "transparent",
            },
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: "none",
          borderRadius: 6,
          fontWeight: 500,
          color: "white",
        },
        contained: {
          boxShadow: `0 2px 4px ${colors.highlightColor}`,
        },
        outlined: {
          color: "white",
          borderColor: colors.highlightColor,
          "&:hover": {
            borderColor: colors.highlightColor,
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 4,
        },
      },
    },
    MuiCircularProgress: {
      styleOverrides: {
        root: {
          color: colors.highlightColor,
        },
      },
    },
  },
});

// Export the colors so they can be used in other components
export { colors };

function App() {
  // 数据源状态管理
  const [dataSource, setDataSource] = useState("cursor");
  const [isLoading, setIsLoading] = useState(false);
  const [clearDataTrigger, setClearDataTrigger] = useState(0);

  // 处理数据源切换
  const handleDataSourceChange = (newSource) => {
    if (newSource !== dataSource) {
      // 立即设置loading状态和触发数据清空
      setIsLoading(true);
      setClearDataTrigger((prev) => prev + 1);
      setDataSource(newSource);
      // 延迟重置加载状态，给API请求时间完成
      setTimeout(() => setIsLoading(false), 1000);
    }
  };

  // 获取当前数据源的配置信息
  const currentConfig = getDataSourceConfig(dataSource);

  return (
    <ThemeProvider theme={modernTheme}>
      <CssBaseline />
      <Router>
        <Header
          dataSource={dataSource}
          onDataSourceChange={handleDataSourceChange}
          isLoading={isLoading}
        />
        <Routes>
          <Route
            path="/"
            element={
              <ChatList
                dataSource={dataSource}
                historyTitle={currentConfig.historyTitle}
                clearDataTrigger={clearDataTrigger}
              />
            }
          />
          <Route
            path="/chat/:sessionId"
            element={<ChatDetail dataSource={dataSource} />}
          />
          <Route
            path="/settings"
            element={
              <SettingsPage
                dataSource={dataSource}
                onDataSourceChange={handleDataSourceChange}
              />
            }
          />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
