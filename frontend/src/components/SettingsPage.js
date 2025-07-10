import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Container,
  Typography,
  Box,
  Alert,
  Snackbar,
  Button,
  CircularProgress,
  Paper,
  Divider,
} from "@mui/material";
import {
  Settings as SettingsIcon,
  Refresh as RefreshIcon,
} from "@mui/icons-material";
import PathConfigCard from "./PathConfigCard";
import { getAllDataSources } from "../constants/dataSourceConfig";

const SettingsPage = ({ dataSource, onDataSourceChange }) => {
  const navigate = useNavigate();
  const [settings, setSettings] = useState({
    paths: {},
    default_paths: {},
    config_info: {},
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [validating, setValidating] = useState(false);
  const [validationResults, setValidationResults] = useState({});
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: "",
    severity: "info",
  });
  const [initialDataSource, setInitialDataSource] = useState(dataSource);

  // 获取所有数据源配置
  const dataSources = getAllDataSources();

  // 加载设置
  const loadSettings = async () => {
    try {
      setLoading(true);
      const response = await fetch("/api/settings");
      if (response.ok) {
        const data = await response.json();
        setSettings(data);
      } else {
        throw new Error("加载设置失败");
      }
    } catch (error) {
      console.error("加载设置失败:", error);
      showSnackbar("加载设置失败: " + error.message, "error");
    } finally {
      setLoading(false);
    }
  };

  // 保存设置
  const saveSettings = async () => {
    try {
      setSaving(true);
      const response = await fetch("/api/settings", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          paths: settings.paths,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        showSnackbar("设置保存成功", "success");
        // 重新加载设置以获取最新状态
        await loadSettings();
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || "保存设置失败");
      }
    } catch (error) {
      console.error("保存设置失败:", error);
      showSnackbar("保存设置失败: " + error.message, "error");
    } finally {
      setSaving(false);
    }
  };

  // 验证所有路径
  const validateAllPaths = async () => {
    try {
      setValidating(true);
      const response = await fetch("/api/settings/validate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          paths: settings.paths,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setValidationResults(data.results || {});
        showSnackbar("路径验证完成", "info");
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || "验证路径失败");
      }
    } catch (error) {
      console.error("验证路径失败:", error);
      showSnackbar("验证路径失败: " + error.message, "error");
    } finally {
      setValidating(false);
    }
  };

  // 重置所有设置
  const resetAllSettings = async () => {
    if (!window.confirm("确定要重置所有设置为默认值吗？此操作不可撤销。")) {
      return;
    }

    try {
      setSaving(true);
      const response = await fetch("/api/settings/reset", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        showSnackbar("设置已重置为默认值", "success");
        await loadSettings();
        setValidationResults({}); // 清空验证结果
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || "重置设置失败");
      }
    } catch (error) {
      console.error("重置设置失败:", error);
      showSnackbar("重置设置失败: " + error.message, "error");
    } finally {
      setSaving(false);
    }
  };

  // 更新单个路径
  const updatePath = (dataSource, path) => {
    setSettings((prev) => ({
      ...prev,
      paths: {
        ...prev.paths,
        [dataSource]: path,
      },
    }));
  };

  // 重置单个路径
  const resetPath = async (dataSource) => {
    try {
      const response = await fetch("/api/settings/reset", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          data_source: dataSource,
        }),
      });

      if (response.ok) {
        showSnackbar(`${dataSource} 路径已重置`, "success");
        await loadSettings();
        // 清除该数据源的验证结果
        setValidationResults((prev) => {
          const newResults = { ...prev };
          delete newResults[dataSource];
          return newResults;
        });
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || "重置路径失败");
      }
    } catch (error) {
      console.error("重置路径失败:", error);
      showSnackbar("重置路径失败: " + error.message, "error");
    }
  };

  // 验证单个路径
  const validatePath = async (dataSource, path) => {
    try {
      const response = await fetch("/api/settings/validate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          data_source: dataSource,
          path: path,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setValidationResults((prev) => ({
          ...prev,
          [dataSource]: data,
        }));
        return data;
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || "验证路径失败");
      }
    } catch (error) {
      console.error("验证路径失败:", error);
      showSnackbar("验证路径失败: " + error.message, "error");
      return null;
    }
  };

  // 显示提示消息
  const showSnackbar = (message, severity = "info") => {
    setSnackbar({
      open: true,
      message,
      severity,
    });
  };

  // 关闭提示消息
  const closeSnackbar = () => {
    setSnackbar((prev) => ({ ...prev, open: false }));
  };

  // 组件挂载时加载设置
  useEffect(() => {
    loadSettings();
  }, []);

  // 当数据源变化时，跳转到主页面显示对应数据源的对话
  useEffect(() => {
    if (dataSource && initialDataSource && dataSource !== initialDataSource) {
      // 数据源发生了变化，显示提示并跳转到主页面
      showSnackbar(
        `已切换到 ${
          getAllDataSources().find((ds) => ds.value === dataSource)
            ?.displayName || dataSource
        }`,
        "success"
      );

      // 延迟跳转，让用户看到切换反馈
      const timer = setTimeout(() => {
        navigate("/");
      }, 1000);

      return () => clearTimeout(timer);
    }
  }, [dataSource, initialDataSource, navigate]);

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box
          display="flex"
          justifyContent="center"
          alignItems="center"
          minHeight="400px"
        >
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* 页面标题 */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Box display="flex" alignItems="center" mb={2}>
          <SettingsIcon sx={{ mr: 2, fontSize: 32, color: "primary.main" }} />
          <Typography variant="h4" component="h1" fontWeight="bold">
            设置
          </Typography>
        </Box>

        <Typography variant="body1" color="text.secondary" mb={3}>
          配置各种AI编辑器的数据源路径。如果路径为空，将使用系统默认路径。
          在上方Header中切换数据源会自动跳转到主页面显示对应的对话内容。
        </Typography>

        {/* 操作按钮 */}
        <Box display="flex" gap={2} flexWrap="wrap">
          <Button
            variant="contained"
            onClick={saveSettings}
            disabled={saving}
            startIcon={saving ? <CircularProgress size={20} /> : null}
          >
            {saving ? "保存中..." : "保存设置"}
          </Button>

          <Button
            variant="outlined"
            onClick={validateAllPaths}
            disabled={validating}
            startIcon={
              validating ? <CircularProgress size={20} /> : <RefreshIcon />
            }
          >
            {validating ? "验证中..." : "验证所有路径"}
          </Button>

          <Button
            variant="outlined"
            color="warning"
            onClick={resetAllSettings}
            disabled={saving}
          >
            重置所有设置
          </Button>
        </Box>
      </Paper>

      {/* 配置信息 */}
      {settings.config_info && Object.keys(settings.config_info).length > 0 && (
        <Paper elevation={1} sx={{ p: 2, mb: 3, bgcolor: "grey.50" }}>
          <Typography variant="subtitle2" gutterBottom>
            配置文件信息
          </Typography>
          <Typography variant="body2" color="text.secondary">
            文件路径: {settings.config_info.config_file_path}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            最后更新:{" "}
            {settings.config_info.updated_at
              ? new Date(settings.config_info.updated_at).toLocaleString()
              : "未知"}
          </Typography>
        </Paper>
      )}

      {/* 路径配置卡片 */}
      <Box display="flex" flexDirection="column" gap={3}>
        {dataSources.map((dataSource) => (
          <PathConfigCard
            key={dataSource.value}
            dataSource={dataSource}
            currentPath={settings.paths[dataSource.value] || ""}
            defaultPath={settings.default_paths[dataSource.value] || ""}
            validationResult={validationResults[dataSource.value]}
            onPathChange={(path) => updatePath(dataSource.value, path)}
            onValidate={(path) => validatePath(dataSource.value, path)}
            onReset={() => resetPath(dataSource.value)}
          />
        ))}
      </Box>

      {/* 提示消息 */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={closeSnackbar}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert
          onClose={closeSnackbar}
          severity={snackbar.severity}
          sx={{ width: "100%" }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default SettingsPage;
